# Turns report/report.md into report.docx (pandoc) and report.pdf (LibreOffice).
# After pandoc, python-docx tidies the look: fonts, headings, table borders.

import os
import subprocess
import pypandoc
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
BLUE = RGBColor(0x1F, 0x3A, 0x5F)

# 1. a Word template with our margins and fonts
ref = "report/reference.docx"
with open(ref, "wb") as f:
    f.write(subprocess.run([pypandoc.get_pandoc_path(), "--print-default-data-file", "reference.docx"],
                           capture_output=True, check=True).stdout)
doc = Document(ref)
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
sizes = {"Normal": 11, "Body Text": 11, "First Paragraph": 11, "Compact": 9.5,
         "Title": 24, "Subtitle": 13, "Author": 11, "Date": 11,
         "Heading 1": 15, "Heading 2": 12}
for name, size in sizes.items():
    if name in doc.styles:
        st = doc.styles[name]
        st.font.name, st.font.size = FONT, Pt(size)
        fonts = st.element.rPr.rFonts
        for theme in ["w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"]:
            fonts.attrib.pop(qn(theme), None)           # theme fonts would override ours
        fonts.set(qn("w:eastAsia"), FONT)
        if name.startswith("Heading") or name == "Title":
            st.font.color.rgb, st.font.bold = BLUE, True
doc.save(ref)

# 2. markdown -> docx
pypandoc.convert_file("report/report.md", "docx", outputfile="report/report.docx",
                      extra_args=["--resource-path=report", f"--reference-doc={ref}", "--columns=100"])
os.remove(ref)


# 3. tidy tables and pictures
def borders(table):
    tbl_pr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "8C8C8C")
        b.append(e)
    tbl_pr.append(b)


def shade(cell, color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shd)


doc = Document("report/report.docx")
for table in doc.tables:
    borders(table)
    header = table.rows[0]
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))   # repeat on new page
    for cell in header.cells:
        shade(cell, "DCE6F1")
    for r, row in enumerate(table.rows):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))   # keep each row on one page
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                for run in p.runs:
                    run.font.size = Pt(9.5)
                    run.font.bold = True if r == 0 else run.font.bold

for p in doc.paragraphs:
    if p._p.xpath(".//w:drawing"):                 # centre every chart
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.save("report/report.docx")

# 4. docx -> pdf
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", "report", "report/report.docx"],
               check=True, capture_output=True)
print("built report/report.docx and report/report.pdf")
