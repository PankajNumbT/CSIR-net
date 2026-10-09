"""Write independent source-grounded packs without editing another worker's files."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import parse_bank,export_bank
RAW={q['id']:q for q in json.loads((ROOT/'data/raw_questions.json').read_text())}
PAPER_IDS={p['id'] for p in json.loads((ROOT/'data/papers.json').read_text())}
class Writer:
 def __init__(self,paper_id,suffix=''):
  self.pid=paper_id;self.path=ROOT/'data/completed_papers'/f'{paper_id}{suffix}.json'
  self.packs=json.loads(self.path.read_text())['questions'] if self.path.exists() else []
 def add(self,n,track,topic,difficulty,prompt,options,correct,hints,solution,theory,examples,status='reviewed',note=''):
  qid=f'{self.pid}-q{n:03d}';src=RAW[qid]
  opts=dict(zip('ABCD',options)) if isinstance(options,list) else options
  pack={'id':qid,'source_type':'official_exam','paper_id':self.pid,'question_number':n,'part':src['part'],
   'track':track,'topic':topic,'difficulty':difficulty,'prompt':prompt,'options':opts,
   'correct_options':list(correct),'hints':hints,'solution':solution,'theory':theory,
   'similar_questions':[{'prompt':p,'solution':s} for p,s in examples],
   'review_status':status,'source_note':note or 'Original attached paper; independently transcribed and mathematically worked.',
   'answer_source':f'Independent mathematical derivation; question {n}, PDF page {src["page"]}. No candidate response used as an answer key.',
   'page':src['page'],'image':src['image'],'classification_status':'reviewed'}
  self.packs=[q for q in self.packs if q['id']!=qid]+[pack]
  self.save()
 def save(self):
  parsed=parse_bank({'schema_version':1,'questions':sorted(self.packs,key=lambda q:q['question_number'])},PAPER_IDS)
  encoded=export_bank(parsed).encode();tmp=self.path.with_suffix('.tmp');tmp.write_bytes(encoded);tmp.replace(self.path)
