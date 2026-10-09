"""Rebuild the source-only download using the user's original twelve PDFs."""
from pathlib import Path
import argparse,json,shutil,sys,hashlib
from io import BytesIO
import fitz
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from extract_attached_papers import FILES

def restore_question_image(doc,question,target):
 """Use the saved, checked regions rather than re-detecting question boundaries."""
 regions=question['regions']
 if len(regions)==1 and regions[0]['method']=='embedded_english_image':
  region=regions[0];page=doc[region['page']-1];wanted=fitz.Rect(region['rect'])
  for entry in page.get_images(full=True):
   for rect in page.get_image_rects(entry[0]):
    if max(abs(a-b) for a,b in zip(rect,wanted))<0.02:
     pix=fitz.Pixmap(doc,entry[0])
     if pix.n>4:pix=fitz.Pixmap(fitz.csRGB,pix)
     target.write_bytes(pix.tobytes('png'))
     return
  raise RuntimeError('Original embedded question image not found: '+question['id'])
 images=[]
 for region in regions:
  pix=doc[region['page']-1].get_pixmap(matrix=fitz.Matrix(1.7,1.7),clip=fitz.Rect(region['rect']))
  images.append(Image.open(BytesIO(pix.tobytes('png'))).convert('RGB'))
 combined=Image.new('RGB',(max(im.width for im in images),sum(im.height for im in images)+12*(len(images)-1)),'white')
 y=0
 for im in images:combined.paste(im,(0,y));y+=im.height+12
 encoded=BytesIO();combined.save(encoded,format='PNG',optimize=True)
 target.write_bytes(encoded.getvalue())

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-dir',type=Path,required=True,help='Folder containing your original PDFs')
 args=parser.parse_args();paper_dir=ROOT/'papers';paper_dir.mkdir(exist_ok=True)
 records=json.loads((ROOT/'data/source_anchors.json').read_text())
 existing=list(args.source_dir.glob('*.pdf'))
 by_hash={hashlib.sha256(p.read_bytes()).hexdigest():p for p in existing}
 missing=[]
 for pid,name in FILES.items():
  wanted=records[pid]['sha256'];found=by_hash.get(wanted)
  if not found:missing.append(name);continue
  dest=paper_dir/(pid+'.pdf')
  if dest.resolve()!=found.resolve():shutil.copy2(found,dest)
 if missing:parser.error('Original matching PDFs are missing: '+', '.join(missing))
 questions=json.loads((ROOT/'data/raw_questions.json').read_text())
 assets=ROOT/'assets/questions';assets.mkdir(parents=True,exist_ok=True)
 for pid in FILES:
  with fitz.open(paper_dir/(pid+'.pdf')) as doc:
   for question in questions:
    if question['paper_id']==pid:restore_question_image(doc,question,assets/(question['id']+'.png'))
 print('All 12 PDFs and 1,420 question images are ready. Run: python -m streamlit run streamlit_app.py')
if __name__=='__main__':main()
