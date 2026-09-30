#!/usr/bin/env python3
"""Generalized builder: render any Kestrelattice product manuscript -> polished PDF (Letter).
Usage: build_product_pdf.py <src.md> <out.pdf> <title> <subtitle> <description> <footer_label>
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/kestrelattice")
from build_pdf import (PDF, parse_table_row, is_sep_row, strip_md,
                       SANS, INK, MUTED, WHITE, ACCENT, ACCENT_DARK)


class ProductPDF(PDF):
    def __init__(self, title, subtitle, description, footer_label):
        self.ptitle = title
        self.psubtitle = subtitle
        self.pdesc = description
        self.footer_label = footer_label
        super().__init__()

    def footer(self):
        if not self.in_body or self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font(SANS, "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, "Kestrelattice  ·  " + self.footer_label, align="L")
        self.set_xy(-30, -15)
        self.cell(20, 5, str(self.page_no()), align="R")

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
        self.set_font(SANS, "B", 28)
        self.set_text_color(*INK)
        self.multi_cell(0, 12, self.ptitle)
        self.ln(5)
        self.set_font(SANS, "B", 20)
        self.set_text_color(*ACCENT)
        self.cell(0, 10, self.psubtitle)
        self.ln(13)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.l_margin + 40, self.get_y())
        self.ln(9)
        self.set_font(SANS, "", 11.5)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 6.8, self.pdesc)
        self.ln(12)
        self.set_font(SANS, "", 10)
        self.set_text_color(*INK)
        self.cell(0, 6, "By GhostCorp  ·  September 2026")
        self.ln(6)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "Companion to the MIT-licensed free playbook.")
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
            "Companion to The Governed Agent Mesh Playbook — Studio Edition. "
            "Bracketed [CAPS] are your inputs — fill them, name an owner, and the "
            "template is adopted.")


def main():
    src, out, title, subtitle, description, footer_label = sys.argv[1:7]
    lines = open(src, encoding="utf-8").read().split("\n")
    pdf = ProductPDF(title, subtitle, description, footer_label)
    pdf.set_title("Kestrelattice — " + title)
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

    pdf.output(out)
    print("pages:", pdf.page_no())
    print("wrote:", out)


if __name__ == "__main__":
    main()
