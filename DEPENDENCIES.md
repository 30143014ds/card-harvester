# Runtime dependencies

The assistant performs processing. These setup commands are for the local runtime
used by Codex/Claude Code or a setup operator, not manual recognition steps.

| Component | Required for | Declaration/check |
| --- | --- | --- |
| Python 3.11+ | All scripts | `check_environment.py` |
| ffmpeg and ffprobe on PATH | Video preparation and native extraction | System installation; not a pip package |
| ffmpeg zscale and tonemap filters | HDR video | HDR flag in the environment check |
| numpy ≥2, opencv-python-headless ≥4.10 | Frames, geometry, quality ranking | Python requirements file |
| Pillow ≥11 | Images and XLSX photo restoration | Python requirements file |
| openpyxl ≥3.1 | XLSX reading, edits, restoration, VCF | Python requirements file |
| XlsxWriter ≥3.2.9 | XLSX export and floating images | Python requirements file |
| phonenumbers ≥9 | Format explicit international phone numbers | Python requirements file |
| zxing-cpp | Optional QR decoding | Optional requirements file |
| vobject | Optional independent VCF parser in tests | Optional requirements file |
| Assistant vision and image display | Contact recognition | Host capability, not a Python package |

The canonical Python list is
[scripts/business_cards/requirements.txt](scripts/business_cards/requirements.txt).
The root [requirements.txt](requirements.txt) includes it.
System dependencies are documented here because pip does not provide the ffmpeg
and ffprobe executables. Recognition uses the host assistant; no OCR API key is needed.

## Install Python packages locally

From the package root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_environment.py --mode video
```

On Windows, use `py -3 -m venv .venv` and
`.\.venv\Scripts\Activate.ps1` in PowerShell before pip.
Use the same virtual environment's Python when executing the skill.

For VCF-only use, `python -m pip install "openpyxl>=3.1"` is sufficient.
Check it with `python scripts/check_environment.py --mode vcf`.

Optional helpers:

```bash
python -m pip install -r requirements-optional.txt
```

## Install ffmpeg and ffprobe

Install a build appropriate for your OS that provides **both** executables:

- macOS with Homebrew: `brew install ffmpeg`.
- Debian/Ubuntu: `sudo apt-get update`, then `sudo apt-get install ffmpeg`.
- Windows: obtain an ffmpeg build and add its bin directory to PATH.
  Follow the [official download links](https://ffmpeg.org/download.html).

The assistant should use existing tools and install missing packages only within
the host's permissions. Do not attempt to bypass managed-environment restrictions.
Run `python scripts/check_environment.py --mode video --hdr` for HDR footage;
it checks zscale and tonemap. A lean ffmpeg build may lack them.

## Environment check

`scripts/check_environment.py` uses the standard library to report Python/package
versions and executable availability. It exits nonzero when a required item is
missing or unusable and does not install anything.

- `--mode video`: all Python dependencies plus ffmpeg/ffprobe.
- `--mode workbook`: XLSX/photo dependencies, without video packages or ffmpeg.
- `--mode vcf`: openpyxl only.
- `--hdr`: additionally check HDR filters in video mode.
- `--qr`: additionally require the optional zxing-cpp helper.

The check cannot establish whether the assistant can see images, accept a video
upload, or complete recognition. Verify those capabilities in the actual session.

## Hosted environments

Claude and ChatGPT Web control available tools, package installation, storage,
network access, and upload limits. Installing a skill/plugin does not install
system dependencies. Check each session and report actual missing capabilities.
A local environment gives the most direct control over ffmpeg and packages.
