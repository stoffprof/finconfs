"""Parse the Holden Conference in Finance and Real Estate program page (holdenconference.org/program/).

Each paper has two discussants (empirical and theory); both go in `discussant`, "; "-separated.
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

DAY_RE = re.compile(r"^(Thursday|Friday|Saturday), (\w+ \d+)$")
SESS_RE = re.compile(r"^(.*?) \(Session Chair: (.*)\)$")
SLOT_RE = re.compile(r"^(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2}) —$")


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    for t in soup(["script", "style"]):
        t.decompose()
    lines = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").splitlines()]
    lines = [l for l in lines if l]
    rows, day_num, date, sess, title, chair, slot = [], 0, "", 0, "", "", None
    for i, l in enumerate(lines):
        m = DAY_RE.match(l)
        if m:
            day_num, date = day_num + 1, m.group(2)
            continue
        m = SESS_RE.match(l)
        if m:
            sess, title, chair = sess + 1, m.group(1), m.group(2)
            continue
        m = SLOT_RE.match(l)
        if m:
            slot = m.groups()
            continue
        if l.startswith("Authors:") and slot:
            disc = lines[i + 1].split(":", 1)[1] if lines[i + 1].startswith("Discussants") else ""
            disc = "; ".join(re.sub(r"\s*\(.*?\)", "", d.split("—")[-1]).strip() for d in disc.split(";"))
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                             session_title=title, chair=chair, session_start=slot[0], session_end=slot[1],
                             paper_title=lines[i - 1], authors=l.split(":", 1)[1].strip(),
                             presenter="", discussant=disc))
            slot = None
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
