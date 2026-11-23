"""Start a dated development note; never invent experimental results."""
import argparse
from datetime import datetime,timedelta,timezone
from pathlib import Path
import re


def create_note(root,title):
    folder=Path(root)/'LAB_NOTES';folder.mkdir(exist_ok=True)
    date=datetime.now(timezone(timedelta(hours=7))).strftime('%Y%m%d')
    indices=[]
    for p in folder.glob(f'LN-{date}-*.md'):
        match=re.match(r'LN-\d{8}-(\d{3})_',p.name)
        if match:indices.append(int(match.group(1)))
    slug=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')[:60] or 'change'
    note_id=f'LN-{date}-{max(indices,default=0)+1:03d}'
    path=folder/f'{note_id}_{slug}.md'
    template=(folder/'TEMPLATE.md').read_text(encoding='utf-8')
    content=template.replace('{{ID}}',note_id).replace('{{TITLE}}',title).replace('{{DATE}}',date[:4]+'-'+date[4:6]+'-'+date[6:])
    with path.open('x',encoding='utf-8') as stream:stream.write(content)
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('title')
    args=parser.parse_args();print(create_note(Path(__file__).resolve().parents[1],args.title))
