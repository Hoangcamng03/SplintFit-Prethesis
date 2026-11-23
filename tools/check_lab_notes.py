"""Check staged/committed lab-note presence, not the truth of scientific claims."""
import argparse,re,subprocess,sys
from pathlib import Path

SECTIONS=('Objective','Changes','Validation','Limitations','Next')
NOTE_NAME=re.compile(r'^LAB_NOTES/LN-\d{8}-\d{3}_.+\.md$')
ROOT=Path(__file__).resolve().parents[1]


def validate_changes(changed,read):
    if not changed:return []
    notes=[p for p in changed if NOTE_NAME.fullmatch(p)]
    if not notes:return ['Thay đổi cần một lab note LN-YYYYMMDD-NNN_*.md được thêm/cập nhật trong cùng commit.']
    errors=[]
    for path in notes:
        content=read(path)
        if not re.search(r'^status:\s*complete\s*$',content,re.M):errors.append(path+': note còn draft hoặc thiếu status: complete.')
        for section in SECTIONS:
            if not re.search(r'^## '+section+r'\b',content,re.M):errors.append(path+': thiếu mục '+section)
    return errors


def git(*args):
    return subprocess.check_output(['git',*args],text=True,encoding='utf-8',cwd=ROOT)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true')
    parser.add_argument('--base');parser.add_argument('--head',default='HEAD')
    args=parser.parse_args()
    if args.staged:
        changed=git('diff','--cached','--name-only','--diff-filter=ACMRD','-z').split('\0')
        read=lambda path:git('show',':'+path)
    else:
        # No external ref text is executed as shell code.
        if not re.fullmatch(r'[A-Za-z0-9_./~-]+',args.head):parser.error('Invalid head ref')
        base=args.base
        if base and not re.fullmatch(r'[A-Za-z0-9_./~-]+',base):parser.error('Invalid base ref')
        if base and set(base)!={'0'}:
            changed=git('diff','--name-only','--diff-filter=ACMRD','-z',base,args.head).split('\0')
        else:changed=git('ls-tree','-r','--name-only','-z',args.head).split('\0')
        read=lambda path:git('show',args.head+':'+path)
    errors=validate_changes([p for p in changed if p],read)
    for e in errors:print(e,file=sys.stderr)
    if errors:return 1
    print('Lab note check passed (presence and format only).');return 0


if __name__=='__main__':raise SystemExit(main())
