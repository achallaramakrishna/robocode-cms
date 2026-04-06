"""
generate_notes_pdf.py
======================
Generates a professional PDF from a notes JSON file using fpdf2.
Designed for the RoboBank Java Full Stack course.

Usage (on prod):
    /opt/robodynamics/venv/bin/python3 generate_notes_pdf.py \
        --input /path/to/notes_day_01.json \
        --output /path/to/notes_day_01.pdf

Run locally:
    python generate_notes_pdf.py --input generated_content/day_01/notes_day_01.json --output generated_content/day_01/notes_day_01.pdf
"""

import sys
import json
import argparse
from pathlib import Path

try:
    from fpdf import FPDF, XPos, YPos
    from fpdf.enums import XPos, YPos
except ImportError:
    print("fpdf2 not installed. Run: pip install fpdf2")
    sys.exit(1)


# ─── Colors ───────────────────────────────────────────────────────────────────
ROBOBANK_BLUE   = (0,   80,  158)   # Primary brand color
ROBOBANK_ORANGE = (255, 140,  0)    # Accent color
DARK_GRAY       = (50,  50,   50)   # Body text
LIGHT_GRAY      = (245, 245, 245)   # Code backgrounds
MID_GRAY        = (150, 150, 150)   # Subtle separators
WHITE           = (255, 255, 255)
CODE_BG         = (30,  30,   46)   # Dark background for code blocks
CODE_TEXT       = (220, 220, 170)   # Light yellow text for code
HIGHLIGHT_BG    = (255, 250, 205)   # Light yellow for key points
WARNING_BG      = (255, 235, 235)   # Light red for common mistakes


# Detect font directory
import os as _os
_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "C:/Windows/Fonts",
    _os.path.expanduser("~/fonts"),
]
_FONT_DIR = ""
for _d in _FONT_DIRS:
    if _os.path.exists(_os.path.join(_d, "DejaVuSans.ttf")):
        _FONT_DIR = _d
        break


def _font(name):
    """Return absolute font path."""
    if _FONT_DIR:
        return _os.path.join(_FONT_DIR, name)
    return name  # fallback: let fpdf search PATH


class NotesPDF(FPDF):
    """Custom PDF class for RoboBank course notes."""

    def __init__(self, meta: dict):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.meta = meta
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(left=20, top=20, right=20)
        # Register Unicode-compatible fonts
        self.add_font("DejaVu", style="", fname=_font("DejaVuSans.ttf"))
        self.add_font("DejaVu", style="B", fname=_font("DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", style="I", fname=_font("DejaVuSans-Oblique.ttf"))
        self.add_font("DejaVuMono", style="", fname=_font("DejaVuSansMono.ttf"))
        self.add_font("DejaVuMono", style="B", fname=_font("DejaVuSansMono-Bold.ttf"))

    def header(self):
        # Blue header bar
        self.set_fill_color(*ROBOBANK_BLUE)
        self.rect(0, 0, 210, 14, 'F')

        # Course name (left)
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(10, 3)
        self.cell(120, 8, "RoboBank Java Full Stack Training", align="L")

        # Page number (right)
        self.set_xy(160, 3)
        self.cell(40, 8, f"Page {self.page_no()}", align="R")

        # Reset text color
        self.set_text_color(*DARK_GRAY)
        self.set_xy(20, 18)  # Start content area below header

    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*ROBOBANK_ORANGE)
        self.rect(0, 283, 210, 14, 'F')
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*WHITE)
        self.set_xy(10, 285)
        self.cell(190, 8, f"{self.meta.get('session_title', '')}  |  {self.meta.get('date', '')}  |  {self.meta.get('phase', '')}", align="C")
        self.set_text_color(*DARK_GRAY)

    def cover_page(self, overview: dict):
        """Generate a styled cover/overview page."""
        self.add_page()

        # Big title block
        self.set_fill_color(*ROBOBANK_BLUE)
        self.rect(0, 14, 210, 60, 'F')

        # Day number (large)
        self.set_font("DejaVu", "B", 36)
        self.set_text_color(*WHITE)
        self.set_xy(20, 20)
        day = self.meta.get("session_day", 1)
        self.cell(40, 20, f"Day {day}", align="L")

        # Session title
        self.set_font("DejaVu", "B", 14)
        self.set_xy(20, 42)
        title = self.meta.get("session_title", "").replace(f"Day {day} - ", "")
        self.multi_cell(170, 8, title, align="L")

        # Phase + date
        self.set_font("DejaVu", "", 10)
        self.set_xy(20, 64)
        self.cell(170, 8, f"{self.meta.get('phase', '')}  •  {self.meta.get('date', '')}  •  Reading time: {self.meta.get('reading_time_minutes', 45)} min", align="L")

        # Reset position
        self.set_text_color(*DARK_GRAY)
        self.set_xy(20, 85)

        # Orange bar - "What You Will Learn"
        self.set_fill_color(*ROBOBANK_ORANGE)
        self.rect(20, 85, 170, 9, 'F')
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(22, 86)
        self.cell(166, 7, "LEARNING OUTCOMES", align="L")
        self.set_text_color(*DARK_GRAY)

        # Outcomes
        self.set_font("DejaVu", "", 10)
        self.set_xy(20, 97)
        for outcome in overview.get("learning_outcomes", []):
            self.set_x(20)
            self.cell(6, 7, "✓", align="C")
            self.cell(164, 7, outcome)
            self.ln()

        # Prerequisites
        if overview.get("prerequisite_knowledge"):
            self.ln(4)
            self.set_fill_color(*LIGHT_GRAY)
            self.rect(20, self.get_y(), 170, 9, 'F')
            self.set_font("DejaVu", "B", 10)
            self.set_xy(22, self.get_y() + 1)
            self.cell(166, 7, "PREREQUISITES")
            self.ln(10)
            self.set_font("DejaVu", "", 10)
            for prereq in overview.get("prerequisite_knowledge", []):
                self.set_x(26)
                self.cell(4, 6, "•")
                self.cell(160, 6, prereq)
                self.ln()

        # Summary box
        if overview.get("summary"):
            self.ln(4)
            self.set_fill_color(*HIGHLIGHT_BG)
            y = self.get_y()
            self.set_xy(20, y)
            self.set_font("DejaVu", "B", 10)
            self.cell(170, 7, "SESSION OVERVIEW")
            self.ln(8)
            self.set_font("DejaVu", "I", 10)
            self.set_x(24)
            self.multi_cell(162, 6, overview.get("summary", ""), align="L")

    def section_header(self, section_id: str, title: str):
        """Print a styled section header."""
        self.ln(4)
        # Blue left bar + section title
        self.set_fill_color(*ROBOBANK_BLUE)
        self.rect(20, self.get_y(), 5, 10, 'F')
        self.set_font("DejaVu", "B", 13)
        self.set_text_color(*ROBOBANK_BLUE)
        self.set_xy(28, self.get_y())
        self.cell(0, 10, f"{section_id}. {title}")
        self.ln(12)
        self.set_text_color(*DARK_GRAY)

    def body_text(self, text: str):
        """Print body text with paragraph breaks."""
        self.set_font("DejaVu", "", 10)
        self.set_x(20)
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                self.multi_cell(170, 6, para.strip(), align="J")
                self.ln(3)

    def code_block(self, code: str, description: str = ""):
        """Print a styled dark code block."""
        self.ln(2)
        if description:
            self.set_font("DejaVu", "I", 9)
            self.set_text_color(*MID_GRAY)
            self.set_x(20)
            self.multi_cell(170, 5, description)
            self.set_text_color(*DARK_GRAY)

        # Dark background
        lines = code.split('\n')
        block_height = len(lines) * 5.5 + 6

        # Check if fits on page
        if self.get_y() + block_height > 260:
            self.add_page()

        y_start = self.get_y()
        self.set_fill_color(*CODE_BG)
        self.rect(20, y_start, 170, block_height, 'F')

        # Code text
        self.set_font("DejaVuMono", "", 8)
        self.set_text_color(*CODE_TEXT)
        self.set_xy(24, y_start + 3)
        for line in lines:
            self.set_x(24)
            # Truncate very long lines
            if len(line) > 90:
                line = line[:87] + "..."
            self.cell(162, 5.5, line)
            self.ln(5.5)

        self.set_text_color(*DARK_GRAY)
        self.ln(3)

    def example_block(self, title: str, description: str, code: str, output: str):
        """Print a styled example with code and output."""
        self.ln(3)
        # Example title bar
        self.set_fill_color(*ROBOBANK_ORANGE)
        self.set_text_color(*WHITE)
        self.set_font("DejaVu", "B", 9)
        self.set_x(20)
        self.cell(170, 7, f"  Example: {title}", fill=True)
        self.ln(7)
        self.set_text_color(*DARK_GRAY)

        if description:
            self.set_font("DejaVu", "I", 9)
            self.set_x(20)
            self.multi_cell(170, 5, description)
            self.ln(1)

        self.code_block(code, "")

        if output:
            self.set_font("DejaVu", "B", 9)
            self.set_x(20)
            self.cell(170, 6, "Expected Output:")
            self.ln(6)
            # Output in lighter code block
            self.set_fill_color(*LIGHT_GRAY)
            out_lines = output.split('\n')
            out_h = len(out_lines) * 5 + 4
            y = self.get_y()
            self.rect(20, y, 170, out_h, 'F')
            self.set_font("DejaVuMono", "", 9)
            self.set_text_color(*DARK_GRAY)
            self.set_xy(24, y + 2)
            for line in out_lines:
                self.set_x(24)
                self.cell(162, 5, line[:85])
                self.ln(5)
            self.ln(3)

    def key_points_box(self, points: list):
        """Print a key points box."""
        if not points:
            return
        self.ln(3)
        y = self.get_y()
        self.set_fill_color(*HIGHLIGHT_BG)
        box_h = len(points) * 7 + 10
        self.rect(20, y, 170, box_h, 'F')
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(*ROBOBANK_BLUE)
        self.set_xy(22, y + 2)
        self.cell(0, 6, "💡 KEY POINTS")
        self.ln(7)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*DARK_GRAY)
        for point in points:
            self.set_x(22)
            self.cell(5, 6, "▶")
            self.multi_cell(161, 6, point)
        self.ln(3)

    def mistakes_box(self, mistakes: list):
        """Print a common mistakes box."""
        if not mistakes:
            return
        y = self.get_y()
        self.set_fill_color(*WARNING_BG)
        box_h = len(mistakes) * 7 + 10
        self.rect(20, y, 170, box_h, 'F')
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(180, 0, 0)
        self.set_xy(22, y + 2)
        self.cell(0, 6, "⚠ COMMON MISTAKES")
        self.ln(7)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*DARK_GRAY)
        for mistake in mistakes:
            self.set_x(22)
            self.cell(5, 6, "✗")
            self.multi_cell(161, 6, mistake)
        self.ln(3)

    def image_placeholder(self, image_data: dict):
        """Print an image or a placeholder box."""
        caption = image_data.get("caption", "")
        url = image_data.get("url", "")
        alt = image_data.get("alt", "")
        note = image_data.get("note", "")

        y = self.get_y()
        box_h = 45

        if y + box_h > 260:
            self.add_page()
            y = self.get_y()

        # Light blue placeholder box
        self.set_fill_color(220, 235, 255)
        self.rect(35, y, 140, box_h, 'F')
        self.set_draw_color(*ROBOBANK_BLUE)
        self.rect(35, y, 140, box_h)

        # Image icon placeholder
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*ROBOBANK_BLUE)
        self.set_xy(35, y + 5)
        self.cell(140, 8, "[ IMAGE ]", align="C")

        # Caption
        self.set_font("DejaVu", "I", 9)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(35, y + 15)
        self.multi_cell(140, 5, caption, align="C")

        # URL reference
        if url:
            self.set_font("DejaVu", "", 7)
            self.set_text_color(*MID_GRAY)
            self.set_xy(35, y + box_h - 10)
            # Truncate URL if too long
            display_url = url if len(url) < 70 else url[:67] + "..."
            self.cell(140, 5, f"Ref: {display_url}", align="C")

        if note:
            self.set_font("DejaVu", "I", 7)
            self.set_text_color(*MID_GRAY)
            self.set_xy(35, y + box_h - 5)
            self.cell(140, 4, note, align="C")

        self.set_text_color(*DARK_GRAY)
        self.set_draw_color(0, 0, 0)
        self.set_xy(20, y + box_h + 4)

    def cheat_sheet_page(self, cheat_sheet: list):
        """Print a quick reference / cheat sheet page."""
        self.add_page()
        self.set_fill_color(*ROBOBANK_BLUE)
        self.rect(20, 18, 170, 10, 'F')
        self.set_font("DejaVu", "B", 12)
        self.set_text_color(*WHITE)
        self.set_xy(22, 19)
        self.cell(0, 8, "QUICK REFERENCE — CHEAT SHEET")
        self.ln(14)
        self.set_text_color(*DARK_GRAY)

        # Two-column cheat sheet
        col1_x, col2_x = 20, 110
        col_w = 88
        y = self.get_y()

        for i, item in enumerate(cheat_sheet):
            x = col1_x if i % 2 == 0 else col2_x
            if i % 2 == 0 and i > 0:
                y = self.get_y() + 1

            # Item box
            self.set_fill_color(*LIGHT_GRAY)
            self.set_xy(x, y)
            self.set_font("DejaVuMono", "B", 9)
            self.set_text_color(*ROBOBANK_BLUE)
            self.cell(col_w, 6, f"  {item.get('item', '')}", fill=True)
            self.set_xy(x, y + 6)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*DARK_GRAY)
            self.multi_cell(col_w, 5, f"  {item.get('description', '')}", fill=True)

            if i % 2 == 1:
                self.set_xy(20, self.get_y() + 2)
                y = self.get_y()
            else:
                # Keep y the same for col2
                pass

    def assignment_page(self, assignment: dict):
        """Print the home assignment."""
        self.add_page()
        self.set_fill_color(*ROBOBANK_ORANGE)
        self.rect(20, 18, 170, 12, 'F')
        self.set_font("DejaVu", "B", 13)
        self.set_text_color(*WHITE)
        self.set_xy(22, 20)
        self.cell(0, 8, "HOME ASSIGNMENT")
        self.ln(16)
        self.set_text_color(*DARK_GRAY)

        # Title
        self.set_font("DejaVu", "B", 12)
        self.set_x(20)
        self.multi_cell(170, 8, assignment.get("title", ""))
        self.ln(4)

        # Description
        self.set_font("DejaVu", "", 11)
        self.set_x(20)
        self.multi_cell(170, 7, assignment.get("description", ""))
        self.ln(4)

        # Hints
        if assignment.get("hints"):
            self.set_fill_color(*HIGHLIGHT_BG)
            y = self.get_y()
            self.rect(20, y, 170, len(assignment["hints"]) * 7 + 12, 'F')
            self.set_font("DejaVu", "B", 10)
            self.set_xy(22, y + 2)
            self.cell(0, 7, "HINTS:")
            self.ln(8)
            self.set_font("DejaVu", "", 10)
            for hint in assignment["hints"]:
                self.set_x(26)
                self.cell(5, 6, "💡")
                self.multi_cell(161, 6, hint)
            self.ln(3)

        # Submission
        if assignment.get("submission"):
            self.ln(4)
            self.set_font("DejaVu", "B", 10)
            self.set_x(20)
            self.cell(0, 7, "SUBMISSION INSTRUCTIONS:")
            self.ln(7)
            self.set_font("DejaVu", "", 10)
            self.set_x(20)
            self.multi_cell(170, 7, assignment.get("submission", ""))


def generate_pdf(notes_json_path: Path, output_pdf_path: Path):
    """Main function: load JSON and generate PDF."""
    print(f"Loading: {notes_json_path}")
    with open(notes_json_path, encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get("meta", {})
    overview = data.get("overview", {})
    sections = data.get("sections", [])
    quick_ref = data.get("quick_reference", {})
    assignment = data.get("home_assignment", {})

    pdf = NotesPDF(meta)

    # Cover page
    pdf.cover_page(overview)

    # Content sections
    for section in sections:
        pdf.add_page()
        title = section.get("title", "")
        s_id = section.get("section_id", "")
        # Section number (extract number from 'S1', 'S2' etc.)
        s_num = s_id.replace("S", "")
        pdf.section_header(s_num, title)

        # Images (if any)
        for img in section.get("images", []):
            pdf.image_placeholder(img)

        # Main content
        pdf.body_text(section.get("content", ""))

        # Syntax box
        syntax = section.get("syntax_box")
        if syntax:
            pdf.code_block(
                syntax.get("code", ""),
                syntax.get("description", "")
            )

        # Examples
        for ex in section.get("examples", []):
            pdf.example_block(
                ex.get("title", ""),
                ex.get("description", ""),
                ex.get("code", ""),
                ex.get("output", "")
            )

        # Key points
        pdf.key_points_box(section.get("key_points", []))

        # Common mistakes
        pdf.mistakes_box(section.get("common_mistakes", []))

    # Cheat sheet page
    if quick_ref.get("cheat_sheet"):
        pdf.cheat_sheet_page(quick_ref["cheat_sheet"])

    # Assignment page
    if assignment:
        pdf.assignment_page(assignment)

    # Save
    pdf.output(str(output_pdf_path))
    print(f"PDF generated: {output_pdf_path} ({output_pdf_path.stat().st_size / 1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Generate PDF from Notes JSON")
    parser.add_argument("--input", required=True, help="Path to notes JSON file")
    parser.add_argument("--output", required=True, help="Output PDF path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf(input_path, output_path)


if __name__ == "__main__":
    main()
