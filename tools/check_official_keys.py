"""Compare completed answers to exact question IDs in retrieved official keys."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import load_project_bank
raw={q['id']:q for q in json.loads((ROOT/'data/raw_questions.json').read_text())}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--require-consistent',action='store_true',help='Fail if a scored answer disagrees with an exact-ID official key')
args=parser.parse_args()
questions=load_project_bank(ROOT,False)
mismatches=[]
for file in sorted((ROOT/'data/official_keys').glob('*.json')):
    key=json.loads(file.read_text());matched=0
    print(key['paper_id'],key['source_url'])
    for q in questions:
        if q.paper_id!=key['paper_id'] or q.review_status=='pending':continue
        qid=raw[q.id].get('question_id')
        answer=key['question_id_answers'].get(qid)
        if answer is None:
            print('NO EXACT ID',q.id,qid);continue
        if q.review_status=='source_issue':
            print('EXPLAINED SOURCE ISSUE',q.id,'official key:',','.join(answer) if answer else 'Dropped');continue
        if set(answer)!=set(q.correct_options):
            print('MISMATCH',q.id,'derived:',','.join(q.correct_options),'official:',','.join(answer))
            mismatches.append(q.id)
        else:matched+=1
    print('Matched completed answer sets:',matched)
if args.require_consistent and mismatches:
    raise SystemExit(f'{len(mismatches)} unexplained official-key discrepancies: '+', '.join(mismatches))
