import logging
from io import BytesIO
from fpdf import FPDF

logger = logging.getLogger(__name__)

# Ranglar palitrasini sozlaymiz
INK = (26, 26, 46)
ACCENT = (192, 57, 43)
SIDEBAR_BG = (22, 22, 42)
WHITE = (255, 255, 255)
TAG_TXT = (190, 188, 210)

def _safe(text: str) -> str:
    """Unicode harflarni latin-1 (FPDF kutubxonasi tushunadigan) formatga o'tkazish"""
    if not text: return ""
    # O'zbekcha harflarni o'xshashlariga almashtirish
    rep = {"o'": "o", "g'": "g", "sh": "sh", "ch": "ch", "O'": "O", "G'": "G"}
    for k, v in rep.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")

def create_pdf(data: dict) -> BytesIO:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    # 1. Sidebar background
    pdf.set_fill_color(*SIDEBAR_BG)
    pdf.rect(0, 0, 70, 297, "F")
    
    # 2. Name & Title (Main area)
    pdf.set_xy(75, 15)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*INK)
    pdf.cell(0, 10, _safe(data.get("full_name", "")))
    
    pdf.set_xy(75, 25)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "SOFTWARE ENGINEER & DEVELOPER")
    
    # 3. Sidebar content (Contacts & Skills)
    pdf.set_text_color(*WHITE)
    y = 40
    
    # Contact Label
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, "CONTACT")
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(10, y + 10)
    pdf.multi_cell(50, 5, _safe(f"Email: {data.get('email', '')}\n\n{data.get('contacts', '')}"))
    
    # 4. Main content (Experience & Education)
    y_main = 45
    
    # Experience
    pdf.set_xy(75, y_main)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 10, "PROFESSIONAL EXPERIENCE")
    
    pdf.set_xy(75, y_main + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*INK)
    pdf.multi_cell(120, 6, _safe(data.get("experience", "")))
    
    # Education
    y_edu = pdf.get_y() + 10
    pdf.set_xy(75, y_edu)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 10, "EDUCATION")
    
    pdf.set_xy(75, y_edu + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*INK)
    pdf.multi_cell(120, 6, _safe(data.get("education", "")))

    buf = BytesIO(pdf.output())
    buf.seek(0)
    return buf