#!/usr/bin/env python3
"""Conservative PU2PNY CI change classifier.

ARM64 may be skipped only when every changed path is documentation. Unknown or
mixed paths always require the normal build path.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def git_changed(base,head):
    p=subprocess.run(['git','diff','--name-only',f'{base}...{head}'],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:
        raise SystemExit(p.stderr or 'git diff failed')
    return [x.strip() for x in p.stdout.splitlines() if x.strip()]

def is_documentation(path):
    p=path.replace('\\','/')
    name=Path(p).name.lower()
    return p.startswith('docs/') or (('/' not in p) and (name.endswith('.md') or name.startswith('readme') or name.startswith('changelog')))

def classify(paths):
    docs_only=bool(paths) and all(is_documentation(p) for p in paths)
    result={
        'changed_count':len(paths),
        'docs_only':docs_only,
        'arm64_required':not docs_only,
        'i18n_required':any(p.startswith('src/') and (p.endswith('.html') or 'ui-language' in p or 'ui-common' in p) for p in paths),
        'paths':paths,
    }
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--head',default='HEAD');ap.add_argument('--github-output')
    args=ap.parse_args();result=classify(git_changed(args.base,args.head))
    print(json.dumps(result,ensure_ascii=False))
    output=args.github_output or os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output,'a',encoding='utf-8') as f:
            for key in ('docs_only','arm64_required','i18n_required'):
                f.write(f"{key}={'true' if result[key] else 'false'}\n")
            f.write(f"changed_count={result['changed_count']}\n")
    return 0
if __name__=='__main__':raise SystemExit(main())
