from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_BREAK
import sys
ROOT = Path(__file__).resolve().parent
ITEMS = [('3.1', 'activity-3.1/embedded_courses.py', 'Embedded course schema'),
         ('3.1-try', 'activity-3.1-try/prerequisites.py', 'Referenced prerequisites'),
         ('3.2', 'activity-3.2/migrate_blog.py', 'Referenced to embedded migration'),
         ('3.2-try', 'activity-3.2-try/large_comments.py', 'Large comment collections')]

def report():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Inches(.55)
    sec.left_margin = sec.right_margin = Inches(.75)
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.add_heading('Exercise 3 | MongoDB Data Modeling', 0)
    doc.add_paragraph('University enrollment and blog schema design')
    doc.add_paragraph('Name: ____________________    Roll No.: ____________________')
    doc.add_paragraph('Local MongoDB Community Server | Database: lab3-mongodb')
    for i, (label, rel, title) in enumerate(ITEMS):
        if i: doc.add_page_break()
        doc.add_heading(f'Activity {label}: {title}', 1)
        doc.add_heading('Python script', 2)
        for line in (ROOT / rel).read_text(encoding='utf-8').splitlines():
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1
            r = p.add_run(line or ' ')
            r.font.name = 'Consolas'
            r.font.size = Pt(8)
        doc.add_heading('Actual output screenshots', 2)
        images = sorted((ROOT/'screenshots').glob(label+'-[0-9]*.png'))
        if not images:
            doc.add_paragraph('Pending: insert actual terminal screenshot(s) after running this activity.')
        for img in images:
            doc.add_picture(str(img), width=Inches(6.6))
    doc.add_heading('Reference', 1)
    doc.add_paragraph('Assignment instructions supplied by Sujeet S Jagtap; chapter-03 repository link provided in assignment (not retrieved during preparation).')
    doc.save(ROOT/'Exercise-3.docx')

if __name__ == '__main__':
    report()
    if '--draft' in sys.argv: sys.exit(0)
    for label, rel, _ in ITEMS:
        if not (ROOT/rel).with_suffix('.json').exists() or not list((ROOT/'screenshots').glob(label+'-[0-9]*.png')):
            sys.exit(f'Missing JSON or actual screenshot for {label}. Run labs and capture evidence first.')
    with ZipFile(ROOT/'Exercise-3-Submission.zip','w',ZIP_DEFLATED) as z:
        for _, rel, _ in ITEMS:
            for path in (ROOT/rel, (ROOT/rel).with_suffix('.json')):
                z.write(path, path.relative_to(ROOT))
        for name in ('Exercise-3.docx','common.py','requirements.txt','README.md'):
            z.write(ROOT/name,name)
        for path in (ROOT/'screenshots').glob('*.png'):
            z.write(path,path.relative_to(ROOT))
    print('Created Exercise-3-Submission.zip')
