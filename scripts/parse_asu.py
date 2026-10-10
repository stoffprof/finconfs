"""Parse ASU Sonoran Winter Finance Conference program archives (finance-conference.wpcarey.asu.edu).

Sessions are "Session I".."Session V" (no times posted); each paper is a title line, an author
block in which the presenter is set apart (bold), and "Discussant: Name (Affil)".
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    bold = {re.sub(r"\s+", " ", b.get_text(" ", strip=True)) for b in soup.find_all(["strong", "b"])}
    for t in soup(["script", "style"]):
        t.decompose()
    lines = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").splitlines()]
    lines = [l for l in lines if l]
    rows, sess, chair, buf = [], 0, "", []
    for l in lines:
        m = re.match(r"^Session ([IVX]+)$", l)
        if m:
            sess, buf = ROMAN[m.group(1)], []
            continue
        if not sess:
            continue
        if l.startswith("Session Chair:"):
            chair = l.split(":", 1)[1].strip()
            continue
        if l.startswith("Discussant:"):
            title, authors = buf[0], " ".join(buf[1:]).replace(" ,", ",").replace("( ", "(")
            presenter = "; ".join(n for n in bold if n and n in authors and len(n.split()) >= 2)
            rows.append(dict(conf_id=conf_id, session_num=sess, chair=chair, paper_title=title,
                             authors=authors, presenter=presenter,
                             discussant=re.sub(r"\s*\(.*", "", l.split(":", 1)[1]).strip()))
            buf = []
            continue
        if l in ("Maps and Locations",):
            break
        buf.append(l)
    return number_slots(rows, key=("session_num",))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
