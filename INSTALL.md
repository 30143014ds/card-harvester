# Install Card Harvester

Start with the OpenAI option you use: Codex CLI, Codex desktop, ChatGPT desktop,
or ChatGPT Web. Claude instructions follow below. Installation makes the workflow
available; [runtime dependencies](DEPENDENCIES.md) are a separate setup step.

## Codex CLI

### Ask Codex to install it

Paste this into a Codex session:

```text
Install the skill from https://github.com/30143014ds/card-harvester
as card-harvester. SKILL.md is at the repository root.
Set up its runtime dependencies and check the environment before processing.
```

Codex can use its skill installer or copy the complete skill folder into a supported
location. The repository root is the skill, so retain its scripts and references.
Start a new turn and invoke `$card-harvester` or select it through `/skills`.

### Manual installation

Copy or clone the complete repository to:

- `~/.agents/skills/card-harvester/` for personal use.
- `.agents/skills/card-harvester/` inside a project.

For a personal installation on macOS/Linux:

```bash
git clone https://github.com/30143014ds/card-harvester.git ~/.agents/skills/card-harvester
```

The entry point must be `card-harvester/SKILL.md`. If the destination already
exists, update that installation instead of overwriting it. If discovery does not
refresh, restart the client. See [DEPENDENCIES.md](DEPENDENCIES.md) for setup.

[Official skill documentation](https://learn.chatgpt.com/docs/build-skills)

## Codex desktop

Open a local Codex session and use the same installation prompt as for the CLI.
For manual setup, use the personal or project skill locations above on the machine
where the session runs. Select the installed skill or ask to use `$card-harvester`.

Give the session a local video path or attach the file where supported. The
assistant should check dependencies and use its Python/shell and image tools.
Installing the skill alone does not install ffmpeg or Python packages.
The optional `agents/openai.yaml` supplies the display name and default prompt.

## ChatGPT desktop

Standalone skills are supported in the ChatGPT desktop app. Open **Skills** in
the sidebar to view available skills. Where the local Codex runtime is available,
use the personal/project installation above and select Card Harvester through
the skill picker or an `@` mention.

Check that the session can access the skill's scripts and video, execute Python
and ffmpeg, and display extracted images. Local filesystem installation and
workspace-managed sharing have separate controls; availability depends on the
app and workspace. For broader reusable distribution, use a plugin.

[Official skill documentation](https://learn.chatgpt.com/docs/build-skills)

## ChatGPT Web

### Persistent installation through a plugin

Plugins are OpenAI's distribution route for reusable skills on the web. This
repository is a **skill bundle**, not a published plugin or an account-wide
installer. Local Codex skill paths do not install it into a ChatGPT Web account.

Where **Plugin Creator** is available, select `@Plugin Creator`, provide this
package as source material, and request a plugin containing the Card Harvester
skill and its Python scripts. Review it and test privately in Work.
For public distribution, package and submit a plugin through OpenAI's documented
workflow. Once published or shared, install it from Plugins and select it with
an @ mention. Availability depends on workspace settings.

[Build plugins in ChatGPT](https://learn.chatgpt.com/docs/build-plugins)
· [Package a plugin](https://developers.openai.com/plugins/build/plugins)

### Try the files in a single session

If the session accepts a ZIP and exposes file execution and image viewing, attach
`card-harvester.zip` in Work and ask:

> Unpack card-harvester.zip, read card-harvester/SKILL.md, and check the environment
> before processing my files. Use the bundled workflow for this conversation.

This is session use, not permanent installation. Upload formats and package
installation vary by account and runtime. The assistant needs Python, ffmpeg/ffprobe,
the Python packages, and image viewing. Use a local Codex session if these are
unavailable. A plugin does not provision runtime tools by itself.

## Claude Code

Copy the complete `card-harvester` folder into `~/.claude/skills/card-harvester/`
for personal use, or `.claude/skills/card-harvester/` inside a project.
Invoke `/card-harvester` and check [dependencies](DEPENDENCIES.md).

[Official Claude Code documentation](https://code.claude.com/docs/en/skills)

## Claude: web and desktop

1. Enable **Code execution and file creation** in **Settings → Capabilities**.
2. Open **Customize → Skills → + → Create skill → Upload a skill**.
3. Upload `card-harvester.zip` and enable it.

The ZIP must contain a single top-level `card-harvester/` folder with SKILL.md,
scripts, and references. If downloading from GitHub's **Code → Download ZIP**,
rename the extracted `card-harvester-main` folder to `card-harvester` and zip it
again before uploading. Keep all skill files inside that folder.

Account/organization settings may restrict custom skills. Uploading the skill does
not install ffmpeg or Python packages. Run the environment check before processing.

[Official Claude installation guide](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

## First task

> Use Card Harvester to process this business-card video. Create a new Excel
> workbook with linked card photos, then export all contacts and phone numbers
> to a VCF. Check dependencies first.

For appending, upload/select the existing workbook and say "append this video to
this workbook." For VCF-only export, upload/select the workbook and ask to export it.

## Validation status

The Python workflow and bundle structure are checked locally. Installation and full
recognition have not been exercised in Claude or ChatGPT Web.
Do not treat a successful package check as a completed host or device import test.
