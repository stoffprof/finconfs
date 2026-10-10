"""Parse Jackson Hole Finance Group Conference programs (jhfinance.web.unc.edu/<year>-2/).

Single track, no discussants. Each paper is a title followed by "by A, B, and C"; the presenter is
set in bold. Sessions are "Session I: Topic" with a time range on the preceding line.
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows



def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    bold = {re.sub(r"\s+", " ", b.get_text(" ", strip=True)).strip(" ,")
            for b in soup.find_all(["strong", "b"])}
    for t in soup(["script", "style"]):
        t.decompose()
    content = soup.find("article") or soup
    paras = [re.sub(r"\s+", " ", p.get_text(" ", strip=True)) for p in content.find_all(["p", "h2", "h3", "h4"])]
    rows, day_num, date, sess, title, chair, times = [], 0, "", 0, "", "", ("", "")
    for p in paras:
        m = re.match(r"^(Friday|Saturday|Sunday|Monday|Thursday), (\w+ \d+)", p)
        if m:
            day_num, date = day_num + 1, m.group(2)
        m = re.search(r"(?:(\d{1,2}:\d{2} [ap]\.m\.) [–-] (\d{1,2}:\d{2} [ap]\.m\.) )?Session ([IVX]+): (.*?)(?: Session Chair: (.*))?$", p)
        if m and not re.search(r"\sby\s", p):
            sess, title = sess + 1, m.group(4).strip()
            times = (m.group(1) or "", m.group(2) or "")
            chair = (m.group(5) or "").strip()
            continue
        if p.startswith("Session Chair:"):
            chair = p.split(":", 1)[1].strip()
            continue
        m = re.match(r"^(.*?)\s+by\s+(.*)$", p)
        if m and sess and not re.match(r"^\d{1,2}:\d{2}", p):
            ptitle, authors = m.groups()
            names = [n.strip() for n in re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+", authors) if n.strip()]
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                             session_title=title, chair=chair, session_start=times[0],
                             session_end=times[1], paper_title=ptitle.strip(), authors="; ".join(names),
                             presenter="; ".join(n for n in names if n in bold), discussant=""))
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
