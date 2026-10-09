import json,hashlib,sys,unittest
from pathlib import Path
from dataclasses import replace,asdict
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import *
from solver import request_payload,unpack_response,to_question,generate_pack,save_draft
PAPERS=json.loads((ROOT/'data/papers.json').read_text());IDS={p['id'] for p in PAPERS}
RAW=json.loads((ROOT/'data/raw_questions.json').read_text())
SOLVED=read_bank(ROOT/'data/exam_questions.json',IDS)
BANK=load_project_bank(ROOT)
BY_ID={q.id:q for q in BANK}

class ScoringTests(unittest.TestCase):
 def test_single_correct_and_penalty(self):
  q=BY_ID['2020-june-26nov-q030']
  self.assertEqual(grade(q,['D'])['points'],3)
  self.assertEqual(grade(q,['A'])['points'],-.75)
 def test_aptitude_mark_and_penalty(self):
  q=BY_ID['2020-june-26nov-q003']
  self.assertEqual(grade(q,['C'])['points'],2)
  self.assertEqual(grade(q,['A'])['points'],-.5)
 def test_multiple_requires_complete_set(self):
  q=BY_ID['2020-june-26nov-q061']
  self.assertEqual(grade(q,['B','C'])['points'],4.75)
  for choices in [['B'],['C'],['B','C','D']]:
   self.assertEqual(grade(q,choices)['points'],0)
   self.assertFalse(grade(q,choices)['correct'])
 def test_invalid_single_and_empty(self):
  for choices in [[],['A','B'],['X']]:
   with self.assertRaises(BankError):grade(BY_ID['2020-june-26nov-q003'],choices)
 def test_unreviewed_never_graded(self):
  q=replace(SOLVED[0],review_status='pending',correct_options=[])
  with self.assertRaises(BankError):grade(q,['A'])
  with self.assertRaises(BankError):grade(replace(SOLVED[0],review_status='draft'),['C'])
 def test_progress_ignores_forged_points(self):
  q=SOLVED[0]
  x=validate_progress({'schema_version':1,'bookmarks':[q.id,'unknown'],
    'responses':{q.id:{'selected':['A'],'submitted':True,'points':999},'unknown':{'selected':['A']}}},set(BY_ID))
  self.assertEqual(x['bookmarks'],[q.id]);self.assertNotIn('points',x['responses'][q.id])
  self.assertEqual(grade(q,x['responses'][q.id]['selected'])['points'],-.5)

class InventoryTests(unittest.TestCase):
 def test_exact_source_coverage(self):
  self.assertEqual(len(RAW),1420);self.assertEqual(len(BANK),1420)
  self.assertEqual(len({q['id'] for q in RAW}),1420)
  for p in PAPERS:
   expected=set(range(21,121)) if p['id']=='2021-june' else set(range(1,121))
   self.assertEqual({q['question_number'] for q in RAW if q['paper_id']==p['id']},expected)
 def test_solution_coverage_separate_from_source_coverage(self):
  rows=coverage(BANK,PAPERS)
  self.assertEqual(sum(x['available'] for x in rows),1420)
  counts=Counter(q.review_status for q in BANK)
  self.assertEqual(sum(x['ready'] for x in rows),counts['reviewed'])
  self.assertEqual(sum(x['pending'] for x in rows),counts['pending'])
  self.assertEqual(sum(x['explained_issues'] for x in rows),counts['source_issue'])
  self.assertEqual(sum(counts.values()),1420)
  self.assertEqual(sum(x['missing'] for x in rows),20)
  self.assertEqual({q.paper_id for q in SOLVED},IDS)
 def test_every_image_decodes(self):
  from PIL import Image
  for q in RAW:
   with self.subTest(q=q['id']):
    path=ROOT/q['image'];self.assertTrue(path.is_file())
    with Image.open(path) as im:
     self.assertGreater(im.width,180);self.assertGreater(im.height,25);im.verify()
 def test_original_pdf_hashes(self):
  reports=json.loads((ROOT/'data/extraction_report.json').read_text())
  for row in reports:
   data=(ROOT/'papers'/f'{row["paper_id"]}.pdf').read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
 def test_labels_and_parts(self):
  for q in BANK:
   self.assertEqual(q.part,'A' if q.question_number<=20 else 'B' if q.question_number<=60 else 'C')
   self.assertEqual(q.answer_type,'Multiple correct' if q.part=='C' else 'Single correct')
 def test_pending_has_no_inferred_candidate_answer(self):
  for q in source_questions(RAW):
   self.assertEqual(q.correct_options,[]);self.assertEqual(q.review_status,'pending')
 def test_all_questions_accessible_by_tracks(self):
  math=filter_questions(BANK,'Mathematics');stats=filter_questions(BANK,'Statistics')
  self.assertEqual({q.id for q in math+stats},set(BY_ID))
  for q in BANK:
   if q.track=='Shared':self.assertIn(q,math);self.assertIn(q,stats)
 def test_shuffle_reproducible_without_mutation(self):
  original=list(BANK)
  self.assertEqual(shuffled_ids(BANK,1234),shuffled_ids(BANK,1234))
  self.assertEqual(set(shuffled_ids(BANK,7)),set(BY_ID));self.assertEqual(BANK,original)

class ImportTests(unittest.TestCase):
 def test_source_issue_explanation_remains_ungraded(self):
  q=replace(SOLVED[0],review_status='source_issue',correct_options=[])
  checked=validate_question(asdict(q),IDS)
  with self.assertRaises(BankError):grade(checked,['A'])
 def test_complete_pack_round_trip(self):
  self.assertEqual(parse_bank(json.loads(export_bank(SOLVED)),IDS),SOLVED)
 def test_duplicate_sources_rejected(self):
  a=asdict(SOLVED[0]);b=dict(a,id='other-id')
  with self.assertRaises(BankError):parse_bank({'schema_version':1,'questions':[a,b]},IDS)
 def test_bad_part_rejected(self):
  q=asdict(SOLVED[0]);q['part']='C'
  with self.assertRaises(BankError):validate_question(q,IDS)
 def test_missing_theory_rejected(self):
  q=asdict(SOLVED[0]);q['theory']=''
  with self.assertRaises(BankError):validate_question(q,IDS)
 def test_solution_provenance_must_match(self):
  with self.assertRaises(BankError):overlay_solutions(BANK,[replace(SOLVED[0],question_number=4)])
 def test_cached_draft_cannot_replace_reviewed(self):
  self.assertEqual(overlay_solutions([SOLVED[0]],[replace(SOLVED[0],review_status='draft')]),[SOLVED[0]])

class SolverTests(unittest.TestCase):
 def result(self):
  q=asdict(SOLVED[0]);fields=('track','topic','difficulty','prompt','options','correct_options','hints','solution','theory','similar_questions')
  return {k:q[k] for k in fields}|{'status':'solved','issue':''}
 def test_payload_private_image_grounding(self):
  x=request_payload(RAW[0],b'fakeimage','gpt-5.2')
  self.assertFalse(x['store']);self.assertTrue(x['text']['format']['strict'])
  self.assertEqual(x['input'][0]['content'][1]['detail'],'high')
  self.assertIn('not an answer key',x['input'][0]['content'][0]['text'])
 def test_response_to_draft_only(self):
  src=next(q for q in RAW if q['id']==SOLVED[0].id)
  q=to_question(src,self.result(),'gpt-5.2',ROOT)
  self.assertEqual(q['review_status'],'draft')
  self.assertIn('no official answer-key verification',q['answer_source'])
 def test_ambiguous_does_not_make_pack(self):
  result=self.result();result.update(status='ambiguous',issue='Multiple valid single-choice answers')
  with self.assertRaises(BankError):to_question(RAW[0],result,'gpt-5.2',ROOT)
 def test_incomplete_response_rejected(self):
  with self.assertRaises(RuntimeError):unpack_response({'status':'incomplete','output':[]})
 def test_refusal_rejected(self):
  with self.assertRaises(RuntimeError):unpack_response({'status':'completed','output':[{'content':[{'type':'refusal','refusal':'x'}]}]})
 def test_structured_response(self):
  result=self.result()
  wrapped={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}
  self.assertEqual(unpack_response(wrapped),result)
 def test_no_key_no_network(self):
  with patch.dict('os.environ',{},clear=True),patch('urllib.request.urlopen') as network:
   with self.assertRaises(RuntimeError):generate_pack(RAW[0],ROOT)
   network.assert_not_called()
 def test_flagged_source_never_sent(self):
  flagged=next(q for q in RAW if q.get('source_issue'))
  with patch.dict('os.environ',{'OPENAI_API_KEY':'test-placeholder'},clear=True),patch('urllib.request.urlopen') as network:
   with self.assertRaises(BankError):generate_pack(flagged,ROOT)
   network.assert_not_called()
 def test_reviewed_pack_not_written_as_draft(self):
  with self.assertRaises(BankError):save_draft(asdict(SOLVED[0]),ROOT)

class DerivationChecks(unittest.TestCase):
 def test_matrix_power_independent_calculation(self):
  def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
  a=[[3,-2],[2,-1]];power=[[1,0],[0,1]]
  for _ in range(20):power=multiply(power,a)
  self.assertEqual(power,[[41,-40],[40,-39]])
 def test_finite_binomial_mle(self):
  from fractions import Fraction
  from math import comb
  grid=[(n,p) for n in [5,6] for p in [Fraction(1,4),Fraction(3,4)]]
  best=max(grid,key=lambda z:comb(z[0],3)*z[1]**3*(1-z[1])**(z[0]-3))
  self.assertEqual(best,(5,Fraction(3,4)))
 def test_poisson_collision_by_enumeration(self):
  from itertools import product
  hits=list(product(range(9),repeat=3))
  collisions=sum(len(set(x))<3 for x in hits)
  from fractions import Fraction
  self.assertEqual(Fraction(collisions,len(hits)),Fraction(25,81))
if __name__=='__main__':unittest.main()
