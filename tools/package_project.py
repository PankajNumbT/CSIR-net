"""Package a consistent snapshot of the project, with optional original assets."""
import argparse,hashlib,json,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import coverage,overlay_solutions,parse_bank,source_questions

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-only',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    skip={'.git','__pycache__','.venv','venv','ai_drafts','ocr'}
    files={}
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(p in skip for p in rel.parts):continue
        if path.suffix in ('.pyc','.tmp','.zip') or path.name in ('.env','secrets.toml','generation_failures.json'):continue
        if args.source_only and (rel.parts[0]=='papers' or rel.parts[:2]==('assets','questions')):continue
        files[str(rel)]=path.read_bytes()
    papers=json.loads(files['data/papers.json'])
    raw=json.loads(files['data/raw_questions.json'])
    ids={p['id'] for p in papers}
    bank=source_questions(raw)
    for name,data in files.items():
        if name=='data/exam_questions.json' or name.startswith('data/completed_papers/') and name.endswith('.json'):
            bank=overlay_solutions(bank,parse_bank(json.loads(data),ids))
    counts=Counter(q.review_status for q in bank)
    report={'source_questions':len(bank),'solved':counts['reviewed'],
            'source_issues_explained':counts['source_issue'],'pending':counts['pending'],
            'unclassified':sum(q.topic=='Unclassified' for q in bank),
            'missing_from_attachments':20,'papers':coverage(bank,papers)}
    files['data/coverage_report.json']=(json.dumps(report,indent=2)+'\n').encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in files.items():archive.writestr('net_studio/'+name,data)
    with zipfile.ZipFile(args.output) as archive:
        bad=archive.testzip()
        if bad:raise SystemExit('Archive verification failed: '+bad)
    print(json.dumps({'output':str(args.output.resolve()),'files':len(files),
                     'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
                     'content':{k:v for k,v in report.items() if k!='papers'}},indent=2))

if __name__=='__main__':main()
