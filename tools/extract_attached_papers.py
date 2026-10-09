"""Build exact question images and an auditable source inventory.

Run from this workspace. Text OCR assists search/classification; it never replaces
the displayed question image and never supplies an answer key.
"""
from __future__ import annotations
import concurrent.futures
import csv
import hashlib
import json
import logging
import re
import shutil
import subprocess
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parents[1]
WORKSPACE = BASE.parent
logging.getLogger('pypdf').setLevel(logging.ERROR)
FILES = {
 '2020-june-26nov': 'CSIR NET Maths Nov 26 2020(1).pdf',
 '2020-june-30nov': 'CSIR NET Maths Nov 30 2020(1).pdf',
 '2021-june': 'CSIR NET 2022 _16-02-2022(1).pdf',
 '2022-june': 'June_2022_16 Sep 2022(1).pdf',
 '2023-june': '2023_June(1).pdf',
 '2023-december': '2023_Dec(1).pdf',
 '2024-june': '2024_June(1).pdf',
 '2024-december-28feb': '2024_Dec_28 Feb 2025(1).pdf',
 '2024-december-02mar': '2024_Dec_02 Mar 2025(1).pdf',
 '2025-june': '2025_June(1).pdf',
 '2025-december': 'csir-net-2025-mathematical-sciences-question-paper-and-answer-key-pdf-1773051569(1).pdf',
 '2026-june': 'csir-net-2026-mathematical-sciences-question-paper-jul-17-2026-shift-2-1787981124(1).pdf',
}


def anchors_for(doc, pid):
    anchors = []
    if pid == '2023-june':
        for i, page in enumerate(doc):
            file = WORKSPACE / 'tmp/june2023_ocr' / f'page-{i+1:03d}.tsv'
            if not file.exists():
                raise RuntimeError('Run the June 2023 page OCR first.')
            for row in csv.DictReader(file.open(), delimiter='\t'):
                value = row['text'].strip().replace('O','0').replace('o','0').replace('I','1')
                match = re.search(r'704\d{3}', value)
                if match and float(row['left']) < 220:
                    value = match[0]
                    n = int(value[-3:])
                    if 1 <= n <= 120:
                        anchors.append({'number':n, 'page':i, 'y':float(row['top'])/2, 'qid':value})
        # These two client IDs were checked visually after OCR split digits.
        anchors += [{'number':85,'page':51,'y':737,'qid':'704085'},
                    {'number':99,'page':61,'y':105,'qid':'704099'}]
    elif pid in ('2020-june-26nov', '2020-june-30nov', '2021-june'):
        for i,page in enumerate(doc):
            for word in page.get_text('words'):
                match = re.fullmatch(r'\((\d{1,3})\.\)', word[4])
                if match and word[0] < 115:
                    anchors.append({'number':int(match[1]),'page':i,'y':word[1], 'qid':None})
    elif pid == '2022-june':
        local = []
        for i,page in enumerate(doc):
            for word in page.get_text('words'):
                match = re.fullmatch(r'(\d{1,3})\)',word[4])
                if match and word[0] < 45:
                    local.append({'local_number':int(match[1]),'page':i,'y':word[1]})
        local.sort(key=lambda x:(x['page'],x['y']))
        for j,item in enumerate(local,1):
            anchors.append({'number':j,'page':item['page'],'y':item['y'],'qid':None})
        print(pid,'local markers',len(local),flush=True)
    elif pid in ('2025-december','2026-june'):
        for i,page in enumerate(doc):
            for word in page.get_text('words'):
                match = re.fullmatch(r'Q\.(\d{1,3})',word[4])
                if match:
                    anchors.append({'number':int(match[1]),'page':i,'y':word[1], 'qid':None})
    elif pid == '2025-june':
        for i,page in enumerate(doc):
            for block in page.get_text('dict')['blocks']:
                if 'lines' not in block: continue
                for line in block['lines']:
                    text=''.join(s['text'] for s in line['spans'])
                    match=re.search(r'Question Number\s*:\s*(\d+)',text)
                    if match:
                        qid=re.search(r'Question Id\s*:\s*(\d+)',text)
                        anchors.append({'number':int(match[1]),'page':i,'y':line['bbox'][1], 'qid':qid[1] if qid else None})
    else:
        for i,page in enumerate(doc):
            words = page.get_text('words')
            # Serial column, including rows whose heading is on the previous page.
            for word in words:
                if 45 <= word[0] < 62 and re.fullmatch(r'\d{1,3}',word[4]):
                    qids=[w[4] for w in words if 63<=w[0]<100 and abs(w[1]-word[1])<3 and w[4].isdigit()]
                    if qids:
                        anchors.append({'number':int(word[4]),'page':i,'y':word[1], 'qid':qids[0]})
    anchors.sort(key=lambda x:(x['page'],x['y']))
    unique={}
    for a in anchors:
        if a['number'] not in unique: unique[a['number']]=a
    return sorted(unique.values(),key=lambda x:(x['page'],x['y']))


def save_question_image(doc,pid,start,end,target):
    # Table, response-sheet and 2025 CBT exports store the English question plus
    # its four choices as one image. Preserve that image directly when possible.
    if pid not in ('2020-june-26nov','2020-june-30nov','2021-june','2022-june','2023-june'):
        candidates=[]
        last=end['page'] if end else len(doc)-1
        for pi in range(start['page'],last+1):
            page=doc[pi]
            lower=start['y']-10 if pi==start['page'] else -10
            upper=end['y'] if end and pi==end['page'] else page.rect.height
            for item in page.get_images(full=True):
                for rect in page.get_image_rects(item[0]):
                    if lower <= rect.y0 < upper and rect.width > 180 and rect.height > 25:
                        candidates.append((pi,rect.y0,rect,item[0]))
        if candidates:
            pi,_,rect,xref=min(candidates,key=lambda x:(x[0],x[1]))
            pix=fitz.Pixmap(doc,xref)
            if pix.n>4: pix=fitz.Pixmap(fitz.csRGB,pix)
            pix.save(target)
            return [{'page':pi+1,'rect':list(rect),'method':'embedded_english_image'}]
    parts=[]
    final_page=end['page'] if end else len(doc)-1
    images=[]
    from PIL import Image
    from io import BytesIO
    for pi in range(start['page'],final_page+1):
        page=doc[pi]
        top=max(0,start['y']-3) if pi==start['page'] else 0
        bottom=(end['y']-7) if end and pi==end['page'] else page.rect.height
        if bottom<=top+5: continue
        clip=fitz.Rect(25,top,page.rect.width-25,bottom)
        pix=page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),clip=clip)
        images.append(Image.open(BytesIO(pix.tobytes('png'))).convert('RGB'))
        parts.append({'page':pi+1,'rect':list(clip),'method':'page_crop'})
    if not images: raise RuntimeError(f'Empty question crop: {pid} {start}')
    w=max(im.width for im in images);h=sum(im.height for im in images)+12*(len(images)-1)
    combined=Image.new('RGB',(w,h),'white');y=0
    for im in images:
        combined.paste(im,(0,y));y+=im.height+12
    # Encode in memory and write once; avoid many tiny PNG writes on remote-backed mounts.
    encoded=BytesIO()
    combined.save(encoded,format='PNG',optimize=True)
    target.write_bytes(encoded.getvalue())
    return parts


def main():
    assets=BASE/'assets/questions';assets.mkdir(parents=True,exist_ok=True)
    paper_dir=BASE/'papers';paper_dir.mkdir(exist_ok=True)
    inventory=[];report=[]
    saved_anchors=BASE/'data/source_anchors.json'
    saved=json.loads(saved_anchors.read_text()) if saved_anchors.exists() else {}
    for pid,name in FILES.items():
        src=WORKSPACE/'upload'/name
        local=paper_dir/f'{pid}.pdf'
        if not src.exists():src=local
        if src.resolve()!=local.resolve():shutil.copy2(src,local)
        doc=fitz.open(src)
        digest=hashlib.sha256(src.read_bytes()).hexdigest()
        anchors=saved[pid]['anchors'] if pid in saved and saved[pid]['sha256']==digest else anchors_for(doc,pid)
        expected=set(range(21,121)) if pid=='2021-june' else set(range(1,121))
        found={a['number'] for a in anchors}
        report.append({'paper_id':pid,'pages':len(doc),'found':len(found),'missing':sorted(set(range(1,121))-found),
                       'unexpected':sorted(found-expected),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
        print(pid,'anchors',len(anchors),'missing',sorted(expected-found),flush=True)
        if found-expected: raise RuntimeError(f'Unexpected numbers in {pid}')
        for j,start in enumerate(anchors):
            end=anchors[j+1] if j+1<len(anchors) else None
            n=start['number'];qid=f'{pid}-q{n:03d}'
            asset=assets/f'{qid}.png'
            regions=save_question_image(doc,pid,start,end,asset)
            part='A' if n<=20 else ('B' if n<=60 else 'C')
            inventory.append({'id':qid,'paper_id':pid,'question_number':n,'question_id':start.get('qid'),
                              'part':part,'track':'Shared' if part=='A' else 'Unclassified',
                              'topic':'Aptitude' if part=='A' else 'Unclassified',
                              'difficulty':'Unrated','image':str(asset.relative_to(BASE)),
                              'regions':regions,'page':start['page']+1,'text':'',
                              'source_type':'official_exam','solution_status':'pending'})
    (BASE/'data/raw_questions.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    (BASE/'data/extraction_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('TOTAL',len(inventory),flush=True)

if __name__=='__main__':main()
