# Before you install

[English](installation.md) · [한국어](installation.ko.md) · [Back to README](../README.md)

Project Showcase runs on your computer. Install these tools once, then use the skill in any project.

| Tool | What it does |
| --- | --- |
| Claude Code or Codex | Reads the project and writes the presentation |
| Python 3.12 | Runs the presentation pipeline |
| Node.js 22+ and npm | Runs the browser and video tools |
| FFmpeg and ffprobe | Encodes video and checks media duration |
| Google Chrome | Renders HTML slides and video frames |
| Git | Downloads and updates this repository |

Already have a tool? Keep it and check its version below.

## Set up your coding agent

Install and sign in to either one. Skip this if you already use it with your project.

- [Claude Code official quickstart](https://code.claude.com/docs/en/quickstart)
- [Codex official quickstart](https://developers.openai.com/codex/quickstart)

## macOS

1. Press **⌘ Space**, type **Terminal**, and open it.
2. If `brew --version` is not found, [install Homebrew](https://brew.sh/) and follow its printed **Next steps**. Those steps make `brew` available in Terminal.
3. Install the required command-line tools:

   ```sh
   brew install python@3.12 node@24 ffmpeg git
   ```

4. Make the versioned Node installation available in this Terminal session:

   ```sh
   export PATH="$(brew --prefix node@24)/bin:$PATH"
   ```

   To keep this setting in new Terminal windows, run this once:

   ```sh
   printf '%s\n' 'export PATH="$(brew --prefix node@24)/bin:$PATH"' >> "$HOME/.zprofile"
   ```

   Reopen Terminal. Start your coding agent from that terminal, or configure the same Node path in your editor. The agent must also be able to find `node` and `npm`.

5. [Download Google Chrome](https://www.google.com/chrome/) if it is not installed. Open the download and drag Chrome to **Applications**.
6. Check the tools:

   ```sh
   python3.12 --version
   node --version
   npm --version
   git --version
   ffmpeg -version
   ffprobe -version
   ```

Each command should print a version. Node must be 22 or newer. If you already use another supported Node installation, keep its existing PATH configuration.

Continue with [Install](../README.md#install) in the same Terminal window.

## Windows

1. Open **Start**, search for **PowerShell**, and open it.
2. Run these commands one at a time. Skip tools you already have:

   ```powershell
   winget install --exact --id Python.Python.3.12
   winget install --exact --id OpenJS.NodeJS.LTS
   winget install --exact --id Git.Git
   winget install --exact --id Gyan.FFmpeg
   winget install --exact --id Google.Chrome
   ```

   If `winget` is missing, install Microsoft's [App Installer](https://learn.microsoft.com/windows/package-manager/winget/) first.

3. **Close PowerShell and open it again.** This refreshes the paths added by the installers.
4. Check the tools:

   ```powershell
   py -3.12 --version
   node --version
   npm.cmd --version
   git --version
   ffmpeg -version
   ffprobe -version
   ```

Continue with [Install](../README.md#install). Use `py -3.12` for Python commands. A full Windows presentation run has not yet been validated.

## Check the installed skill

The installer prints the full command path. Run an environment check from a folder where you can save files:

**macOS**

```sh
"$HOME/.local/bin/project-showcase" --out showcase-output/preflight preflight
```

**Windows**

```powershell
& "$env:USERPROFILE\.local\bin\project-showcase.cmd" --out showcase-output/preflight preflight
```

`preflight PASS` means the test synthesized speech, rendered diagnostic frames, and produced a short video. It does not approve the content or listening quality of your presentation.

## Common fixes

| What you see | What to do |
| --- | --- |
| `python3` uses an old macOS Python | Use `python3.12`, as shown above |
| `node`, `npm`, or `ffmpeg` is not found | Reopen the terminal; on macOS also apply the PATH line above |
| `project-showcase` is not found | Use the full command path shown above or printed by the installer |
| The agent cannot find the skill | Start a new agent session; Claude Code uses `/project-showcase` |
| An installation already exists | Rerun `scripts/install_global.py --replace`; it backs up the old install |
| `E_DESIGN_SELECTION_REQUIRED` | Open the comparison and choose a direction and revision first |
| A network or rendering step fails | Give the agent the error and output folder; ask it to resume |

For a nonstandard Chrome location, set `CHROME_PATH` to the Chrome executable before running the command. Keep API keys and private customer data out of scripts sent to online voice synthesis.
