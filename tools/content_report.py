"""Validate and summarize all currently completed source learning packs."""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import coverage, export_bank, load_project_bank

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true',help='Refresh the checked coverage report.')
    parser.add_argument('--require-complete',action='store_true',help='Fail if any available question lacks a learning pack.')
    parser.add_argument('--export',type=Path,help='Export completed packs as one portable bank.')
    args=parser.parse_args()
    questions=load_project_bank(ROOT,include_drafts=False)
    papers=json.loads((ROOT/'data/papers.json').read_text())
    counts=Counter(q.review_status for q in questions)
    rows=coverage(questions,papers)
    report={'source_questions':len(questions),'solved':counts['reviewed'],
            'source_issues_explained':counts['source_issue'],'pending':counts['pending'],
            'unclassified':sum(q.topic=='Unclassified' for q in questions),
            'missing_from_attachments':sum(r['missing'] for r in rows),'papers':rows}
    if args.write:
        path=ROOT/'data/coverage_report.json';tmp=path.with_suffix('.tmp')
        tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
    if args.export:
        args.export.write_text(export_bank([q for q in questions if q.review_status!='pending']))
    print(json.dumps({k:v for k,v in report.items() if k!='papers'},indent=2))
    if args.require_complete and counts['pending']:
        raise SystemExit('Not complete: available source questions still lack learning packs.')

if __name__=='__main__':main()
