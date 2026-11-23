from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document
from docx.shared import Inches, Pt
ROOT = Path(__file__).resolve().parent
folders = ['activity-2.1','activity-2.1-try','activity-2.2','activity-2.2-try']
for name in folders:
    for file in ['output.json','output.png']:
        if not (ROOT/name/file).is_file(): raise SystemExit(f'Missing {name}/{file}')
if not (ROOT/folders[-1]/'compass.png').is_file(): raise SystemExit('Missing Compass screenshot')
d = Document()
d.add_heading('Exercise 2: Cloud Setup and CRUD',0)
d.add_paragraph('23CSE528 | NoSQL DBs using MongoDB')
d.add_paragraph('Activity 2.1 comparison uses local MongoDB Community Server instead of Docker, as requested. This differs from the original assignment.')
d.add_paragraph('Reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-02')
for name in folders:
    d.add_page_break(); d.add_heading(name,1)
    for f in sorted((ROOT/name).glob('*.py')):
        d.add_heading(f.name,2)
        for line in f.read_text(encoding='utf-8').splitlines():
            r=d.add_paragraph().add_run(line); r.font.name='Consolas'; r.font.size=Pt(8)
            r._parent.paragraph_format.space_after=Pt(0)
    d.add_heading('Actual execution evidence',2)
    for f in sorted((ROOT/name).glob('*.png')):
        d.add_picture(str(f),width=Inches(5.8))
for f in ['common.py','books.py']:
    d.add_page_break(); d.add_heading('Shared helper: '+f,1)
    for line in (ROOT/f).read_text(encoding='utf-8').splitlines():
        par=d.add_paragraph(); par.paragraph_format.space_after=Pt(0)
        r=par.add_run(line); r.font.name='Consolas'; r.font.size=Pt(8)
report=ROOT/'Lab2-Report.docx'; d.save(report)
with ZipFile(ROOT/'Lab2-Submission.zip','w',ZIP_DEFLATED) as z:
    for name in folders:
        for f in (ROOT/name).iterdir():
            if f.suffix in {'.py','.json','.png'}: z.write(f,f.relative_to(ROOT))
    for name in ['common.py','books.py','requirements.txt','README.md','.env.example','RUN-LABS.bat','CONFIGURE-ATLAS.bat','configure_atlas.py',report.name]:
        z.write(ROOT/name,name)
print('Created Lab2-Report.docx and Lab2-Submission.zip')
