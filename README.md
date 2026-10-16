# card-harvester

An AI-powered agent skill that turns videos of business cards into structured contacts, with batch extraction, recognition, deduplication, and export to Excel and vCard.

**Film your business-card holder. Upload the video. Get Excel and VCF files.**

- **Start with 30 seconds of filming.** Record a short video, preferably in 4K at
  30 fps, to digitize your cards, keep photos of the originals, and add the contacts
  to your phone.
- **Capture the contact details.** Extract company names, full names, job titles,
  phone numbers, email addresses, and the text printed on each card. Unclear
  details are flagged for review.
- **Keep adding to your collection.** Process multiple videos, append new cards
  to an existing workbook, review duplicates, and retain your manual corrections.
- **Use Codex or Claude.** Works as an agent skill in Codex and Claude Code;
  hosted options and requirements are covered in the installation guide.

## How it works

1. **Record your cards.** Film yourself turning the pages of a business-card
   holder, or showing loose cards. Keep each page still long enough for the text
   to be readable. Prefer 4K at 30 fps, good light, and minimal glare; use longer
   or multiple videos for a larger collection.
2. **Give the video to your assistant.** Attach the video where uploads are
   supported, or give Codex/Claude Code its local file path. Ask:

   > Use Card Harvester to process this video. Create an Excel workbook with
   > linked card photos, then export all contacts and phone numbers to a VCF.

3. **Get your files.** Download the Excel workbook (`.xlsx`) with structured
   contacts and a linked gallery of card photos. Import the vCard file (`.vcf`)
   into iPhone or Android contacts. Names and contact text retain their original
   language.

For another batch, provide the existing workbook and ask to append the new video.

## Install in Codex CLI or Codex desktop

Open Codex and paste:

```text
Install the skill from https://github.com/30143014ds/card-harvester
as card-harvester. SKILL.md is at the repository root.
Set up its runtime dependencies and check the environment before processing.
```

Once installed, start a new turn and ask Codex to use `$card-harvester` with your
video. The assistant handles extraction, recognition, and export.

See [INSTALL.md](INSTALL.md) for manual installation, ChatGPT desktop/web, and
Claude setup. [DEPENDENCIES.md](DEPENDENCIES.md) lists Python and ffmpeg requirements.
The assistant's workflow starts in [SKILL.md](SKILL.md).

## License

[MIT](LICENSE). Copyright (c) 2026 Denis.
