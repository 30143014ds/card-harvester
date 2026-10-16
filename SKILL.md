---
name: card-harvester
license: MIT
description: Extract unique business cards from uploaded videos, recognize contacts using the assistant's vision, create or append an Excel workbook with linked card photos, or export a business-card workbook to VCF for iPhone and Android.
---

# Card Harvester

Produce an XLSX containing company, full name, position, email, all phone numbers,
a card photo, and a link to its fixed position on the Originals sheet (four per row).
Use English workbook labels and preserve contact text in its original language.
Run the workflow for the user; do not make them operate scripts or an OCR API.

For XLSX-to-VCF requests, read [references/vcf.md](references/vcf.md) and use
`scripts/export_vcf.py`. Export first name, last name, company, email, and **all**
phone numbers, regardless of country or mobile/landline type. Do not infer a country
code for national/local numbers. Keep separate workbook rows as separate contacts.
This mode needs no video processing, photo restoration, or new recognition.

## Environment and workbook selection

Read [references/platforms.md](references/platforms.md) for Codex, Claude, and
ChatGPT Web capabilities. Before processing, run `scripts/check_environment.py`
with `--mode video`, `--mode workbook`, or `--mode vcf`.
[DEPENDENCIES.md](DEPENDENCIES.md) describes runtime requirements and setup.
Skill installation does not install Python packages or ffmpeg.

- **Append/add to the current workbook:** use the uploaded or previously selected XLSX.
  `business_cards.xlsx` is a convention, not a required filename or path.
- **New/separate workbook:** create an isolated work directory and a new XLSX.
  Preserve existing workbooks and their catalogs.
- Ask which workbook only if multiple candidates remain equally plausible.
  Independent video preparation can continue while that choice is pending.

Pass working-library and output paths explicitly. For video processing, restoration,
annotations, and validation, read [references/workflow.md](references/workflow.md).

## Extraction and recognition

Create a separate job for **each video**. Inspect the full overview and annotate
stable scenes and card borders afresh: frames may contain several cards, backs,
folded cards, or repeated appearances. Never reuse another video's geometry.
Crop from native resolution with perspective and rotation correction. Prefer a
legible alternative over a sharper frame obscured by glare or a finger.
Retain the complete contact block.

Recognize with the current assistant's vision, without an external OCR API.
Respect an explicit model/cost preference; if unavailable, explain and agree on a
replacement before recognition. Use only tools and model options available in the
current host. Open every card image visually, not just as file bytes.
Read [references/recognition.md](references/recognition.md) for the JSON schema.

Combine work, mobile, and unclassified phone numbers; keep fax numbers separate.
Check extensions against the photo. Do not guess illegible digits or email addresses:
inspect alternatives and flag unresolved uncertainty. A confidently read corporate
email domain and an official website can establish a company; record the URL and
evidence. A public email provider does not identify an employer. A department name
without a job title belongs in raw text, leaving position empty.

## Append and deliver

Match rows by hidden `_id`. Preserve prior fields, manual edits, and gallery positions.
A confirmed duplicate with the same company, role, and contact details can reference
the existing row. A different employer or role is a separate card; do not automatically
merge translated versions. A QR/vCard-only or advertising back does not create an
empty contact.

Use floating XLSX photos: table previews fit 340×188 px and gallery photos 450×308 px.
Link to specific Originals cells. Use JPEG quality 92 without resolution reduction
or chroma subsampling. Store identical photo bytes once in the XLSX. Do not recompress
JPEGs restored from an existing workbook. Do not claim Google Sheets or phone-import
testing without an actual import session.

Deliver the XLSX link, added/total contact counts, and material uncertainties.
Create demonstration videos only on request. Delete source or intermediate files
only after a cleanup request, and first verify that the delivered XLSX can restore
all rows, IDs, and photos. Keep user contacts, photos, and videos outside the skill.
