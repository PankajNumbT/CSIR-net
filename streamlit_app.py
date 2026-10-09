from __future__ import annotations
import json
import hashlib
import os
import random
from dataclasses import asdict
from html import escape
from pathlib import Path
import streamlit as st
from core import (BankError, LABELS, PENALTIES, TRACK_TOPICS, bank_digest, coverage,
                  export_bank, filter_questions, grade, overlay_solutions, parse_bank,
                  load_project_bank, shuffled_ids, validate_progress)

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='NET Studio · Mathematics & Statistics', page_icon='∑', layout='wide')
st.markdown('<style>'+(ROOT/'assets/style.css').read_text()+'</style>',unsafe_allow_html=True)
papers=json.loads((ROOT/'data/papers.json').read_text())
paper_ids={p['id'] for p in papers};paper_by_id={p['id']:p for p in papers}
raw=json.loads((ROOT/'data/raw_questions.json').read_text());raw_by_id={q['id']:q for q in raw}
official_keys={}
for key_file in sorted((ROOT/'data/official_keys').glob('*.json')):
    key_record=json.loads(key_file.read_text())
    official_keys[key_record['paper_id']]=key_record
for key,default in {'imported_bank':[],'responses':{},'results':{},'bookmarks':[],
                    'hints':{},'panels':{},'seed':random.SystemRandom().randint(0,10**9),
                    'queue_signature':'','queue':[],'cursor':0}.items():
    if key not in st.session_state:st.session_state[key]=default
try:
    # A session import replaces that source's pack, never its original question image.
    questions=load_project_bank(ROOT)
    incoming=parse_bank({'schema_version':1,'questions':st.session_state.imported_bank},paper_ids)
    questions=overlay_solutions(questions,incoming)
except (BankError,OSError,ValueError) as exc:
    st.error(f'Question bank could not be loaded: {exc}');st.stop()
q_by_id={q.id:q for q in questions}
# Recompute saved scores when a pack changes or an item becomes unscored.
current_results={}
for qid,rec in st.session_state.responses.items():
    question=q_by_id.get(qid)
    if not rec.get('submitted'):continue
    if question is None or question.review_status!='reviewed':
        rec['submitted']=False
        continue
    try:
        current_results[qid]=grade(question,rec['selected'])|{'assisted':rec.get('assisted',False)}
    except BankError:
        rec['submitted']=False
st.session_state.results=current_results
ready=[q for q in questions if q.review_status=='reviewed']
drafts=[q for q in questions if q.review_status=='draft']
issues=[q for q in questions if q.review_status=='source_issue']
pending=[q for q in questions if q.review_status=='pending']

def heading(kicker,title,subtitle):
    st.markdown(f'<div class="page-head"><div><div class="eyebrow">{escape(kicker)}</div>'
                f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>'
                '<span class="live-label">Learn one question at a time</span></div>',unsafe_allow_html=True)

def metrics():
    results=list(st.session_state.results.values());n=len(results)
    right=sum(r['correct'] for r in results)
    a,b,c,d=st.columns(4)
    a.metric('Scored attempts',n);b.metric('Correct',right)
    c.metric('Accuracy',f'{right/n:.0%}' if n else '—')
    d.metric('Practice score',f'{sum(r["points"] for r in results):g}')

def answer_provenance(q):
    st.caption(q.answer_source)
    key_record=official_keys.get(q.paper_id)
    source_id=raw_by_id.get(q.id,{}).get('question_id')
    if not key_record or source_id not in key_record['question_id_answers']:return
    official=key_record['question_id_answers'][source_id]
    if q.review_status=='source_issue':
        st.caption('Official key: '+(', '.join(official) if official else 'Dropped')+'. See the source-issue diagnosis in the solution.')
    elif set(official)==set(q.correct_options):
        st.caption('Answer set matches the official final key for this question ID.')
    else:
        st.caption('This answer set differs from the official final key and needs reconciliation.')
    st.markdown(f'[NTA final key · question ID {source_id} · PDF page {key_record["page"]}]({key_record["source_url"]})')

def generate_draft(q):
    from solver import generate_pack, save_draft
    try:
        with st.spinner('Preparing hints, a solution, theory, and worked examples…'):
            pack=generate_pack(raw_by_id[q.id],ROOT)
            save_draft(pack,ROOT)
        st.rerun()
    except (BankError,ValueError,RuntimeError,OSError) as exc:
        st.error(str(exc))

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">∑</span>NET Studio</div>'
                '<div class="brand-sub">CSIR NET · Mathematical Sciences</div>',unsafe_allow_html=True)
    page=st.radio('Workspace',['Practice','Papers','Question bank'],key='workspace')
    st.divider();st.caption('YOUR LEARNING TRACK')
    track=st.radio('Select subject',['Mathematics','Statistics'],key='track')
    if page=='Practice':
        eligible=[q for q in questions if q.track in (track,'Shared','Unclassified')]
        topics=['All topics']+TRACK_TOPICS[track]
        counts={t:sum(q.topic==t for q in eligible) for t in TRACK_TOPICS[track]}
        topic=st.selectbox('Topic',topics,key=f'topic_{track}',
            format_func=lambda t:t if t=='All topics' else f'{t} · {counts[t]}')
        status=st.selectbox('Content',['All source questions','Solutions ready','Source issues explained','Draft explanations','Awaiting solutions'],key='status')
        paper_id=st.selectbox('Paper',['all']+[p['id'] for p in papers],key='paper_filter',
            format_func=lambda x:'All papers' if x=='all' else paper_by_id[x]['label'])
        difficulty=st.multiselect('Difficulty',['Easy','Moderate','Hard','Unrated'],key='difficulty')
        part=st.selectbox('Exam part',['All parts','A','B','C'],key='part',
            format_func=lambda x:{'A':'Part A · 2 marks','B':'Part B · 3 marks','C':'Part C · 4.75 marks'}.get(x,x))
        search=st.text_input('Search questions',placeholder='e.g. eigenvalue, estimator',key='search')
        only_saved=st.checkbox('Bookmarked only',key='only_saved')
        if st.button('Shuffle questions',use_container_width=True,key='shuffle'):
            st.session_state.seed=random.SystemRandom().randint(0,10**9);st.session_state.cursor=0;st.rerun()
        st.markdown('<div class="legend">🟢 Easy &nbsp; 🟠 Moderate &nbsp; 🔴 Hard<br/>⚪ Unrated · Difficulty is an estimate.</div>',unsafe_allow_html=True)
    st.divider()
    st.caption(f'{len(papers)} papers · {len(raw):,} source questions · {len(ready)} solved')
    st.caption('Aptitude appears in both tracks. Provisional topic labels need review; unclassified questions appear in both tracks.' if pending else 'Aptitude appears in both tracks. Subjects follow the reviewed learning packs.')

if page=='Practice':
    heading('Practice room',track,'Choose a topic. Think it through. Build the theory behind it.')
    st.markdown(f'<div class="content-note"><b>{len(raw):,} questions from your 12 PDFs.</b> '
                f'{len(ready)} have worked solutions. {len(issues)} have explained source issues. '
                +(f'{len(drafts)} have draft explanations; {len(pending)} await explanations. ' if pending or drafts else 'Every available question has hints, theory, and worked examples. ')+
                'The February 2022 copy is missing Part A.</div>',unsafe_allow_html=True)
    metrics()
    pool=filter_questions(questions,track,topic,paper_id,'official_exam',difficulty,part,
                         set(st.session_state.bookmarks) if only_saved else None)
    wanted={'Solutions ready':'reviewed','Source issues explained':'source_issue','Draft explanations':'draft','Awaiting solutions':'pending'}.get(status)
    if wanted:pool=[q for q in pool if q.review_status==wanted]
    if search.strip():
        query=search.strip().casefold()
        pool=[q for q in pool if query in (q.id+' '+raw_by_id.get(q.id,{}).get('text','')+' '+q.prompt+' '+q.topic).casefold()]
    signature=json.dumps([track,topic,paper_id,difficulty,part,status,search,only_saved,
        sorted(st.session_state.bookmarks) if only_saved else [],st.session_state.seed,bank_digest(questions)])
    if st.session_state.queue_signature!=signature:
        # Shuffle within readiness groups so the opening question has a solution when available.
        shuffled=shuffled_ids(pool,st.session_state.seed)
        order={'reviewed':0,'source_issue':1,'draft':2,'pending':3}
        st.session_state.queue=sorted(shuffled,key=lambda x:order[q_by_id[x].review_status])
        st.session_state.cursor=0;st.session_state.queue_signature=signature
    queue=st.session_state.queue
    if not queue:
        st.info('No questions match these filters. Choose All topics or another paper.'+(' Topics with zero questions may still be awaiting classification.' if pending else ''))
    else:
        cursor=min(st.session_state.cursor,len(queue)-1);q=q_by_id[queue[cursor]]
        rec=st.session_state.responses.setdefault(q.id,{'selected':[],'submitted':False,'assisted':False})
        result=st.session_state.results.get(q.id)
        a,b,c=st.columns([3,2,1])
        a.caption(f'QUESTION {cursor+1} OF {len(queue):,} · PAPER QUESTION {q.question_number}')
        jump_key=hashlib.sha256(signature.encode()).hexdigest()[:12]
        destination=b.number_input('Jump to position',min_value=1,max_value=len(queue),value=cursor+1,key=f'jump_{jump_key}_{cursor}',label_visibility='collapsed')
        if b.button('Go',key='go'):
            st.session_state.cursor=int(destination)-1;st.rerun()
        saved=q.id in st.session_state.bookmarks
        if c.button('★ Saved' if saved else '☆ Save',key='bookmark'):
            if saved:st.session_state.bookmarks.remove(q.id)
            else:st.session_state.bookmarks.append(q.id)
            st.rerun()
        st.progress((cursor+1)/len(queue))
        with st.container(border=True):
            tags=[(q.topic,'topic'),(q.difficulty,q.difficulty.lower()),(q.answer_type,''),
                  (f'{q.marks:g} marks · Part {q.part}',''),(q.review_status.replace('_',' ').title(),'')]
            st.markdown('<div class="metadata">'+''.join(f'<span class="tag {cls}">{escape(label)}</span>' for label,cls in tags)+'</div>',unsafe_allow_html=True)
            st.caption(paper_by_id[q.paper_id]['label'])
            issue=raw_by_id.get(q.id,{}).get('source_issue')
            if issue:st.warning('Source check needed: '+issue)
            if q.classification_status=='provisional':st.caption('Topic assigned provisionally from OCR keywords.')
            if q.review_status!='pending':st.markdown(q.prompt)
            if q.image:
                img=(ROOT/q.image).resolve()
                allowed=(ROOT/'assets/questions').resolve()
                if img.is_relative_to(allowed) and img.suffix=='.png' and img.exists():
                    if q.review_status=='pending':st.image(str(img),width='stretch')
                    else:
                        needs_diagram=any(word in q.prompt.lower() for word in ('diagram','figure','shown below','shown in','in the graph'))
                        with st.expander('Original question · diagrams and source check',expanded=needs_diagram):
                            st.image(str(img),width='stretch')
            if q.part=='C':
                st.caption('Select every correct option. The complete set is required for marks.')
                selected=[]
                for label in LABELS:
                    choice,text_col=st.columns([1,7])
                    checked=choice.checkbox(label,value=label in rec['selected'],key=f'answer_{q.id}_{label}',disabled=bool(result))
                    text_col.markdown(q.options[label])
                    if checked:selected.append(label)
            else:
                for label in LABELS:st.markdown(f'**{label}.** {q.options[label]}')
                idx=LABELS.index(rec['selected'][0]) if rec['selected'] else None
                value=st.radio('Choose one answer',LABELS,index=idx,
                    horizontal=True,key=f'answer_{q.id}',disabled=bool(result))
                selected=[value] if value else []
            rec['selected']=selected
            left,right=st.columns([2,3])
            if q.review_status=='reviewed':
                if left.button('Check answer',type='primary',use_container_width=True,disabled=bool(result),key='submit'):
                    try:
                        st.session_state.results[q.id]=grade(q,selected)|{'assisted':rec['assisted']}
                        rec['submitted']=True;st.rerun()
                    except BankError as exc:st.warning(str(exc))
            else:
                if left.button('Save answer',type='primary',use_container_width=True,key='save_answer'):
                    st.success('Selection saved. This source-issue item remains unscored.' if q.review_status=='source_issue' else 'Selection saved. A score will be available after the answer is reviewed.')
                st.caption('This question is excluded from scoring.' if q.review_status=='source_issue' else 'This question is not graded yet.')
            right.caption(f'Incorrect answer: −{PENALTIES[q.part]:g} marks.' if PENALTIES[q.part] else 'No negative marking in Part C.')
            if result:
                text=f'Answer: {", ".join(q.correct_options)} · Score: {result["points"]:g}'
                (st.success if result['correct'] else st.error)(text)
                if result['assisted']:st.caption('Assisted attempt: a hint or explanation was opened before submission.')
                answer_provenance(q)
            if q.review_status=='draft':st.warning('AI-generated draft: answer and explanation await independent checking.')
            if q.review_status=='source_issue':
                st.warning('This question has a source ambiguity, an official withdrawal, or an answer-key discrepancy. Open Solution for the derivation and the exact issue. This question is excluded from scoring.')
            st.divider();x,y,z=st.columns(3)
            seen=st.session_state.hints.get(q.id,0)
            hint_label=f'Hint · {seen}/{len(q.hints)}' if q.hints else 'Hint'
            for col,label,panel in [(x,hint_label,'hint'),(y,'Solution','solution'),(z,'Theory & similar questions','theory')]:
                if col.button(label,use_container_width=True,key=panel):
                    st.session_state.panels[q.id]=panel
                    if panel=='hint':st.session_state.hints[q.id]=min(seen+1,len(q.hints))
                    if not result:rec['assisted']=True
                    st.rerun()
            panel=st.session_state.panels.get(q.id)
            if panel and q.review_status=='pending':
                st.info('The learning pack for this question is pending. Its original text and options are available above.')
                if os.getenv('OPENAI_API_KEY') and st.button('Generate a draft explanation',key='generate'):
                    generate_draft(q)
            elif panel=='hint':
                st.subheader('A nudge in the right direction')
                for i,hint in enumerate(q.hints[:st.session_state.hints[q.id]],1):st.markdown(f'**Hint {i}.** {hint}')
            elif panel=='solution':
                st.subheader('Step-by-step solution');st.markdown(q.solution);answer_provenance(q)
            elif panel=='theory':
                st.subheader('Understand the idea');st.markdown(q.theory)
                st.subheader('Similar questions')
                for i,example in enumerate(q.similar_questions,1):
                    st.markdown(f'**Practice {i}.** {example["prompt"]}')
                    with st.expander(f'Worked answer {i}'):st.markdown(example['solution'])
            st.caption(f'Original paper question {q.question_number} · Starts on PDF page {q.page} · A–D correspond to original options 1–4 or a–d.')
        prev,mid,nxt=st.columns([1,3,1])
        if prev.button('Previous',use_container_width=True,disabled=cursor==0,key='previous'):
            st.session_state.cursor=cursor-1;st.rerun()
        mid.caption('Download your progress below to retain answers and bookmarks.')
        if nxt.button('Next question',use_container_width=True,disabled=cursor==len(queue)-1,key='next'):
            st.session_state.cursor=cursor+1;st.rerun()
    with st.expander('Save or restore your practice session'):
        progress={'schema_version':1,'bookmarks':st.session_state.bookmarks,'responses':st.session_state.responses}
        st.download_button('Download progress',json.dumps(progress,indent=2),'net_studio_progress.json','application/json')
        upload=st.file_uploader('Restore progress JSON',type=['json'],key='progress_upload')
        if upload and st.button('Restore session',key='restore'):
            try:
                clean=validate_progress(json.loads(upload.getvalue()),set(q_by_id))
                results={}
                for qid,rec in clean['responses'].items():
                    if rec['submitted'] and q_by_id[qid].review_status=='reviewed':
                        results[qid]=grade(q_by_id[qid],rec['selected'])|{'assisted':rec['assisted']}
                    else:rec['submitted']=False
                for key in list(st.session_state):
                    if key.startswith('answer_'):del st.session_state[key]
                st.session_state.responses=clean['responses'];st.session_state.bookmarks=clean['bookmarks']
                st.session_state.results=results;st.rerun()
            except (BankError,ValueError,TypeError) as exc:st.error(f'Could not restore progress: {exc}')

elif page=='Papers':
    heading('Paper library','2020 to 2026','Your 12 source PDFs, available directly in the app.')
    st.info('The February 2022 attachment contains questions 21–120 only. Its 20 aptitude questions are missing. The supplied collection ends with June 2026.')
    year=st.selectbox('Session year',['All years']+sorted({str(p['year']) for p in papers}))
    subset=[p for p in papers if year=='All years' or str(p['year'])==year]
    selected=st.selectbox('Select a paper',[p['id'] for p in subset],format_func=lambda x:paper_by_id[x]['label'])
    p=paper_by_id[selected];cov={r['paper_id']:r for r in coverage(questions,papers)}[selected]
    with st.container(border=True):
        st.markdown(f'<div class="paper-head">{escape(p["label"])}</div>',unsafe_allow_html=True)
        st.caption(f'Held {p["date"]} · {cov["available"]}/120 source questions · {cov["ready"]} solutions ready')
        a,b=st.columns(2)
        a.download_button('Download original PDF',(ROOT/'papers'/f'{selected}.pdf').read_bytes(),f'{selected}.pdf','application/pdf',use_container_width=True)
        b.link_button('Public source link',p['url'],use_container_width=True)
        st.caption(p['note'])
        if selected=='2021-june':
            st.link_button('Additional copy for locating missing Part A',
                'https://pkalika.in/wp-content/uploads/2022/04/net-feb-2022-with-ans-key.pdf')
            st.caption('This additional public copy has not been imported. The app currently uses questions 21–120 from your attached PDF.')
    st.dataframe(coverage(questions,subset),hide_index=True,use_container_width=True)
    st.caption('Session year can differ from the calendar year of the exam. All local PDFs retain the attached originals.')

else:
    heading('Content workspace','Question bank','Check source coverage and add complete learning packs.')
    a,b,c,d=st.columns(4);a.metric('Source questions',len(raw));b.metric('Solutions ready',len(ready));c.metric('Source issues explained',len(issues));d.metric('Awaiting explanations',len(pending))
    st.dataframe(coverage(questions,papers),hide_index=True,use_container_width=True)
    st.caption('Part A: 20 × 2 marks. Part B: 40 × 3 marks. Part C: 60 × 4.75 marks. Pending, draft, and source-issue questions are not scored.')
    if pending:st.warning(f'{len(pending)} learning packs remain unfinished. OCR-based topic assignments are provisional; unrated difficulty is shown in grey.')
    else:st.success('Every available source question has a learning pack. Source issues are explained and excluded from scoring.')
    with st.expander('Import or export learning packs',expanded=True):
        st.write('A learning pack contains a question transcription, options, correct answers, hints, a worked solution, theory, and worked similar questions.')
        upload=st.file_uploader('Question-bank JSON',type=['json'],key='bank_upload')
        if upload and st.button('Validate and import',type='primary',key='import'):
            try:
                incoming=parse_bank(json.loads(upload.getvalue()),paper_ids)
                for q in incoming:
                    if q.id not in raw_by_id:raise BankError('Import must reference a source question ID in this bank.')
                overlay_solutions(questions,incoming)
                incoming_ids={q.id for q in incoming}
                st.session_state.imported_bank=[x for x in st.session_state.imported_bank if x['id'] not in incoming_ids]+[asdict(q) for q in incoming]
                for q in incoming:
                    st.session_state.results.pop(q.id,None)
                    if q.id in st.session_state.responses:st.session_state.responses[q.id]['submitted']=False
                st.rerun()
            except (BankError,ValueError,TypeError) as exc:st.error(f'Import rejected: {exc}')
        packs=[q for q in questions if q.review_status!='pending']
        st.download_button('Export learning packs',export_bank(packs),'learning_packs.json','application/json')
        st.download_button('Download import example',(ROOT/'data/import_example.json').read_bytes(),'import_example.json','application/json')
        st.caption('Imports stay in this browser session until exported. Permanent packs go in data/completed_papers/.')
    with st.expander('Optional explanation backend'):
        st.write('With an OpenAI API key configured on your server, pending questions can receive draft learning packs. Generation sends the selected question image to the API and incurs API usage charges. Drafts need independent review before grading.')
        st.caption('Backend configured.' if os.getenv('OPENAI_API_KEY') else 'Backend is not configured. See README.md for setup and the resumable bulk-generation command.')
    st.download_button('Download extraction report',(ROOT/'data/extraction_report.json').read_bytes(),'extraction_report.json','application/json')
st.caption('NET Studio · Independent study app. Inspired by modern learning platforms; not affiliated with Unacademy or CSIR.')
