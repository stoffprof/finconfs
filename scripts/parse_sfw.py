"""Parse Spring Finance Workshop program PDFs (pdftotext -layout output).

Layout: day header ("Sunday – April 21, 2024"), "SESSION I: TITLE", "Chair: ...", then per paper a
time + title line (title may wrap), "by ...", "Presenter: Name, Affil", "Discussant: Name, Affil".
"""
import re
import sys

from common import number_slots, write_rows

DAY_RE = re.compile(r"^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) [–-] (.*)$")
SESS_RE = re.compile(r"^SESSION ([IVX]+)\s*:\s*(.*)$")
TIME_RE = re.compile(r"^(\d{1,2}:\d{2} [ap]\.m\.)\s+(.*)$")


def parse(txt_path, conf_id):
    lines = [l.strip() for l in open(txt_path) if l.strip()]
    rows, day_num, date, sess, title, chair, cur = [], 0, "", 0, "", "", None
    for l in lines:
        m = DAY_RE.match(l)
        if m:
            day_num, date = day_num + 1, m.group(2)
            continue
        m = SESS_RE.match(l)
        if m:
            sess, title = sess + 1, m.group(2).strip()
            continue
        if l.startswith("Chair:"):
            chair = l.split(":", 1)[1].strip()
            continue
        m = TIME_RE.match(l)
        if m:
            cur = None if m.group(2).startswith("Break") else dict(
                conf_id=conf_id, day_num=day_num, date=date, session_num=sess, session_title=title,
                chair=chair, session_start=m.group(1), paper_title=m.group(2), authors="")
            continue
        if cur is None:
            continue
        if re.match(r"^[Bb]y ", l):
            cur["authors"] = l[3:].strip()
        elif l.startswith("Presenter:"):
            cur["presenter"] = l.split(":", 1)[1].split(",")[0].strip()
        elif l.startswith("Discussant:"):
            cur["discussant"] = re.sub(r"\s*\(.*", "", l.split(":", 1)[1]).split(",")[0].strip()
            cur["paper_title"] = re.sub(r"\s*\(Best Paper Award\)", "", cur["paper_title"])
            rows.append(cur)
            cur = None
        elif not cur["authors"]:
            cur["paper_title"] += " " + l  # wrapped title
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
