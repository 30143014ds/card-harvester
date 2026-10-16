# Video processing and workbook state

The assistant runs these commands. `<skill>` is the absolute skill folder,
`<work>` is a writable working directory outside it, and `<library>` / `<xlsx>`
are explicitly selected paths. Resolve placeholders before running commands.
Read [dependencies](../DEPENDENCIES.md) and [host capabilities](platforms.md).

```bash
python <skill>/scripts/check_environment.py --mode video
```

## Start an isolated workbook

```bash
python <skill>/scripts/workbook_state.py new <work>/contacts_new
```

This returns `<library>=<work>/contacts_new/card_library` and
`<xlsx>=<work>/contacts_new/business_cards.xlsx`. The target must be new;
choose another name on collision. A new-table request never replaces an old table.

## Continue an existing workbook

The delivered XLSX contains the contact data and photos; original videos and
separate crops are not required for appending. If working state was deleted:

```bash
python <skill>/scripts/workbook_state.py restore <xlsx> --library <work>/recovered/card_library
```

Restore recovers rows, hidden IDs, photos, sources, review flags, and company evidence
from comments. It uses fixed gallery order rather than a possibly sorted contact
table. An existing catalog must have the same IDs. Original OCR JSON and source
videos cannot be recovered from XLSX and are not needed to append another video.
Readers accept both English and legacy Russian workbooks; new exports use English labels.

If the user uploaded an edited workbook, restore that file into a fresh working
library or import its edits into a retained catalog before appending:

```bash
python <skill>/scripts/cards.py --library <library> --xlsx <xlsx> import-edits <work>/edited.xlsx
```

Never map photos by sorted table row when a fixed gallery is available.
If IDs/photos are missing, preserve the previous result and explain what is missing.

## Prepare and annotate each new video

```bash
python <skill>/scripts/cards.py --library <library> --xlsx <xlsx> prepare <work>/upload.MOV --interval 1.2
```

Preparation moves the input into `<library>/../original_videos/`, retaining the source,
and creates `<library>/jobs/<sha256-prefix>`. Resolve the actual upload path first.
Previews shrink to fit 720×1280 **before** HDR tone mapping. Run one heavy decoder
at a time; simultaneous 4K HDR decodes can exhaust memory. Long stages may run in the
background with logs. HDR needs ffmpeg's zscale and tonemap filters.

Inspect every `video_overview_*.jpg`, then individual `debug/samples/*.jpg`.
`proposals.json` may miss cards in transparent sleeves. Build `annotations.json`
from `annotations.template.json`: remove `example_scene`, retain `source_sha256`.

```json
{
  "source_sha256": "<from video_info.json>",
  "scenes": [{
    "id": 0,
    "reference_frame": 45,
    "start_sec": 0.8,
    "end_sec": 3.2,
    "cards": [{
      "id": "card_001",
      "quad": [[20, 450], [240, 445], [245, 780], [18, 790]],
      "rotation": "ccw",
      "side": "upper",
      "row": 1
    }]
  }]
}
```

Quad order is TL, TR, BR, BL in **preview** coordinates, not native-video coordinates.
`reference_frame` is an overview index inside the stable scene.
Rotation is `none`, `cw`, `ccw`, or `180`. Card IDs are local to this video,
not old workbook row numbers. Determine card count/layout by inspection.

```bash
python <skill>/scripts/cards.py --library <library> --xlsx <xlsx> extract <job> --interval 1.0
```

For long videos, add `--scene 0` and process successive scenes. Finish annotations
before native export where possible. Extraction resumes from cache. Recognition can
start on ready groups, but import only after every assigned card has a valid JSON.

Inspect `overview_*.jpg`, native `cards/*.png`, and `alternatives/*.png`.
Fix a bad crop and regenerate it rather than treating cut-off text as illegible.
Select a clearly better frame through `review_choices.json`:

```json
{"card_001": {"selected_frame": 60, "reason": "Less glare over the contact details"}}
```

Re-export may renumber alternatives. Make changes before recognition, or preserve
previous evidence images under separate names and update the manifest consistently.

## Recognition, company evidence, and duplicates

Follow [recognition.md](recognition.md) and [platforms.md](platforms.md).
Actually display each image and inspect alternatives as needed. Save JSON after
every 1–3 cards. Each required `id` matches its filename. If delegating, use disjoint
ranges and do not wait for the entire video when assigned crops are ready.

```bash
python <skill>/scripts/cards.py --library <library> --xlsx <xlsx> domains <job>
```

Store verified corporate domains in a working JSON, starting from the empty
`scripts/business_cards/company_domains.json`, and pass `--companies <domains.json>`.
Example: `{"example.com":{"company":"Example","url":"https://example.com/contacts/","evidence":"Official contact page"}}`.
A group-wide domain may require checking the division's printed website.
Alternatively put `company` and `company_evidence` (`domain,url,evidence,method`)
directly in recognition JSON. Do not replace printed phone numbers or job titles
with newer web data; do not search for a personal email to fill a gap.

For backs without independent contacts, use `skip_as_contact:true`, `skip_reason`,
and `related_card_id` when known. The image and explanation remain in the job.
Try local zxing-cpp for QR/vCard data and compare it with the front.
For repeats within a video, skip the inferior instance with a link to the best one.
For an existing contact, set `duplicate_of:"c_..."` and `duplicate_reason`
only after reviewing **both** photos, including company, role, and contact details.
A shared name/email/phone is insufficient. Without an explicit decision, the
importer merges only exact structured duplicates.

## Import and validate

```bash
python <skill>/scripts/cards.py --library <library> --xlsx <xlsx> --companies <domains.json> append <job>
```

Import validates the batch before catalog changes, backs up the catalog, and
preserves manual edits and stable IDs. Use `export` or `status` with the same
paths for regeneration or counts.

After export verify:

- Prior IDs, fields, manual edits, and gallery order remain; counts reconcile.
- Each contact has one image on Contacts and one on Originals. G links to its
  gallery location; H is the hidden ID.
- Originals has four cards per row with no filter: A4/C4/E4/G4, then A7.
- Uncertain fields appear on Review; fax-only numbers are excluded from phones.
- Each distinct JPEG is stored once in XLSX and reused for both photo placements.

For an explicit cleanup request, first restore data/photos from the retained XLSX
into a temporary folder. Then remove only the agreed sources and intermediates.
Do not delete unrelated workspace files through broad globs.
