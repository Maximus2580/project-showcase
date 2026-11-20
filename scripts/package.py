"""Package v2 source and a source-matched example; never infer approval from file existence."""
import argparse, hashlib, json, shutil, sys, tempfile, zipfile
from argparse import Namespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'.claude/skills/project-showcase'
sys.path.insert(0,str(SKILL/'scripts'))
import showcase

def package(example, dest, draft):
    dest.mkdir(parents=True,exist_ok=True)
    # Gate the example first: failed or stale sources must not produce a new release.
    validated=showcase.export_bundle(Namespace(out=example.resolve(),draft=draft))
    validation=ROOT/'docs/VALIDATION-V2.md'
    if not validation.is_file():raise ValueError('Write the current v2 validation report before packaging.')
    excluded={'node_modules','__pycache__','.venv','.showcase-venv','.DS_Store'}
    files={p.relative_to(ROOT).as_posix():p for p in sorted(SKILL.rglob('*')) if p.is_file() and not set(p.relative_to(SKILL).parts)&excluded}
    files.update({'LICENSE':ROOT/'LICENSE','START-HERE.md':ROOT/'docs/STUDENT-START.md','VALIDATION-V2.md':validation,'INSTRUCTOR-CHECKLIST.md':ROOT/'docs/INSTRUCTOR-CHECKLIST.md','REVIEW-V2.md':ROOT/'docs/REVIEW-V2.md'})
    contents={name:p.read_bytes() for name,p in files.items()}
    # This guide moves from docs/ to ZIP root; preserve its relative setup link.
    contents['INSTRUCTOR-CHECKLIST.md']=contents['INSTRUCTOR-CHECKLIST.md'].replace(b'(../.claude/',b'(.claude/')
    manifest={'name':'project-showcase','version':'2.1.0','files':{name:hashlib.sha256(data).hexdigest() for name,data in contents.items()},'example_signature':showcase.build_signature(example),'status':'검수 대기' if draft else '청취 확인'}
    target=dest/'project-showcase-v2-student.zip';tmp=target.with_suffix('.tmp')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in contents.items():z.writestr(name,data)
        z.writestr('PACKAGE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    tmp.replace(target)
    target_example=dest/'project-showcase-v2-example.zip'
    shutil.copy2(validated,target_example.with_suffix('.tmp'));target_example.with_suffix('.tmp').replace(target_example)
    # Use a fresh extraction directory so no stale files enter the reviewable preview.
    preview=dest/'project-showcase-example'
    with tempfile.TemporaryDirectory(dir=dest) as work:
        with zipfile.ZipFile(target_example) as z:z.extractall(work)
        if preview.exists():shutil.rmtree(preview)
        shutil.move(work,preview)
    results={p.name:{'bytes':p.stat().st_size,'sha256':showcase.filehash(p)} for p in (target,target_example)}
    showcase.write(dest/'manifest-project-showcase.json',results)
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--example',type=Path,default=ROOT/'showcase-output/project-showcase-example')
    p.add_argument('--dest',type=Path,default=ROOT/'artifacts')
    p.add_argument('--draft',action='store_true',help='Preserve pending listening status; not release approval')
    a=p.parse_args();package(a.example.resolve(),a.dest.resolve(),a.draft)
