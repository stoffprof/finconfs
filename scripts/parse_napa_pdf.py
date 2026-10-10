"""Parse older Napa conference PDF agendas (2014-2017, 2019).

Each paper is a title line ending in "(8:45 am - 9:30 am)" (2014-2017) or a time line followed by a
title (2019), then one author per line ("Name, Affil") or "A, Affil | B, Affil". Presenters are bold.
"""
import re
import sys

import pdfplumber

from common import number_slots, write_rows

TIME = r"(\d{1,2}:\d{2} ?[ap]m) ?[-–] ?(\d{1,2}:\d{2} ?[ap]m)"


def pdf_lines(path):
    """Yield (text, bold_spans) per visual line."""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(extra_attrs=["fontname"], keep_blank_chars=False, use_text_flow=True)
            lines = {}
            for w in words:
                lines.setdefault(round(w["top"]), []).append(w)
            for top in sorted(lines):
                ws = sorted(lines[top], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in ws)
                bold = " ".join(w["text"] for w in ws if "Bold" in w["fontname"] or "bold" in w["fontname"])
                yield text, bold


def parse(pdf_path, conf_id, year):
    rows, cur, pending_time = [], None, None
    stop = re.compile(r"^(LUNCHEON|Luncheon|Break|BREAK|\(Presenters|Cave Tour|Conference Dinner|Wine)")
    for text, bold in pdf_lines(pdf_path):
        m = re.search(rf"^(.*?)\s*\({TIME}\)\s*$", text)
        if m and m.group(1):                       # "Title (8:45 am - 9:30 am)"
            cur = dict(conf_id=conf_id, day_num=1, date=year, session_num=0, session_start=m.group(2),
                       session_end=m.group(3), paper_title=m.group(1).strip(), authors=[], presenter=[])
            rows.append(cur)
            continue
        m = re.match(rf"^{TIME}$", text)
        if m:                                      # 2019: time line, title on the next line
            pending_time, cur = m.groups(), None
            continue
        if pending_time and not cur:
            cur = dict(conf_id=conf_id, day_num=1, date=year, session_num=0, session_start=pending_time[0],
                       session_end=pending_time[1], paper_title=text.strip(), authors=[], presenter=[])
            rows.append(cur)
            pending_time = None
            continue
        if cur is None or stop.match(text) or re.search(TIME, text):
            if stop.match(text) or re.search(TIME, text):
                cur = None
            continue
        if "," in text or "|" in text:
            cur["authors"].append(text)
            for name in re.split(r"\s*\|\s*|\s+and\s+", bold):
                name = re.sub(r",.*", "", name).strip()
                if len(name.split()) >= 2:
                    cur["presenter"].append(name)
        elif not cur["authors"]:
            cur["paper_title"] += " " + text.strip()  # wrapped title
    rows = [r for r in rows if not re.match(r"^(BREAK|Break|LUNCH|Luncheon)", r["paper_title"])]
    for r in rows:
        t = re.sub(r"^Best Paper Award Winner\s*", "", r["paper_title"])
        if t.count(".") > 2 and " " not in t.strip():
            t = t.replace(".", " ")             # 2017 PDF encodes spaces as dots
        r["paper_title"] = t.replace("¿", "?").strip()
        r["authors"] = re.sub(r"\s*\|\s*", "; ", "; ".join(r["authors"]))
        r["presenter"] = "; ".join(n for n in dict.fromkeys(r["presenter"])
                                   if not re.search(r"University|School|College|Institute", n))
    return number_slots(rows)


if __name__ == "__main__":
    write_rows(parse(*sys.argv[1:4]), sys.argv[4])
