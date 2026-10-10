"""Parse FRA annual meeting program pages (fraconference.com/<year>-2/) into slot rows."""
import csv
import re
import sys

from bs4 import BeautifulSoup

FIELDS = ["conf_id", "day_num", "date", "session_num", "session_start", "session_end",
          "session_title", "chair", "slot_in_session", "n_slots_in_session", "paper_title",
          "authors", "presenter", "discussant"]

DAY_RE = re.compile(r"^(Saturday|Sunday|Friday|Monday),? (\w+ \d+)(?:st|nd|rd|th)?,? (\d{4})")
SESS_RE = re.compile(r"^([\d:.]+ [AP]M) to ([\d:.]+ [AP]M) Session (\d+)(.*)")


def parse(html_path, conf_id, year):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    for t in soup(["script", "style"]):
        t.decompose()
    lines = [l.strip() for l in soup.get_text("\n").splitlines() if l.strip()]
    start = next(i for i, l in enumerate(lines) if l.startswith("Program for the"))
    # older pages: the Discussant/Presenter line can be missing; guard index use below
    # page headers split "20\nth\nAnnual"; join short fragments is unnecessary for parsing below
    rows, day_num, date, sess, title = [], 0, None, None, None
    i = start
    while i < len(lines):
        l = lines[i]
        m = DAY_RE.match(l)
        if m:
            day_num += 1
            date = f"{m.group(2)}, {year}"  # FRA 2024 page misprints Sunday's year
        m = SESS_RE.match(l)
        if m:
            sess = dict(session_num=int(m.group(3)), session_start=m.group(1).replace(".", ":"),
                        session_end=m.group(2), chair="", session_title="")
            if "Early Ideas" in m.group(4) or lines[i + 1] == "Early Ideas Session":
                sess = None  # no discussants; short pitches
        if sess and l.startswith("Chairperson:"):
            sess["chair"] = l.split(":", 1)[1].strip()
        if sess and re.match(r"^Authors?:", l):
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, **sess,
                             paper_title=lines[i - 1], authors=l.split(":", 1)[1].strip(),
                             discussant=lines[i + 1].split(":", 1)[1].strip()
                             if lines[i + 1].startswith("Discussant") else ""))
            # at FRA the discussant presents the paper
            rows[-1]["presenter"] = rows[-1]["discussant"]
        i += 1
    for r in rows:
        same = [x for x in rows if x["session_num"] == r["session_num"]]
        r["n_slots_in_session"] = len(same)
        r["slot_in_session"] = same.index(r) + 1
    return rows


if __name__ == "__main__":
    html_path, conf_id, year, out = sys.argv[1:5]
    rows = parse(html_path, conf_id, year)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}")
