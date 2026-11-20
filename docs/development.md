# Development

[Back to README](../README.md)

## Repository layout

```text
skills/project-showcase/   Installable skill, pipeline, references, and font
scripts/install_global.py User-level installer
tests/                    Pipeline, selection, browser, and installer regressions
docs/                     Setup and contributor guidance
i18n/README.ko.md          Korean user guide
public/preview.png        One current presentation cover
```

Generated decks, audio, video, ZIP files, logs, local review reports, and backups belong in ignored `showcase-output/` or `artifacts/`. Do not commit them. Test images are generated locally by `bootstrap.py`; the repository does not include demo applications or a gallery of sample outputs.

## Run tests

With Python 3.12, Node.js 22+, Chrome, and FFmpeg installed:

```sh
python3.12 -m venv .showcase-venv
.showcase-venv/bin/python -m pip install -r skills/project-showcase/requirements.txt
npm ci --prefix skills/project-showcase
.showcase-venv/bin/python -m unittest discover -s tests -v
```

On Windows, create the environment with `py -3.12`, and use `.showcase-venv\Scripts\python.exe`.

Unit tests mock synthesis and render operations. Browser regressions run real Chrome at 1080p and 720p. Use the installed CLI's `preflight` command for real speech synthesis and a short render. A passed test is not a human listening review.

## Keep these contracts

- New projects begin with a neutral outline and unverified facts. The agent fills them from real project evidence.
- `kind` describes content; `layout` controls presentation. Preview, deck, and video share the renderer.
- Four current previews and an explicit revision selection precede production. Source changes invalidate the affected selection or production checks.
- Design-mode output edits must return to the source model or variant. Never bypass the selected style by editing generated CSS.
- Unchanged speech uses the audio cache. Manual work is preserved before regeneration.

For the input model and commands, see the skill's [data contract](../skills/project-showcase/references/data-contract.md), [design workflow](../skills/project-showcase/references/design.md), and [quality gates](../skills/project-showcase/references/quality.md).
