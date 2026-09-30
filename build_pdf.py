#!/usr/bin/env python3
"""Render studio-edition.md -> a polished, print-ready PDF (Letter)."""
import re
from fpdf import FPDF

SRC = "/home/hatch/workspace/kestrelattice/studio-edition.md"
OUT = "/home/hatch/workspace/your_files/kestrelattice-studio-edition.pdf"
FD = "/usr/share/fonts/truetype/dejavu/"

ACCENT = (224, 122, 95)      # #e07a5f terracotta
ACCENT_DARK = (158, 79, 58)
INK = (30, 27, 24)
MUTED = (120, 110, 98)
CODE_BG = (244, 241, 236)
LINE = (208, 198, 186)
WHITE = (255, 255, 255)
ROW_ALT = (250, 247, 242)

SANS = "dvsans"
MONO = "dvmono"

def strip_md(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s

def segments(line):
    """Split a line into (text, style) segments: styles '', 'B', 'I', 'C'."""
    out = []
    pat = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)")
    pos = 0
    for m in pat.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], ""))
        tok = m.group(0)
        if tok.startswith("**"):
            out.append((tok[2:-2], "B"))
        elif tok.startswith("`"):
            out.append((tok[1:-1], "C"))
        else:
            out.append((tok[1:-1], "I"))
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], ""))
    return [(t, s) for t, s in out if t]

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.add_font(SANS, "", FD + "DejaVuSans.ttf")
        self.add_font(SANS, "B", FD + "DejaVuSans-Bold.ttf")
        self.add_font(SANS, "I", FD + "DejaVuSans.ttf")   # no oblique on system; fall back
        self.add_font(MONO, "", FD + "DejaVuSansMono.ttf")
        self.set_auto_page_break(True, margin=20)
        self.in_body = False

    def footer(self):
        if not self.in_body or self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font(SANS, "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, "ghostcorpnet  ·  Studio Edition", align="L")
        self.set_xy(-30, -15)
        self.cell(20, 5, str(self.page_no()), align="R")

    # ---- primitives -----------------------------------------------------
    def rich_para(self, segs, size=10.5, lh=5.8, indent=0, bullet=None):
        """Write wrapped rich text; optional bullet/checkbox prefix."""
        if indent:
            self.set_x(self.l_margin + indent)
        if bullet:
            self.set_font(SANS, "", size)
            self.set_text_color(*ACCENT_DARK)
            self.write(lh, bullet + "  ")
        self.set_text_color(*INK)
        for text, st in segs:
            if st == "C":
                self.set_font(MONO, "", size - 1.2)
            else:
                self.set_font(SANS, st, size)
            self.write(lh, text)
        self.ln(lh + 1.4)

    def para(self, line, size=10.5, lh=5.8):
        line = line.strip()
        if not line:
            self.ln(2.5)
            return
        if line.startswith("- [ ]"):
            self.rich_para(segments(line[5:].strip()), size=size, lh=lh, bullet="☐")
        elif line.startswith("- "):
            self.rich_para(segments(line[2:].strip()), size=size, lh=lh, bullet="•")
        elif re.match(r"^\d+\.\s", line):
            num, rest = re.match(r"^(\d+)\.\s(.*)$", line).groups()
            self.rich_para(segments(rest.strip()), size=size, lh=lh, bullet=num + ".")
        else:
            self.rich_para(segments(line), size=size, lh=lh)

    def code_block(self, lines):
        self.ln(1)
        self.set_fill_color(*CODE_BG)
        x = self.l_margin
        w = self.epw
        self.set_font(MONO, "", 7.8)
        self.set_text_color(*INK)
        y0 = self.get_y()
        self.set_x(x)
        text = "\n".join(lines)
        self.multi_cell(w, 4.5, text, fill=True, new_x="LMARGIN", new_y="NEXT")
        y1 = self.get_y()
        self.set_draw_color(*LINE)
        self.set_line_width(0.3)
        self.line(x, y0, x, y1)
        self.line(x + w, y0, x + w, y1)
        self.line(x, y0, x + w, y0)
        self.line(x, y1, x + w, y1)
        self.ln(3)

    def md_table(self, rows):
        if not rows:
            return
        header, body = rows[0], rows[1:]
        ncols = len(header)
        w = self.epw
        if ncols == 5:
            widths = [w * p for p in (0.11, 0.21, 0.30, 0.20, 0.18)]
        elif ncols == 4:
            widths = [w * p for p in (0.16, 0.30, 0.30, 0.24)]
        elif ncols == 3:
            widths = [w * p for p in (0.22, 0.44, 0.34)]
        else:
            widths = [w / ncols] * ncols
        self.ln(2)
        x0 = self.l_margin
        # header
        self.set_font(SANS, "B", 8)
        self.set_fill_color(*ACCENT)
        self.set_text_color(*WHITE)
        self.set_x(x0)
        h = 6.5
        for i, cell in enumerate(header):
            self.cell(widths[i], h, " " + strip_md(cell.strip()), border=1, fill=True)
        self.ln(h)
        # body rows
        alt = False
        line_h = 4.2
        for row in body:
            if len(row) < ncols:
                row = row + [""] * (ncols - len(row))
            texts = [strip_md(c.strip()) for c in row[:ncols]]
            self.set_font(SANS, "", 7.6)
            # measure row height with a dry run
            max_lines = 1
            for i, t in enumerate(texts):
                rendered = self.multi_cell(widths[i], line_h, " " + t,
                                           dry_run=True, output="LINES")
                max_lines = max(max_lines, len(rendered))
            rh = max(6.5, max_lines * line_h + 2.5)
            if self.get_y() + rh > self.page_break_trigger:
                self.add_page()
            self.set_fill_color(*(ROW_ALT if alt else WHITE))
            self.set_text_color(*INK)
            y_start = self.get_y()
            x = x0
            for i, t in enumerate(texts):
                self.set_xy(x, y_start)
                self.multi_cell(widths[i], line_h, " " + t, border=0, fill=True,
                               new_x="RIGHT", new_y="TOP", max_line_height=line_h)
                x += widths[i]
            self.set_draw_color(*LINE)
            self.set_line_width(0.25)
            self.rect(x0, y_start, w, rh)
            xx = x0
            for i in range(ncols - 1):
                xx += widths[i]
                self.line(xx, y_start, xx, y_start + rh)
            self.set_xy(x0, y_start + rh)
            alt = not alt
        self.ln(4)

    # ---- structure ------------------------------------------------------
    def cover(self):
        self.set_auto_page_break(False)
        self.add_page()
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, 215.9, 14, "F")
        self.set_y(34)
        self.set_x(self.l_margin)
        self.set_font(SANS, "", 12)
        self.set_text_color(*ACCENT_DARK)
        self.cell(0, 8, "K E S T R E L A T T I C E   ·   G O V E R N E D   A G E N T   M E S H")
        self.ln(18)
        self.set_font(SANS, "B", 30)
        self.set_text_color(*INK)
        self.multi_cell(0, 12.5, "The Governed\nAgent Mesh Playbook")
        self.ln(5)
        self.set_font(SANS, "B", 20)
        self.set_text_color(*ACCENT)
        self.cell(0, 10, "Studio Edition")
        self.ln(13)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.l_margin + 40, self.get_y())
        self.ln(9)
        self.set_font(SANS, "", 11.5)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 6.8,
            "The premium companion to the free playbook: fill-in policy templates, "
            "JSON schemas with validation rules, the priced vendor matrix, a 14-day "
            "rollout with acceptance criteria, and a first-customer kit.")
        self.ln(12)
        self.set_font(SANS, "", 10)
        self.set_text_color(*INK)
        self.cell(0, 6, "By GhostCorp  ·  September 2026")
        self.ln(6)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "Premium companion to the MIT-licensed free playbook.")
        self.set_y(-28)
        self.set_fill_color(*ACCENT)
        self.rect(0, 251.4, 215.9, 14, "F")
        self.set_y(268)
        self.set_x(self.l_margin)
        self.set_font(SANS, "", 9)
        self.set_text_color(*WHITE)
        self.cell(self.epw, 5, "koalstingkdelaney-gif.github.io/kestrelattice", align="C")
        self.set_auto_page_break(True, margin=20)

    def contents_page(self, toc):
        self.add_page()
        self.in_body = True
        self.set_font(SANS, "B", 16)
        self.set_text_color(*INK)
        self.cell(0, 10, "What's inside")
        self.ln(12)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.l_margin + 30, self.get_y())
        self.ln(7)
        for title in toc:
            self.set_font(SANS, "", 11)
            self.set_text_color(*INK)
            self.cell(0, 7.5, strip_md(title))
            self.ln(7.5)
        self.ln(5)
        self.set_font(SANS, "I", 9.5)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 5.8,
            "Every number in this edition traces to the two evidence files in the "
            "open-source repo. Bracketed [CAPS] are your inputs \u2014 fill them, name an "
            "owner, and the template is adopted.")

    def h2(self, text):
        if self.get_y() > self.page_break_trigger - 42:
            self.add_page()
        self.ln(7)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y(), self.l_margin + 34, self.get_y())
        self.ln(4)
        self.set_font(SANS, "B", 15)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(0, 7.5, strip_md(text))
        self.ln(2)

    def h3(self, text):
        if self.get_y() > self.page_break_trigger - 32:
            self.add_page()
        self.ln(3.5)
        self.set_font(SANS, "B", 11.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 6.2, strip_md(text))
        self.ln(1)

    def rule(self):
        self.ln(2)
        self.set_draw_color(*LINE)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + self.epw, y)
        self.ln(4)


def parse_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def is_sep_row(line):
    cells = parse_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)

def main():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    pdf = PDF()
    pdf.set_title("The Governed Agent Mesh Playbook — Studio Edition")
    pdf.set_author("GhostCorp")
    pdf.cover()

    toc = [ln[3:].strip() for ln in lines
           if ln.startswith("## ") and not ln.startswith("###")]
    pdf.contents_page(toc)

    i, n = 0, len(lines)
    in_code = False
    code_lines = []
    table_rows = []
    title_done = False
    while i < n:
        ln = lines[i]
        if ln.strip().startswith("```"):
            if in_code:
                pdf.code_block(code_lines)
                code_lines, in_code = [], False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(ln)
            i += 1
            continue
        s = ln.strip()
        if not s:
            if table_rows:
                pdf.md_table(table_rows)
                table_rows = []
            pdf.para("")
            i += 1
            continue
        if s.startswith("|"):
            if not is_sep_row(s):
                table_rows.append(parse_table_row(s))
            i += 1
            continue
        if table_rows:
            pdf.md_table(table_rows)
            table_rows = []
        if s.startswith("# ") and not title_done:
            title_done = True
        elif s.startswith("## "):
            pdf.h2(s[3:].strip())
        elif s.startswith("### "):
            pdf.h3(s[4:].strip())
        elif s == "---":
            pdf.rule()
        else:
            pdf.para(s)
        i += 1
    if table_rows:
        pdf.md_table(table_rows)

    pdf.output(OUT)
    print("pages:", pdf.page_no())
    print("wrote:", OUT)

if __name__ == "__main__":
    main()
