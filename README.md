# Project Showcase

**Turn a working project into slides and a narrated demo.**

English · [한국어](i18n/README.ko.md)

A skill for Claude Code and Codex. It reads your project, checks real outputs, and prepares four design directions before building your presentation.

![Project Showcase — latest presentation cover](public/preview.png)

## Prerequisites

You need **Claude Code or Codex**, **Python 3.12**, **Node.js 22+**, **Git**, **FFmpeg**, and **Google Chrome**. Internet access is needed for installation and Korean voice synthesis.

New to these tools? Follow the [step-by-step setup for macOS and Windows](docs/installation.md) first. It explains what to install, where to enter commands, and how to check that everything works.

## Install

Open Terminal on macOS or PowerShell on Windows, then run:

```sh
git clone https://github.com/Maximus2580/project-showcase.git
cd project-showcase
```

**macOS**

```sh
python3.12 scripts/install_global.py
```

**Windows**

```powershell
py -3.12 scripts/install_global.py
```

The installer prepares its own Python environment and dependencies, then installs the skill for both Claude Code and Codex. Your project's environment stays separate. Start a new agent session after installation.

## Use it

Open the project you want to present. In Claude Code, run `/project-showcase`. In Codex, ask:

```text
Use project-showcase to introduce this project.
Inspect the code and real outputs. Show me four design directions,
with a cover, a demo slide, and a dense content slide for each.
Wait for my choice, then make an 8-slide HTML presentation
and an approximately 3-minute video with Korean narration and subtitles.
```

1. **Review the directions.** Open the comparison HTML the agent gives you.
2. **Choose or revise.** For example: “Use B, revision r002. Keep the large demo, but use a lighter background.”
3. **Review the presentation.** The agent builds the full slides, script, and video after your selection.
4. **Watch and listen.** Play the final video from start to finish, then tell the agent what needs fixing or ask for the delivery ZIP.

If you request design changes, the agent shows a new revision for you to choose before continuing.

For a specific style, include the audience, brand colors, or a reference in your first request. There is no fixed visual theme. The agent authors the design; the tools render it and check the files.

## What you get

Everything stays in `showcase-output/<project>/`:

| File | Open it to… |
| --- | --- |
| `design/index.html` | Compare four directions and their three representative slides |
| `deck/index.html` | Present eight slides; use arrow keys, **F** for fullscreen |
| `renders/*.mp4` | Watch the narrated, subtitled video |
| `SCRIPT.md` · `SPEAKER-NOTES.md` | Read the script and presentation notes |
| `exports/*.zip` | Share the delivery bundle with its review status |

Default video: **1920 × 1080, 30 fps, Korean narration**. Timing follows measured speech. Unverified features and missing demo screens are labeled; the skill does not invent results.

## Update or resume

Update from the cloned repository:

```sh
git pull
python3.12 scripts/install_global.py --replace
```

On Windows, use `py -3.12` instead of `python3.12`. Replacement backs up the previous installation.

To continue a presentation, ask the agent:

```text
Resume project-showcase in showcase-output/my-project.
Keep my edits, reuse unchanged audio, and tell me what review is still needed.
```

## Help

- [Installation, environment check, and common fixes](docs/installation.md)
- [Design workflow and revision commands](skills/project-showcase/references/design.md) — agent reference in Korean
- [Development and tests](docs/development.md)

macOS has been tested. Windows setup is documented, but a complete Windows presentation run still needs validation. Final listening is a separate review step; automatic checks do not mark it complete.

[MIT license](LICENSE). Bundled Pretendard font: [SIL Open Font License](skills/project-showcase/assets/fonts/LICENSE-Pretendard.txt).
