"""Prepare and extract an arbitrary new video using reviewed per-video borders."""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

from extract_cards import (apply_review_choices, contact_sheet, export_cards,
                           order_quad, rank_candidates)
from .contacts import atomic_json

TONE = ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,'
        'tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=full,format=rgb24')


def probe(video: Path):
    if not video.is_file():
        raise FileNotFoundError(video)
    raw = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_streams',
        '-show_format', '-of', 'json', str(video)], text=True))
    stream = raw['streams'][0]
    numerator, denominator = map(int, stream['avg_frame_rate'].split('/'))
    if numerator <= 0 or denominator <= 0:
        numerator, denominator = map(int, stream['r_frame_rate'].split('/'))
    fps = numerator / denominator
    duration = float(stream.get('duration', raw['format']['duration']))
    rotation = next((float(v['rotation']) for v in stream.get('side_data_list', [])
                     if 'rotation' in v), float(stream.get('tags', {}).get('rotate', 0)))
    width, height = stream['width'], stream['height']
    if round(rotation) % 180:
        width, height = height, width
    with video.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    if fps <= 0 or duration <= 0:
        raise ValueError('Video has no usable duration/frame rate')
    frame_count = str(stream.get('nb_frames', ''))
    return {'source': str(video.resolve()), 'source_sha256': digest, 'fps': fps,
            'duration_sec': duration, 'frames': int(frame_count) if frame_count.isdigit() else round(duration * fps),
            'source_resolution': [width, height], 'rotation': rotation,
            'color_transfer': stream.get('color_transfer'),
            'hdr': stream.get('color_transfer') in ('arib-std-b67', 'smpte2084')}


def frame_at(info, requested, destination: Path, preview_size=None, roi_top=0):
    """FFmpeg handles rotation and HDR. Each request decodes only the nearby GOP."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    filters = ['showinfo']
    if roi_top:
        filters.append(f'crop=iw:ih-{roi_top}:0:{roi_top}')
    if preview_size:
        # Downsample geometry previews before allocating HDR float buffers.
        filters.append(f'zscale=w={preview_size[0]}:h={preview_size[1]}' if info['hdr']
                       else f'scale={preview_size[0]}:{preview_size[1]}')
    if info['hdr']:
        filters.append(TONE)
    command = ['ffmpeg', '-v', 'info', '-threads', '1', '-ss', str(requested), '-copyts',
               '-i', info['source'], '-an', '-filter_threads', '1', '-vf', ','.join(filters),
               '-frames:v', '1', '-threads', '1', '-update', '1', '-y']
    if destination.suffix.lower() == '.jpg':
        command += ['-q:v', '2']
    result = subprocess.run(command + [str(destination)], capture_output=True, text=True)
    if result.returncode or not destination.exists():
        raise RuntimeError(f'Frame at {requested:.3f}s failed: {result.stderr[-1500:]}')
    match = re.search(r'\bn:\s*0\s+pts:\s*-?\d+\s+pts_time:([\d.e+\-]+)', result.stderr)
    return float(match.group(1)) if match else requested


def propose_quads(frame):
    """Broad proposals only; a human/vision agent checks missing and duplicate borders."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    proposals = []
    total_area = frame.shape[0] * frame.shape[1]
    for threshold in (110, 150, 190, 220):
        mask = (gray > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if not total_area * .008 < area < total_area * .8:
                continue
            perimeter = cv2.arcLength(contour, True)
            q = cv2.approxPolyDP(contour, .025 * perimeter, True)
            if len(q) != 4 or not cv2.isContourConvex(q):
                continue
            quad = order_quad(q)
            width = np.linalg.norm(quad[1] - quad[0])
            height = np.linalg.norm(quad[3] - quad[0])
            if min(width, height) < 25 or not .35 < width / height < 3:
                continue
            if any(cv2.intersectConvexConvex(quad, existing)[0] / min(area, cv2.contourArea(existing)) > .65
                   for existing in proposals):
                continue
            proposals.append(quad)
    return [q.tolist() for q in proposals]


def archive_source(video: Path, folder: Path):
    video = video.resolve()
    folder = folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / video.name
    if video == target:
        return video
    suffix = 2
    while target.exists():
        target = folder / f'{video.stem}_{suffix}{video.suffix}'
        suffix += 1
    shutil.move(str(video), str(target))
    return target


def prepare_video(video: Path, root: Path, interval=1.0):
    if interval <= 0:
        raise ValueError('Sampling interval must be positive')
    if not video.is_file():
        raise FileNotFoundError(video)
    video = archive_source(video, root.parent / 'original_videos')
    info = probe(video)
    job = root / 'jobs' / info['source_sha256'][:16]
    job.mkdir(parents=True, exist_ok=True)
    previous = job / 'video_info.json'
    if previous.exists() and json.loads(previous.read_text())['source_sha256'] != info['source_sha256']:
        raise ValueError('Unexpected job hash collision')
    atomic_json(previous, info)
    width, height = info['source_resolution']
    factor = min(720 / width, 1280 / height, 1)
    preview_size = [round(width * factor), round(height * factor)]
    preview_index_path = job / 'preview_index.json'
    cached = json.loads(preview_index_path.read_text()).get('frames', {}) if preview_index_path.exists() else {}
    previews, proposals, items = {}, [], []
    for step in range(math.ceil(info['duration_sec'] / interval)):
        requested = step * interval
        if requested >= info['duration_sec'] - 1 / info['fps']:
            continue
        index = round(requested * info['fps'])
        path = job / 'debug' / 'samples' / f'{index:06}.jpg'
        frame = cv2.imread(str(path)) if path.exists() else None
        timestamp = (cached.get(str(index), {}).get('time_sec', requested) if frame is not None
                     else frame_at(info, requested, path, preview_size))
        previews[str(index)] = {'time_sec': timestamp, 'preview_file': str(path.relative_to(job))}
        frame = cv2.imread(str(path))
        if frame is None:
            raise RuntimeError(f'Unreadable preview {path}')
        quads = propose_quads(frame)
        proposals.append({'reference_frame': index, 'time_sec': timestamp, 'quads': quads})
        drawing = frame.copy()
        for q in quads:
            cv2.polylines(drawing, [np.asarray(q, np.int32)], True, (0, 255, 0), 2)
        annotated = job / 'debug' / f'proposed_{index:06}.jpg'
        cv2.imwrite(str(annotated), drawing)
        items.append((annotated, f'frame {index} | {timestamp:.2f}s'))
        atomic_json(preview_index_path, {'preview_resolution': preview_size, 'frames': previews})
        print(f'Preview {index} at {timestamp:.2f}s', flush=True)
    atomic_json(job / 'preview_index.json', {'preview_resolution': preview_size, 'frames': previews})
    atomic_json(job / 'proposals.json', {'video_sha256': info['source_sha256'], 'frames': proposals})
    atomic_json(job / 'annotations.template.json', {
        'video': info['source'], 'source_sha256': info['source_sha256'],
        'coordinate_space': f'{preview_size[0]}x{preview_size[1]} preview', 'scenes': [],
        'example_scene': {'id': 0, 'reference_frame': 0, 'start_sec': 0, 'end_sec': 1,
                          'cards': [{'id': 'card_001', 'side': 'unknown', 'row': 1,
                                     'quad': [[10, 10], [200, 10], [200, 130], [10, 130]],
                                     'rotation': 'none'}]}})
    for start in range(0, len(items), 12):
        contact_sheet(items[start:start + 12], job / f'video_overview_{start // 12 + 1:02}.jpg',
                      columns=4, cell_size=(260, 430))
    recognition = job / 'recognition'
    recognition.mkdir(exist_ok=True)
    shutil_source = Path(__file__).resolve().parents[2] / 'references' / 'recognition.md'
    (recognition / 'INSTRUCTIONS.md').write_text(shutil_source.read_text(encoding='utf-8'), encoding='utf-8')
    return job


def validate_annotations(info, annotations, preview_size):
    if annotations.get('source_sha256') != info['source_sha256']:
        raise ValueError('Annotations must belong to this video (source_sha256 mismatch)')
    scenes = annotations.get('scenes')
    if not scenes:
        raise ValueError('No reviewed cards. Create annotations.json from the per-video template and proposals.')
    ids, scene_ids = set(), set()
    for scene in scenes:
        if scene['id'] in scene_ids:
            raise ValueError('Duplicate scene ID')
        scene_ids.add(scene['id'])
        if not 0 <= scene['start_sec'] < scene['end_sec'] <= info['duration_sec'] + .05:
            raise ValueError('Scene times are outside the video')
        if not scene['start_sec'] <= scene['reference_frame'] / info['fps'] <= scene['end_sec']:
            raise ValueError('Reference frame is outside the scene')
        for card in scene['cards']:
            if card['id'] in ids or not re.fullmatch(r'card_\d+', card['id']):
                raise ValueError('Card IDs must be unique within one video')
            ids.add(card['id'])
            q = np.asarray(card['quad'], np.float32)
            if q.shape != (4, 2) or not np.isfinite(q).all() or not cv2.isContourConvex(q):
                raise ValueError('Invalid card quadrilateral')
            if q.min() < 0 or q[:, 0].max() >= preview_size[0] or q[:, 1].max() >= preview_size[1]:
                raise ValueError('Card border is outside preview')
            if card.get('rotation', 'none') not in ('none', 'cw', 'ccw', '180'):
                raise ValueError('Invalid card rotation')
            card.setdefault('rotation', 'none')
            card.setdefault('side', 'unknown')
            card.setdefault('row', 0)
    return scenes


def extract_video(job: Path, interval=.4, only_scene=None):
    if interval <= 0:
        raise ValueError('Candidate sampling interval must be positive')
    info = json.loads((job / 'video_info.json').read_text())
    previews = json.loads((job / 'preview_index.json').read_text())
    annotations_path = job / 'annotations.json'
    annotations = json.loads(annotations_path.read_text())
    size = previews['preview_resolution']
    scenes = validate_annotations(info, annotations, size)
    selected_scenes = scenes if only_scene is None else [s for s in scenes if s['id'] == only_scene]
    if not selected_scenes:
        raise ValueError('Unknown scene ID')
    scale = info['source_resolution'][0] / size[0]
    crop_top = max(0, math.floor((min(p[1] for s in scenes for c in s['cards'] for p in c['quad']) - 24) * scale / 2) * 2)
    # Keep coordinates uniform, source pixels untouched. New videos have no fixed ROI offset.
    index_path = job / 'native_index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {
        'source_fps': info['fps'], 'source_frames': info['frames'],
        'source_resolution': info['source_resolution'], 'preview_resolution': size,
        'scale': scale, 'native_roi_top': crop_top,
        'preview_roi_top': round(crop_top / scale), 'samples': {}, 'sample_indices': [],
        'photo_pixels': 'Native source pixels; HDR converted to BT.709' if info['hdr'] else 'Native SDR source pixels',
        'sampling_strategy': 'Reviewed per-video scenes and sampled sharpness candidates'}
    requested = {}
    for scene in selected_scenes:
        requested[scene['reference_frame']] = scene['reference_frame'] / info['fps']
        steps = math.ceil((scene['end_sec'] - scene['start_sec']) / interval)
        for step in range(steps):
            stamp = scene['start_sec'] + step * interval
            if stamp < info['duration_sec'] - 1 / info['fps']:
                requested[round(stamp * info['fps'])] = stamp
    for number, stamp in sorted(requested.items()):
        native = job / 'debug' / 'native' / f'{number:06}.png'
        if not native.exists() or str(number) not in index['samples']:
            timestamp = frame_at(info, stamp, native, roi_top=index['native_roi_top'])
            index['samples'][str(number)] = {'native_file': str(native.relative_to(job)),
                                             'time_sec': timestamp, 'frame_index_is_estimate': True}
        frame = cv2.imread(str(native))
        if frame is None:
            raise RuntimeError(f'Unreadable native frame {native}')
        transform = np.array([[1 / scale, 0, 0], [0, 1 / scale, index['native_roi_top'] / scale]], np.float32)
        preview = cv2.warpAffine(frame, transform, tuple(size), flags=cv2.INTER_LINEAR)
        path = job / 'debug' / 'samples' / f'{number:06}.jpg'
        cv2.imwrite(str(path), preview, [cv2.IMWRITE_JPEG_QUALITY, 98])
        index['samples'][str(number)]['preview_file'] = str(path.relative_to(job))
        if any(scene['reference_frame'] == number for scene in scenes):
            cv2.imwrite(str(job / 'debug' / f'frame_{number:06}.jpg'), preview)
        index['sample_indices'] = sorted(map(int, index['samples']))
        atomic_json(index_path, index)
    # Invalidate ranking if borders/spans changed, or changed inputs would silently reuse stale crops.
    signature = hashlib.sha256(annotations_path.read_bytes() + str(interval).encode()).hexdigest()
    signature_path = job / 'ranking_signature.txt'
    if not signature_path.exists() or signature_path.read_text() != signature:
        for checkpoint in (job / 'debug').glob('ranked_scene_*.json'):
            checkpoint.unlink()
        signature_path.write_text(signature)
    ranked = rank_candidates(job, scenes, info['fps'], info['frames'], only_scene=only_scene)
    ranked = apply_review_choices(job, ranked)
    export_cards(Path(info['source']), job, selected_scenes, info['fps'], ranked, append=only_scene is not None)
    return {'job': str(job), 'cards': sum(len(scene['cards']) for scene in selected_scenes),
            'next_step': 'Review crops and recognize cards here; then run append'}
