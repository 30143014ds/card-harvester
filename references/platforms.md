# Host capabilities

## Shared rules

Use paths that exist in the current session; do not assume `/workspace` is available.
Video processing requires a Python/shell runtime, ffmpeg/ffprobe, the declared Python
packages, and a tool that actually displays extracted images to the model.
Run the appropriate environment check before processing.

Use the current model's vision unless the user selected another available model.
Do not silently replace an explicit model/cost preference, add a paid OCR service,
or connect an API to imitate another host's model. Quality and cost vary by model.
Sequential recognition works without subagents. Delegate only when available and
authorized; give each agent the job path, instructions, and a disjoint card range,
with no nested agents. Save recognition JSON incrementally.

## Codex

Use `view_image`, with `detail="original"` when supported.
Use the user's selected model/effort only when the current agent tools expose it.
If explicitly selecting model/effort requires a fresh context, use
`fork_turns="none"` and pass the needed instructions and job path.
See [installation](../INSTALL.md) for local skill locations.

## Claude Code and Claude

In Claude Code, use Read for supported image files. In hosted Claude, use the
session's image-display tools. Reading only binary file content is insufficient.
Use the current Claude model by default and recognize sequentially.
Do not assume Codex tool names, GPT model names, or agent arguments exist in Claude.
Hosted sessions may restrict package installation, network, memory, or video uploads.

## ChatGPT Web

For a persistent, reusable installation on the web, distribute this skill through
a plugin. A local skill directory or attached ZIP does not by itself install it
into the account. See [INSTALL.md](../INSTALL.md) for the supported plugin route.

Use Work with an execution environment that can access the bundled scripts and
uploaded files, run Python/ffmpeg, and display local images. An instruction-only
chat cannot execute this video workflow. If testing an attached ZIP in a capable
session, unpack it, read SKILL.md, and check dependencies first; describe this as
session use, not permanent installation.

If required tools or file types are unavailable, report the actual missing
capability and suggest a local Codex/Claude Code session or user-provided card images.
Do not claim cloud support merely because the skill or plugin was installed.
