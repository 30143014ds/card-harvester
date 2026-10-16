# Install Card Harvester

This package contains one portable skill and its scripts. Installation makes the
workflow discoverable; runtime dependencies are a separate step.
See [DEPENDENCIES.md](DEPENDENCIES.md) before processing your first video.

## Codex: local skill

Copy the complete `card-harvester` folder into one of:

- `~/.agents/skills/card-harvester/` for personal use.
- `.agents/skills/card-harvester/` in a project.

The installed entry point is `card-harvester/SKILL.md`. Mention
`$card-harvester` or select it through `/skills`. If discovery does not refresh,
restart the client. A repository URL can also be supplied to the skill installer.
The optional `agents/openai.yaml` supplies Codex UI metadata.

[Official skill documentation](https://learn.chatgpt.com/docs/build-skills)

## Claude Code: local skill

Copy the complete folder into `~/.claude/skills/card-harvester/` for personal use,
or `.claude/skills/card-harvester/` inside a project. Invoke `/card-harvester`.

[Official Claude Code documentation](https://code.claude.com/docs/en/skills)

## Claude: web and desktop

1. Enable **Code execution and file creation** in **Settings → Capabilities**.
2. Open **Customize → Skills → + → Create skill → Upload a skill**.
3. Upload `card-harvester.zip` and enable it.

The ZIP must contain a single top-level `card-harvester/` folder with SKILL.md,
scripts, and references. Account/organization settings may restrict custom skills.
A successful upload does not install ffmpeg or Python packages in hosted sessions.
The assistant must run the environment check before attempting the video workflow.

[Official Claude installation guide](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

## ChatGPT Web

### Persistent installation through a plugin

OpenAI documents plugins as the reusable distribution route for skills on the web.
This ZIP is a **skill bundle**, not a published plugin or an account-wide installer.
Local Codex skill paths do not install a skill into a ChatGPT Web account.

Where **Plugin Creator** is available, select `@Plugin Creator`, provide this package
as source material, and request a plugin containing the Card Harvester skill and
its Python scripts. Review the generated package and test it privately in Work.
For public distribution, package and submit a plugin through OpenAI's documented
plugin workflow. Once a published or shared plugin is available, install it from
Plugins and select it with an @ mention. Availability depends on workspace settings.

[Build plugins in ChatGPT](https://learn.chatgpt.com/docs/build-plugins)
· [Package a plugin](https://developers.openai.com/plugins/build/plugins)

### Try the files in a single session

If the session accepts the ZIP and exposes file execution and image viewing,
attach it in Work and ask:

> Unpack card-harvester.zip, read card-harvester/SKILL.md, and check the environment
> before processing my files. Use the bundled workflow for this conversation.

This is a capability-dependent session workflow, not permanent installation.
Do not assume every account can upload videos or install system packages.
The assistant needs Python, ffmpeg/ffprobe, the Python packages, and image viewing.
If these are unavailable, use a local Codex or Claude Code session instead.
A plugin does not provision those runtime tools by itself.

## First task

> Use Card Harvester to process this business-card video and create a new Excel
> workbook with linked card photos. Check dependencies first.

For appending, upload/select the existing workbook and say "append to this workbook."
For phone contacts, ask "Export this workbook to a VCF, keeping all phone numbers."

## Validation status

The Python workflow and bundle structure are checked locally. Installation and
full recognition have not been exercised in Claude or ChatGPT Web.
Do not treat a successful package check as a completed host or device import test.
