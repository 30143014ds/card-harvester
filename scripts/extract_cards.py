"""Native card crop tracking, ranking and export; no video-specific geometry."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def order_quad(points):
    p = np.asarray(points, dtype=np.float32).reshape(4, 2)
    # TL, TR, BR, BL; suitable for the near-horizontal album cards.
    idx = np.argsort(p[:, 1])
    top = p[idx[:2]][np.argsort(p[idx[:2], 0])]
    bottom = p[idx[2:]][np.argsort(p[idx[2:], 0])]
    return np.array([top[0], top[1], bottom[1], bottom[0]], np.float32)


def crop_quad(frame, quad):
    q = np.asarray(quad, np.float32)
    w = round(max(np.linalg.norm(q[1]-q[0]), np.linalg.norm(q[2]-q[3])))
    h = round(max(np.linalg.norm(q[3]-q[0]), np.linalg.norm(q[2]-q[1])))
    dst = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], np.float32)
    matrix = cv2.getPerspectiveTransform(q, dst)
    return cv2.warpPerspective(frame, matrix, (w, h), flags=cv2.INTER_CUBIC)


def contact_sheet(items, destination, columns=4, cell_size=(360,260)):
    cw,ch=cell_size
    canvas=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)), '#eeeeee')
    draw=ImageDraw.Draw(canvas)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    except OSError:
        font=ImageFont.load_default()
    for i,(path,label) in enumerate(items):
        im=Image.open(path).convert('RGB')
        im.thumbnail((cw-16,ch-44),Image.Resampling.LANCZOS)
        x,y=(i%columns)*cw,(i//columns)*ch
        canvas.paste(im,(x+(cw-im.width)//2,y+30+(ch-44-im.height)//2))
        draw.text((x+8,y+7),label,fill='black',font=font)
    canvas.save(destination,quality=95)


def image_quality(crop):
    """Rank the same card across frames, excluding sleeve/border edges."""
    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
    size=(640,400) if crop.shape[1]>480 else (320,200)
    gray=cv2.resize(gray,size,interpolation=cv2.INTER_AREA)
    gray=gray[12:-12,12:-12]
    lap=cv2.Laplacian(gray,cv2.CV_32F)
    tile_energies=[]
    for tile_row in np.array_split(lap,4,axis=0):
        for tile in np.array_split(tile_row,6,axis=1):
            tile_energies.append(float(np.sqrt(np.mean(tile**2))))
    focus=float(np.sqrt(np.mean(lap**2)))
    coverage=float(np.mean(sorted(tile_energies)[:18]))
    hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
    ycc=cv2.cvtColor(crop,cv2.COLOR_BGR2YCrCb)
    skin=((ycc[:,:,1]>135)&(ycc[:,:,1]<180)&(ycc[:,:,2]>85)&(ycc[:,:,2]<135)
          &(hsv[:,:,1]>45)&(hsv[:,:,0]<25)&(hsv[:,:,2]>70))
    # Leave card-edge fingers out of the score where possible.
    skin_fraction=float(skin.mean())
    scale=math.sqrt(crop.shape[0]*crop.shape[1]/50000)
    score=(focus+0.35*coverage)*min(1.4,max(0.6,scale))*(1-min(0.85,skin_fraction*5))
    return {'score':float(score),'focus':focus,'coverage':coverage,
            'skin_fraction':skin_fraction,'native_width':crop.shape[1],
            'native_height':crop.shape[0]}


def reference_image(out, n):
    path=out/'debug'/f'frame_{n:06}.jpg'
    if not path.exists():path=out/'debug'/'samples'/f'{n:06}.jpg'
    return cv2.imread(str(path))


def rank_candidates(out, scenes, fps, total, only_scene=None):
    cv2.setNumThreads(2)
    sift=cv2.SIFT_create(nfeatures=3500,contrastThreshold=0.012,edgeThreshold=15)
    results={card['id']:[] for scene in scenes for card in scene['cards']}
    native_path=out/'native_index.json'
    native=json.loads(native_path.read_text()) if native_path.exists() else None
    for scene in scenes:
        if only_scene is not None and scene['id']!=only_scene:
            continue
        checkpoint=out/'debug'/f'ranked_scene_{scene["id"]:02}.json'
        if checkpoint.exists():
            results.update(json.loads(checkpoint.read_text()))
            print(f'Scene {scene["id"]:02}: loaded completed checkpoint',flush=True)
            continue
        reference=reference_image(out,scene['reference_frame'])
        gray_ref=cv2.cvtColor(reference,cv2.COLOR_BGR2GRAY)
        ref_cards=[]
        for card in scene['cards']:
            quad=np.array(card['quad'],np.float32)
            mask=np.zeros_like(gray_ref)
            cv2.fillConvexPoly(mask,quad.astype(np.int32),255)
            mask=cv2.erode(mask,np.ones((7,7),np.uint8))
            kp,desc=sift.detectAndCompute(gray_ref,mask)
            ref_cards.append((card,quad,kp,desc))
        if native:
            indices=[n for n in native['sample_indices']
                     if scene['start_sec']<=native['samples'][str(n)]['time_sec']<=scene['end_sec']]
        else:
            indices=list(range(math.ceil(scene['start_sec']*fps/3)*3,
                               min(total,math.floor(scene['end_sec']*fps)+1),3))
        for n in indices:
            frame=cv2.imread(str(out/'debug'/'samples'/f'{n:06}.jpg'))
            if frame is None:continue
            full_crop_frame=cv2.imread(str(out/native['samples'][str(n)]['native_file'])) if native else None
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            mask=np.zeros_like(gray);mask[native.get('preview_roi_top',300) if native else 300:]=255
            kp,desc=sift.detectAndCompute(gray,mask)
            if desc is None or len(desc)<10:continue
            matcher=cv2.FlannBasedMatcher(dict(algorithm=1,trees=4),dict(checks=64))
            matcher.add([desc]);matcher.train()
            for card,quad,ref_kp,ref_desc in ref_cards:
                if ref_desc is None or len(ref_desc)<8:continue
                matches=matcher.knnMatch(ref_desc,k=2)
                good=[a for pair in matches if len(pair)==2 for a,b in [pair]
                      if a.distance<0.72*b.distance]
                center=quad.mean(axis=0)
                # Reject accidental matches to a neighboring card of the
                # same corporate design, even when its logo is identical.
                good=[m for m in good if
                      abs(kp[m.trainIdx].pt[0]-ref_kp[m.queryIdx].pt[0])<160 and
                      abs(kp[m.trainIdx].pt[1]-ref_kp[m.queryIdx].pt[1])<125]
                if len(good)<8:continue
                src=np.float32([ref_kp[m.queryIdx].pt for m in good]).reshape(-1,1,2)
                dst=np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1,1,2)
                H,inliers=cv2.findHomography(src,dst,cv2.RANSAC,2.5)
                if H is None or inliers is None or inliers.sum()<8 or inliers.mean()<0.5:
                    continue
                q=cv2.perspectiveTransform(quad.reshape(1,4,2),H)[0]
                if not np.isfinite(q).all() or not cv2.isContourConvex(q):continue
                # A crop must be entirely inside the source video.
                if q[:,0].min()<0 or q[:,0].max()>frame.shape[1]-1 or q[:,1].min()<0 or q[:,1].max()>frame.shape[0]-1:
                    continue
                area=cv2.contourArea(q);ref_area=cv2.contourArea(quad)
                if not 0.45<area/ref_area<2.1:continue
                if abs(q.mean(axis=0)[0]-center[0])>130 or abs(q.mean(axis=0)[1]-center[1])>105:
                    continue
                top=q[1]-q[0]
                if abs(math.degrees(math.atan2(top[1],top[0])))>30:continue
                # Verify correspondences span the card, rather than only
                # a small shared logo; this constrains the extrapolation.
                valid_src=src[inliers.ravel().astype(bool),0,:]
                hull_area=cv2.contourArea(cv2.convexHull(valid_src))
                if hull_area/ref_area<0.06:continue
                native_q=q*native['scale']-np.array([0,native['native_roi_top']],np.float32) if native else q
                crop=crop_quad(full_crop_frame,native_q) if native else crop_quad(frame,q)
                quality=image_quality(crop)
                timestamp=native['samples'][str(n)]['time_sec'] if native else n/fps
                results[card['id']].append({'frame':n,'time_sec':round(timestamp,3),
                                           'quad':q.tolist(),'inliers':int(inliers.sum()),
                                           'match_coverage':float(hull_area/ref_area),
                                           **quality})
        native_reference=cv2.imread(str(out/native['samples'][str(scene['reference_frame'])]['native_file'])) if native else None
        for card,quad,_,_ in ref_cards:
            candidates=results[card['id']]
            # A manually checked reference is retained for review even if
            # matching fails (for example, a largely blank card with glare).
            if quad[:,0].min()>=0 and quad[:,0].max()<reference.shape[1]:
                native_quad=quad*native['scale']-np.array([0,native['native_roi_top']],np.float32) if native else quad
                timestamp=native['samples'][str(scene['reference_frame'])]['time_sec'] if native else scene['reference_frame']/fps
                candidates.append({'frame':scene['reference_frame'],
                                   'time_sec':round(timestamp,3),
                                   'quad':quad.tolist(),'inliers':0,'match_coverage':0,
                                   **image_quality(crop_quad(native_reference,native_quad) if native else crop_quad(reference,quad))})
            candidates.sort(key=lambda c:c['score'],reverse=True)
            # Keep different times as alternatives; adjacent frames usually
            # have almost exactly the same reflection/occlusion.
            distinct=[]
            for candidate in candidates:
                if all(abs(candidate['frame']-other['frame'])>=9 for other in distinct):
                    distinct.append(candidate)
                if len(distinct)==4:break
            results[card['id']]=distinct
            if not distinct:raise RuntimeError(f'No valid crop for {card["id"]}')
        counts=[len(results[c['id']]) for c in scene['cards']]
        checkpoint.write_text(json.dumps({c['id']:results[c['id']] for c in scene['cards']},indent=2))
        print(f'Scene {scene["id"]:02}: {len(indices)} sampled frames, {len(counts)} cards, alternatives {counts}',flush=True)
    if only_scene is None:
        (out/'ranked_candidates.json').write_text(json.dumps(results,indent=2))
    return results


def rotate_crop(crop, rotation):
    if rotation=='cw':return cv2.rotate(crop,cv2.ROTATE_90_CLOCKWISE)
    if rotation=='ccw':return cv2.rotate(crop,cv2.ROTATE_90_COUNTERCLOCKWISE)
    if rotation=='180':return cv2.rotate(crop,cv2.ROTATE_180)
    return crop


def apply_review_choices(out,ranked):
    path=out/'review_choices.json'
    if not path.exists():return ranked
    choices=json.loads(path.read_text())
    for card_id,choice in choices.items():
        if not ranked.get(card_id):continue
        if 'selected_frame' not in choice:continue
        candidates=ranked[card_id]
        index=next((i for i,c in enumerate(candidates) if c['frame']==choice['selected_frame']),None)
        if index is None:raise RuntimeError(f'Reviewed frame missing for {card_id}')
        candidates[0],candidates[index]=candidates[index],candidates[0]
        if 'quad' in choice:
            candidates[0]['quad']=choice['quad']
    return ranked


def export_cards(video,out,scenes,fps,ranked,append=False):
    review_path=out/'review_choices.json'
    reviews=json.loads(review_path.read_text()) if review_path.exists() else {}
    cards_dir=out/'cards';cards_dir.mkdir(exist_ok=True)
    alternatives_dir=out/'alternatives';alternatives_dir.mkdir(exist_ok=True)
    all_cards=[(scene,card) for scene in scenes for card in scene['cards']]
    wanted={}
    for scene,card in all_cards:
        for rank,candidate in enumerate(ranked[card['id']]):
            wanted.setdefault(candidate['frame'],[]).append((scene,card,rank,candidate))
    native_path=out/'native_index.json'
    native=json.loads(native_path.read_text()) if native_path.exists() else None
    written=set()
    def write_frame(n,frame):
            for scene,card,rank,candidate in wanted[n]:
                quad=np.array(candidate['quad'],np.float32)
                if native:
                    candidate['source_quad']=(quad*native['scale']).tolist()
                    quad=quad*native['scale']-np.array([0,native['native_roi_top']],np.float32)
                crop=rotate_crop(crop_quad(frame,quad),card['rotation'])
                if rank==0:
                    filename=f'{card["id"]}.png';path=cards_dir/filename
                else:
                    filename=f'{card["id"]}_alt{rank}.png';path=alternatives_dir/filename
                cv2.imwrite(str(path),crop,[cv2.IMWRITE_PNG_COMPRESSION,6])
                candidate['file']=str(path.relative_to(out))
                candidate['output_width']=crop.shape[1];candidate['output_height']=crop.shape[0]
                written.add((card['id'],rank))
    if native:
        for n in sorted(wanted):
            frame=cv2.imread(str(out/native['samples'][str(n)]['native_file']))
            if frame is None:raise RuntimeError(f'Missing native frame {n}')
            write_frame(n,frame)
    else:
        cap=cv2.VideoCapture(str(video));n=0
        while cap.grab():
            if n in wanted:
                ok,frame=cap.retrieve()
                if not ok:raise RuntimeError(f'Cannot decode selected frame {n}')
                write_frame(n,frame)
            n+=1
        cap.release()
    expected=sum(len(ranked[card['id']]) for _,card in all_cards)
    if len(written)!=expected:raise RuntimeError(f'Only exported {len(written)} of {expected} crops')
    manifest=[]
    for scene,card in all_cards:
        manifest.append({'id':card['id'],'scene':scene['id'], 'side':card['side'],'row':card['row'],
                         'rotation':card['rotation'],'selected':ranked[card['id']][0],
                         'alternatives':ranked[card['id']][1:],
                         'review_notes':[reviews[card['id']]['reason']] if card['id'] in reviews else []})
    if append and (out/'manifest.json').exists():
        previous=json.loads((out/'manifest.json').read_text())['cards']
        new_ids={c['id'] for c in manifest}
        manifest=sorted([c for c in previous if c['id'] not in new_ids]+manifest,key=lambda c:c['id'])
    previous_meta=json.loads((out/'manifest.json').read_text()) if append and (out/'manifest.json').exists() else {}
    digest=previous_meta.get('source_sha256')
    if not digest:
        with video.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
    metadata={'source_video':video.name,'source_path':str(video.resolve()),'source_sha256':digest,
              'fps':fps,'sample_interval_sec':3/fps,'count':len(manifest),'cards':manifest}
    if native:
        metadata['sampling_strategy']=native.get('sampling_strategy','native keyframes')
        metadata['sample_interval_sec']=None
        metadata['source_resolution']=native.get('source_resolution',[2160,3840])
        metadata['geometry_preview_resolution']=native.get('preview_resolution',[720,1280])
        metadata['photo_pixels']=native.get('photo_pixels','Native 4K source pixels, HLG converted to BT.709 using Hable tone mapping')
    (out/'manifest.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False))
    (out/'ranked_candidates.json').write_text(json.dumps(ranked,indent=2))
    make_review_pages(out,manifest)
    print(f'Exported {len(manifest)} selected cards and {expected-len(all_cards)} alternatives in this batch',flush=True)


def make_review_pages(out,cards):
    overview=[]
    for start in range(0,len(cards),24):
        part=cards[start:start+24]
        path=out/f'overview_{start//24+1:02}.jpg'
        items=[(out/c['selected']['file'],f'{c["id"]} | {c["selected"]["time_sec"]:.2f}s') for c in part]
        contact_sheet(items,path,columns=4,cell_size=(420,300))
        overview.append(path.name)
    for scene in sorted({c['scene'] for c in cards}):
        part=[c for c in cards if c['scene']==scene]
        items=[]
        for card in part:
            for rank,candidate in enumerate([card['selected']]+card['alternatives']):
                items.append((out/candidate['file'],f'{card["id"]} #{rank} | {candidate["time_sec"]:.2f}s'))
        contact_sheet(items,out/'debug'/f'quality_{scene:02}.jpg',columns=4,cell_size=(380,265))
