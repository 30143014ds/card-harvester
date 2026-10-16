# card-harvester

An AI-powered agent skill that turns videos of business cards into structured contacts, with batch extraction, recognition, deduplication, and export to Excel and vCard

The assistant reviews scenes, crops cards at native resolution, reads them with
its own vision, and flags uncertain details. No external OCR API is required.

- Create a new workbook or append to an existing one, retaining manual edits.
- Recover contact data and photos from a previously delivered XLSX.
- Export all phone numbers and email addresses without a country-specific filter.
- Keep contact text in its original language; workbook labels are English.
- Use in Codex, Claude Code, or a capable hosted session. Persistent ChatGPT Web
  distribution uses a plugin; the skill ZIP alone is not an account installation.

Read [INSTALL.md](INSTALL.md) for platform setup and
[DEPENDENCIES.md](DEPENDENCIES.md) for Python, ffmpeg, and optional helpers.
The assistant's entry point is [SKILL.md](SKILL.md).

Example request:

> Use Card Harvester to process this video and create a new Excel workbook
> with linked card photos. Check dependencies first.

A working host must expose file execution and image viewing. Hosted installations
are not yet tested end to end. See the installation guide for details.

## License

[MIT](LICENSE). Copyright (c) 2026 Denis.
