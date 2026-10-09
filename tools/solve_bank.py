"""Explicit, resumable bulk generation. API calls incur account usage charges."""
from pathlib import Path
import argparse,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import BankError
from solver import generate_pack,save_draft

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--paper',help='Limit to this paper ID')
 parser.add_argument('--limit',type=int,default=1,help='Maximum new packs, default 1')
 parser.add_argument('--all',action='store_true',help='Generate every pending question; incurs API usage for all of them')
 args=parser.parse_args()
 if not os.getenv('OPENAI_API_KEY'):parser.error('OPENAI_API_KEY is not configured.')
 if args.limit<1:parser.error('--limit must be positive.')
 raw=json.loads((ROOT/'data/raw_questions.json').read_text())
 curated=json.loads((ROOT/'data/exam_questions.json').read_text())['questions']
 done={q['id'] for q in curated}
 for file in (ROOT/'data/ai_drafts').glob('*.json'):
  done.update(q['id'] for q in json.loads(file.read_text())['questions'])
 eligible=[q for q in raw if q['id'] not in done and (not args.paper or q['paper_id']==args.paper)]
 flagged=[q for q in eligible if q.get('source_issue')]
 todo=[q for q in eligible if not q.get('source_issue')]
 if not args.all:todo=todo[:args.limit]
 print(f'Generating {len(todo)} new draft packs. Model: {os.getenv("OPENAI_MODEL","gpt-5.2")}. Drafts are not graded.',flush=True)
 success=0;failures=[{'id':q['id'],'error':q['source_issue']} for q in flagged]
 try:
  for i,q in enumerate(todo,1):
   try:
    save_draft(generate_pack(q,ROOT),ROOT);success+=1
    print(f'{i}/{len(todo)} saved {q["id"]}',flush=True)
   except (BankError,RuntimeError,OSError,ValueError) as exc:
    failures.append({'id':q['id'],'error':str(exc)})
    print(f'{i}/{len(todo)} pending {q["id"]}: {exc}',flush=True)
    if 'HTTP 401' in str(exc) or 'HTTP 403' in str(exc) or 'HTTP 429' in str(exc):break
 finally:
  (ROOT/'data/generation_failures.json').write_text(json.dumps(failures,indent=2))
 print(f'Saved {success} draft packs; {len(failures)} failed/ambiguous. Re-run to resume.',flush=True)
if __name__=='__main__':main()
