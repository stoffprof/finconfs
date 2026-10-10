"""Parse Utah Winter Finance Conference programs rendered from utahwfc.org/program (JS site;
saved with headless Chromium after clicking the year's tab)."""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

DAYS = ("Thursday", "Friday", "Saturday", "Sunday")
TIME_RE = re.compile(r"^(\d{1,2}:\d{2})–(\d{1,2}:\d{2} [AP]M)$")


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    for t in soup(["script", "style"]):
        t.decompose()
    lines = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").splitlines()]
    lines = [l for l in lines if l]
    start = next(i for i, l in enumerate(lines) if l == "Thursday")
    rows, day_num, date, sess, title, chair, times = [], 0, "", 0, "", "", ("", "")
    for i in range(start, len(lines)):
        l = lines[i]
        if l.startswith("Est. 1992"):
            break
        if l in DAYS:
            day_num, date = day_num + 1, lines[i + 1]
        m = TIME_RE.match(l)
        if m:
            times = m.groups()
        m = re.match(r"^Session ([IVX]+): (.*)$", l)
        if m:
            sess += 1
            title, chair = m.group(2), lines[i + 2] if lines[i + 1] == "Chair:" else ""
        if re.fullmatch(r"0\d", l) and lines[i + 3] == "Discussant":
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                             session_title=title, chair=chair, session_start=times[0],
                             session_end=times[1], paper_title=lines[i + 1], authors=lines[i + 2],
                             presenter="", discussant=re.sub(r"\s*\(.*", "", lines[i + 4])))
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
