from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import parse_bank,export_bank,load_project_bank
raw={q['id']:q for q in json.loads((ROOT/'data/raw_questions.json').read_text())}
key=json.loads((ROOT/'data/official_keys/2022-june.json').read_text())
papers={p['id'] for p in json.loads((ROOT/'data/papers.json').read_text())}
for name in ['2022-june-q034-090.json','2022-june-q091-120.json']:
 path=ROOT/'data/completed_papers'/name
 data=json.loads(path.read_text())
 for q in data['questions']:
  source=raw[q['id']];qid=source['question_id'];official=key['question_id_answers'][qid]
  base=f'Independent mathematical derivation; question {q["question_number"]}, PDF page {source["page"]}. No candidate response used as an answer key.'
  if not official:
   compare=' Compared after derivation with the NTA final key, exact source question ID '+qid+': officially dropped; see full source diagnosis.'
  elif set(official)==set(q['correct_options']):
   compare=' Compared after derivation with the NTA final key, exact source question ID '+qid+' and recovered option IDs: agrees ('+', '.join(official)+').'
  else:
   compare=' Compared after derivation with the NTA final key, exact source question ID '+qid+' and recovered option IDs: official labels '+', '.join(official)+' differ from the independently derived labels; the worked solution and source note explain the discrepancy.'
  q['answer_source']=base+compare
  if q['question_number']==93:
   q['source_note']='Exact-ID official final key selects B,C, corresponding to forward solutions x>=0. Source does not state this restriction. On a two-sided neighborhood both IVPs have multiple C1 solutions, labels C,D; explicit backward branch and forward uniqueness proof are included.'
   q['solution']=q['solution'].replace('Under that extra convention the intended labels become B,C.','Under that extra convention the intended labels become B,C, which are exactly the official final-key labels for source question414.')
  if q['question_number']==83:
   q['solution']=q['solution'].replace(' The stated answer list is updated below to retain both universally true statements.','')
  assert len(q['theory'].split())>=100,(q['id'],'theory')
  assert len(q['hints'])>=2 and len(q['similar_questions'])==2,q['id']
  def verify(v):
   if isinstance(v,str): assert not any(ord(c)<32 and c not in '\n\t' for c in v),(q['id'],repr(v))
   elif isinstance(v,dict):
    for x in v.values():verify(x)
   elif isinstance(v,list):
    for x in v:verify(x)
  verify(q)
 parsed=parse_bank(data,papers)
 temp=path.with_suffix('.tmp');temp.write_text(export_bank(parsed));temp.replace(path)
 print(name,len(parsed),'validated',[(q.question_number,q.correct_options) for q in parsed if q.review_status=='source_issue'])
bank=load_project_bank(ROOT,False)
qs=[q for q in bank if q.paper_id=='2022-june']
print('Whole 2022 paper',len(qs),'pending',[(q.question_number) for q in qs if q.review_status=='pending'])
