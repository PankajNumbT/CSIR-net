"""Optional image-grounded learning packs via the OpenAI Responses API.

This module never promotes a model response to reviewed status. No API request is
made at import/startup. Keys are read only from the server environment.
"""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from core import BankError,TRACK_TOPICS,validate_question

FIELDS={
 'status':{'type':'string','enum':['solved','unreadable','ambiguous']},
 'issue':{'type':'string'},
 'track':{'type':'string','enum':['Mathematics','Statistics','Shared']},
 'topic':{'type':'string','enum':sorted(set(sum(TRACK_TOPICS.values(),[])))},
 'difficulty':{'type':'string','enum':['Easy','Moderate','Hard']},
 'prompt':{'type':'string'},
 'options':{'type':'object','properties':{x:{'type':'string'} for x in 'ABCD'},'required':list('ABCD'),'additionalProperties':False},
 'correct_options':{'type':'array','items':{'type':'string','enum':list('ABCD')}},
 'hints':{'type':'array','items':{'type':'string'}},
 'solution':{'type':'string'},
 'theory':{'type':'string'},
 'similar_questions':{'type':'array','items':{'type':'object','properties':{'prompt':{'type':'string'},'solution':{'type':'string'}},'required':['prompt','solution'],'additionalProperties':False}},
}
SCHEMA={'type':'object','properties':FIELDS,'required':list(FIELDS),'additionalProperties':False}

def request_payload(raw:dict,image_bytes:bytes,model:str)->dict:
    instruction=f'''Prepare a careful CSIR NET Mathematical Sciences learning pack for ONLY the source question {raw['question_number']} (Part {raw['part']}) in this image.
The image may show Hindi repetition, page furniture, candidate Chosen Option, or metadata. Those are not an answer key. Use the English question as authority. Transcribe all mathematical assumptions and all four choices exactly, preserving their order; A,B,C,D map to 1,2,3,4 or a,b,c,d. Do not silently repair a misprint or missing assumption.
Part A/B is single correct, Part C multiple correct, including when only one option happens to be true. If the image is incomplete/unreadable, or a single-correct problem has multiple valid choices, return status unreadable/ambiguous with an issue, no correct_options, and no invented solution. Never infer answers from candidate selections.
For a solvable question: choose its primary track and topic from the schema (Part A must be Shared/Aptitude). Give 2–4 progressive hints without revealing the answer in the first hint; a complete public worked mathematical solution, checking every option; substantial theory explaining definitions, theorem hypotheses, why the method works, common errors, and when it fails; and TWO different fully worked similar questions, one near transfer and one extension. Use Markdown and LaTeX $...$ / $$...$$. Do not give generic theory unrelated to the exact question. Verify calculations and counterexamples. Difficulty is an editorial estimate. No invented official citations. Return status solved only if the source question is unambiguous and the mathematical result is supported by your derivation.'''
    return {'model':model,'store':False,'reasoning':{'effort':'high'},'max_output_tokens':14000,
            'input':[{'role':'user','content':[{'type':'input_text','text':instruction},
                    {'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(image_bytes).decode(),'detail':'high'}]}],
            'text':{'format':{'type':'json_schema','name':'learning_pack','strict':True,'schema':SCHEMA}}}

def unpack_response(response:dict)->dict:
    if response.get('status')!='completed':
        raise RuntimeError('Generation did not complete. No learning pack was saved; try again with a suitable output limit.')
    texts=[]
    for message in response.get('output',[]):
        for item in message.get('content',[]):
            if item.get('type')=='refusal':raise RuntimeError('The service declined this request. No learning pack was saved.')
            if item.get('type')=='output_text':texts.append(item['text'])
    if not texts:raise RuntimeError('The service returned no learning pack.')
    try:result=json.loads(''.join(texts))
    except (ValueError,TypeError) as exc:raise RuntimeError('The returned learning pack was not valid JSON.') from exc
    if not isinstance(result,dict) or set(result)!=set(FIELDS):raise RuntimeError('The returned learning pack has an unexpected schema.')
    return result

def to_question(raw:dict,result:dict,model:str,root:Path)->dict:
    if result['status']!='solved':
        raise BankError('Source question requires checking: '+result.get('issue','unreadable or ambiguous source'))
    q={k:result[k] for k in ('track','topic','difficulty','prompt','options','correct_options','hints','solution','theory','similar_questions')}
    q.update(id=raw['id'],source_type='official_exam',paper_id=raw['paper_id'],question_number=raw['question_number'],part=raw['part'],
             review_status='draft',source_note='AI transcription and explanation; compare with the original image.',
             answer_source=f'AI-generated independent derivation ({model}); no official answer-key verification.',
             page=raw['page'],image=raw['image'],classification_status='draft')
    ids={p['id'] for p in json.loads((root/'data/papers.json').read_text())}
    validate_question(q,ids)
    if len(q['similar_questions'])<2:raise BankError('Generation must provide two worked transfer examples.')
    return q

def generate_pack(raw:dict,root:Path)->dict:
    if raw.get('source_issue'):
        raise BankError('This source question needs checking before generation: '+raw['source_issue'])
    key=os.getenv('OPENAI_API_KEY')
    if not key:raise RuntimeError('Set OPENAI_API_KEY on the server to enable draft generation.')
    model=os.getenv('OPENAI_MODEL','gpt-5.2')
    img=(root/raw['image']).resolve()
    if not img.is_relative_to((root/'assets/questions').resolve()):raise BankError('Invalid question image path.')
    payload=request_payload(raw,img.read_bytes(),model)
    request=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode(),
                                   headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=300) as response:result=json.load(response)
    except urllib.error.HTTPError as exc:
        # Deliberately avoid copying arbitrary response bodies or credentials into logs/UI.
        raise RuntimeError(f'Explanation service returned HTTP {exc.code}; no pack was saved. Check account access and limits.') from None
    except (urllib.error.URLError,TimeoutError) as exc:
        raise RuntimeError('Could not reach the explanation service; no pack was saved.') from None
    return to_question(raw,unpack_response(result),model,root)

def save_draft(pack:dict,root:Path)->Path:
    if pack.get('review_status')!='draft':raise BankError('The generation cache accepts drafts only.')
    identifier=pack['id']
    if not identifier or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for ch in identifier):raise BankError('Unsafe question identifier.')
    directory=root/'data/ai_drafts';directory.mkdir(exist_ok=True)
    target=directory/(identifier+'.json');tmp=directory/(identifier+'.tmp')
    tmp.write_text(json.dumps({'schema_version':1,'questions':[pack]},indent=2,ensure_ascii=False))
    tmp.replace(target)
    return target
