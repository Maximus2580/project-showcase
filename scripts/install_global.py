#!/usr/bin/env python3
"""Install Project Showcase for this user; existing installs require --replace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import venv

SOURCE = Path(__file__).resolve().parents[1] / '.claude/skills/project-showcase'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace',action='store_true',help='Back up and replace an existing skill/launcher')
    args=parser.parse_args()
    if sys.version_info < (3,10):raise SystemExit('Python 3.10+ required; Python 3.12 recommended.')
    npm=shutil.which('npm')
    if not npm:raise SystemExit('Install Node 22+ (including npm) first.')
    home=Path.home();dest=home/'.agents/skills/project-showcase';alias=home/'.claude/skills/project-showcase'
    runtime=home/'.local/share/project-showcase';launcher=home/'.local/bin'/('project-showcase.cmd' if os.name=='nt' else 'project-showcase')
    occupied=[p for p in (dest,alias,launcher) if p.exists() or p.is_symlink()]
    if occupied and not args.replace:raise SystemExit('Existing install preserved. Use --replace to back it up: '+', '.join(map(str,occupied)))
    if SOURCE.resolve()==dest.resolve():raise SystemExit('Run this installer from a separate repository checkout.')
    runtime.mkdir(parents=True,exist_ok=True)
    if occupied:
        backup=runtime/'backups'/str(time.time_ns());backup.mkdir(parents=True)
        for i,p in enumerate(occupied):shutil.move(str(p),str(backup/f'{i}-{p.name}'))
        print('Backup:',backup,flush=True)
    excluded=shutil.ignore_patterns('node_modules','__pycache__','.venv','.showcase-venv','*.pyc','.DS_Store')
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(SOURCE,dest,ignore=excluded)
    env=runtime/'venv';venv.EnvBuilder(with_pip=True).create(env)
    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    subprocess.run([str(python),'-m','pip','install','-r',str(dest/'requirements.txt')],check=True)
    npm_args=[npm,'ci','--prefix',str(dest),'--no-audit','--no-fund']
    if os.name=='nt':
        npm_cli=Path(npm).resolve().parent/'node_modules/npm/bin/npm-cli.js'
        node=shutil.which('node')
        if not node or not npm_cli.is_file():raise SystemExit('Cannot locate npm-cli.js beside npm.cmd. Install the standard Node distribution.')
        subprocess.run([node,str(npm_cli),*npm_args[1:]],check=True)
    else:subprocess.run(npm_args,check=True)
    launcher.parent.mkdir(parents=True,exist_ok=True)
    script=dest/'scripts/showcase.py'
    if os.name=='nt':
        launcher.write_text('@echo off\r\n"'+str(python).replace('%','%%')+'" "'+str(script).replace('%','%%')+'" %*\r\n')
    else:
        launcher.write_text('#!/bin/sh\nexec '+shlex.quote(str(python))+' '+shlex.quote(str(script))+' "$@"\n');launcher.chmod(0o755)
    note=f'\n## Prepared global runtime\n\nUse `{launcher} --out <output-folder> <command>`. Python: `{python}`. Skill files: `{dest}`. Dependencies are installed. Keep outputs inside the working project, not the global skill folder.\n'
    p=dest/'SKILL.md';p.write_text(p.read_text(encoding='utf-8')+note,encoding='utf-8')
    alias.parent.mkdir(parents=True,exist_ok=True)
    try:alias.symlink_to(dest,target_is_directory=True)
    except OSError:
        if os.name!='nt':raise
        shutil.copytree(dest,alias,ignore=excluded)
        print('Claude skill copied; use the prepared global runtime above.')
    manifest={'version':json.loads((dest/'package.json').read_text())['version'],'installed_at':time.time(),'canonical':str(dest),'claude_alias':str(alias),'runtime':str(runtime),'cli':str(launcher),'files':{p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file() and not {'node_modules','__pycache__'}&set(p.relative_to(dest).parts)}}
    (runtime/'install-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Installed:',dest)
    print('Claude Code: /project-showcase; Codex: use the project-showcase skill in a new turn.')
    print('Test:',str(launcher),'--out showcase-output/preflight preflight')
    if str(launcher.parent) not in os.environ.get('PATH','').split(os.pathsep):print('Add this directory to PATH, or use the full command path:',launcher.parent)

if __name__=='__main__':main()
