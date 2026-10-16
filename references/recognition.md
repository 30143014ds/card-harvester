# Recognize a prepared video job

Work only in the assigned job directory. Check `manifest.json` and its
`cards/card_XXX.png` entries first. Follow [platforms.md](platforms.md) for models,
image tools, and optional delegation. Use the assistant's vision, without an OCR API.

Actually open each card image. Check 1–3 alternatives when unsure. If edges or text
are cropped, correct the geometry using the source frame before calling text unreadable.
Save one JSON per card as `recognition/card_XXX.json`; `id` must match its filename.

```json
{
  "id": "card_001",
  "company": null,
  "full_name": null,
  "position": null,
  "emails": [],
  "phones": [],
  "fax_phones": [],
  "raw_text": "Visible text in the original language",
  "uncertain_fields": [],
  "notes": [],
  "images_used": ["cards/card_001.png"]
}
```

Put all work, mobile, and unlabeled phone numbers in `phones`; keep fax-only numbers
in `fax_phones`. A combined phone/fax number may count as a phone. Preserve extensions
with the full number, for example `+44 20 7946 0123, ext. 456`. Keep country codes
as printed; never infer one from language, another number, or a presumed country.
Do not prioritize any country or phone type. Preserve national/local numbers.
Keep crossed-out numbers in raw text/notes and flag unclear current validity.

Never complete illegible digits, email addresses, or parts of a name. Do not search
for a personal email to fill a gap. Leave an uncertain field empty and add an object:
`{"field":"phones","visible_fragment":"...","reason":"..."}`.
Missing position is null; a description of services is not a job title.
Keep names and job titles in their original language.

If the company is unreadable, the main assistant may check a confidently read
corporate email domain on the official website. Save verified names and source URLs
in a working company-domain JSON or the recognition record, outside the skill.
A legible domain is usable even when the mailbox is unclear, but does not establish
the complete email. Public email services do not identify employers.

The same person or email can occur on cards for different roles. Do not merge on
name or email alone. The main assistant appends the reviewed batch using the full
command in [workflow.md](workflow.md).
