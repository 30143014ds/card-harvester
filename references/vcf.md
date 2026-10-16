# Export XLSX contacts to VCF

Create one UTF-8 vCard 3.0 file for iPhone and Android from the selected workbook.
Read the XLSX directly without changing it. No video, photo restoration, or new
recognition is needed. Respect an explicitly selected workbook over a cumulative one.

## Fields and phone numbers

The default profile contains first name, last name, company, every email, and
**every phone number**. Middle names, positions, and photos are not included in this
profile. User requests may change the profile; do not claim unsupported fields were
exported without adapting the exporter.

Write each email as a separate `EMAIL;TYPE=INTERNET` field. Deduplicate identical
email addresses within a card; do not invent missing addresses.

Export mobile, landline, and local numbers from every country equally. Remove
formatting punctuation while preserving an explicit leading `+`. For international
notation, `(0)` is treated as an optional national trunk prefix.
Do not add country codes or convert national prefixes by assuming a country.
There is no country-specific phone filter or mobile-code table.

The exporter accepts extension markers such as `ext.`, `extension`, `x`, `#`,
and legacy Russian extension labels. Extensions become `,,` dialing pauses,
escaped in the VCF. Deduplicate the same number with the same extension within
one card; preserve different extensions. Do not merge separate workbook rows.
Preserve contacts without a phone. Report malformed/unreadable numbers rather
than guessing them, and review any existing Review-sheet uncertainties.

## Review names and export

Run commands for the user, storing working JSON and reports outside the skill.
Here `<skill>` is this skill folder and `<work>` is a writable session directory.

```bash
python <skill>/scripts/check_environment.py --mode vcf
python <skill>/scripts/export_vcf.py prepare-names <xlsx> --output <work>/names.json
```

Read the generated mapping and fill `first_name` and `last_name` for every entry.
Keys are hidden `_id` values, or `row:<number>` when no ID exists.
`source_name` must retain the original full name and is validated on export.
An empty string means the component is genuinely absent; null means review is unfinished.

Determine name order from the complete name and its cultural context, including
compound names. Do not assume the first word is the family name. Exclude titles and
academic degrees. Do not embed real names or contact lists in skill code.
If materially ambiguous, inspect the matching workbook photo or ask the user.

```bash
python <skill>/scripts/export_vcf.py export <xlsx> \
  --names <work>/names.json --output <work>/contacts.vcf --report <work>/vcf_report.json
```

All entries are validated before writing. The report includes contact, phone, and
email counts; contacts with/without phones; each selected number; skipped invalid
numbers; and source uncertainties. VCF output uses CRLF, escaping, and UTF-8-safe
folding at 75 bytes.

Verify names, diacritics, extensions, phone retention, and counts. For exporter
changes, run `python -m unittest discover -s <skill>/scripts -p test_export_vcf.py`.
If installed, the independent `vobject` parser provides an additional check; it is
not a runtime requirement. Do not claim real device import testing without a session.

Deliver the VCF link, contact count, counts with/without phones, phone/email totals,
and material uncertainties. Keep duplicates across rows unless asked to merge.
Import into an external account only when requested.
