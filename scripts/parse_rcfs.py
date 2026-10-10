"""Parse RCFS Winter Conference program PDFs (text from pdftotext -layout).

Sessions look like "Session N (8:00 a.m. to 9:30 a.m.)", papers like
"Title, by Presenter, Affiliation (joint with ...)" possibly wrapped over lines,
followed by an indented "Discussant: Name, Affiliation".
"""
import re
import sys

from common import number_slots, write_rows

SESS_RE = re.compile(r"^Session (\d+):? \(?([\d:]+ [ap]\.m\.) to ([\d:]+ [ap]\.m\.)\)?")
DAY_RE = re.compile(r"^(Saturday|Sunday), (\w+ \d+)$")
SKIP_RE = re.compile(r"^(Break|Lunch|Dinner|Breakfast|Refreshments|EARLY AFTERNOON|Allocated|Session Chair)")


def parse(txt_path, conf_id):
    lines = [l.rstrip() for l in open(txt_path) if l.strip()]
    rows, day_num, date, sess, title_buf, chair = [], 0, "", None, [], ""
    for l in lines:
        s = l.strip()
        m = DAY_RE.match(s)
        if m:
            day_num, date = day_num + 1, m.group(2)
            continue
        m = SESS_RE.match(s)
        if m:
            sess = dict(session_num=int(m.group(1)), session_start=m.group(2), session_end=m.group(3))
            title_buf, chair, sess_title_next = [], "", True
            continue
        if sess is None:
            continue
        if s.startswith("Session Chair:"):
            chair = s.split(":", 1)[1].strip()
            continue
        if SKIP_RE.match(s):
            title_buf = []
            continue
        if s.startswith("Discussant:"):
            entry = " ".join(title_buf)
            title_buf = []
            m = re.match(r"(.*?),? by (.*)", entry)
            if not m:
                continue
            title, rest = m.groups()
            presenter = re.split(r",", rest)[0].strip()
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, chair=chair,
                             session_title=sess.get("title", ""), paper_title=title.strip(),
                             authors=rest.strip(), presenter=presenter,
                             discussant=s.split(":", 1)[1].split(",")[0].strip(), **sess))
            continue
        if sess_title_next and not re.search(r",? by ", s):
            sess["title"] = s  # first line after the session header is its title
            sess_title_next = False
            continue
        sess_title_next = False
        title_buf.append(s)
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
