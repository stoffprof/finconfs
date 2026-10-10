"""Parse Colorado Finance Summit programs (coloradofinancesummit.com, Google Sites).

Regular papers: "Title - Author (Affil), ... Discussant: Name (Affil)" one per paragraph.
Job market session: one paragraph listing "Name (Affil) - Title" entries, no discussants.
Presenters are underlined or bold in the page.
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

DAY_RE = re.compile(r"^(Friday|Saturday|Sunday|Monday) ?, (\w+ \d+)")
TIME_RE = re.compile(r"^(\d{1,2}: ?\d{2} [ap]m) — (\d{1,2}:\s?\d\s?\d? ?[ap]m)")


def emphasized(p):
    out = []
    for sp in p.find_all("span", style=True):
        st = sp["style"].replace(" ", "")
        if "underline" in st or "font-weight:700" in st:
            t = sp.get_text(" ", strip=True)
            if t and t[0].isupper():
                out.append(t)
    return out


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    for t in soup(["script", "style"]):
        t.decompose()
    rows, day_num, date, sess, start, end, chair, title = [], 0, "", 0, "", "", "", ""
    seen_program = False
    for p in soup.find_all(["p", "h1", "h2", "h3"]):
        t = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
        if not t:
            continue
        if re.match(r"^20\d\d Program$", t):
            seen_program = True
        if not seen_program:
            continue
        m = DAY_RE.match(t)
        if m:
            day_num, date = day_num + 1, m.group(2)
            continue
        m = TIME_RE.match(t)
        if m:
            sess += 1
            start, end = m.group(1).replace(" ", ""), m.group(2).replace(" ", "")
            chair = t.split("Session Chair:", 1)[1].strip() if "Session Chair:" in t else ""
            title = "Job Market Session" if "Job Market" in t else ""
            continue
        if "Discussant:" in t and " - " in t:
            body, disc = t.rsplit("Discussant:", 1)
            ptitle, authors = body.split(" - ", 1)
            emph = [e for e in emphasized(p) if e in authors]
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                             session_start=start, session_end=end, chair=chair, session_title=title,
                             paper_title=ptitle.strip(), authors=authors.strip(),
                             presenter="; ".join(emph),
                             discussant=re.sub(r"\s*\(.*", "", disc).strip()))
        elif title == "Job Market Session" and " - " in t:
            names = [n for n in emphasized(p) if re.match(r"^[A-Z][\w.'\-]+( [A-Z][\w.'\-]+)+$", n)]
            pat = "|".join(re.escape(n) for n in names)
            parts = re.split(f"({pat})", t) if names else []
            for k in range(1, len(parts) - 1, 2):
                name, after = parts[k], parts[k + 1]
                m2 = re.match(r"\s*\(([^)]*)\)\s*-\s*(.*)", after)
                if not m2:
                    continue
                rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                                 session_start=start, session_end=end, chair=chair, session_title=title,
                                 paper_title=m2.group(2).strip(), authors=f"{name} ({m2.group(1).strip()})",
                                 presenter=name, discussant=""))
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
