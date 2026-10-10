"""Parse UC Davis-FMA Napa Finance Conference program (fma.org/<year>-...-napa-conference).

One-day, single-track, no discussants. Presenting authors are in bold.
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

TIME_RE = re.compile(r"^(\d{1,2}:\d{2} [ap]m) [-–] (\d{1,2}:\d{2} [ap]m)$")


def parse(html_path, conf_id, date):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    bold = {re.sub(r",.*", "", b.get_text(" ", strip=True)).strip()
            for b in soup.find_all(["strong", "b"]) if "," in b.get_text()}
    lines = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").splitlines()]
    lines = [l for l in lines if l.strip("* ")]
    start = next(i for i, l in enumerate(lines) if "Conference Program" in l)
    end = next(i for i, l in enumerate(lines) if i > start and "Presenting authors" in l)
    rows, i = [], start
    while i < end:
        m = TIME_RE.match(lines[i].strip("* "))
        if m and i + 2 < end and not TIME_RE.match(lines[i + 2].strip("* ")):
            title = lines[i + 1].strip("* ")
            if title in ("Break", "Luncheon") or "Tour" in title:
                i += 1
                continue
            j, auth = i + 2, []
            while j < end and not TIME_RE.match(lines[j].strip("* ")):
                if "Best Paper Award Winner" not in lines[j]:
                    auth.append(lines[j])
                j += 1
            authors = " ".join(auth)
            authors = re.sub(r"\s*\|+\s*", "; ", authors).strip("; ")
            presenter = "; ".join(n for n in (re.sub(r",.*", "", a).strip()
                                              for a in authors.split("; ")) if n in bold)
            rows.append(dict(conf_id=conf_id, day_num=1, date=date, session_num=0,
                             session_start=m.group(1), session_end=m.group(2),
                             paper_title=title, authors=authors, presenter=presenter))
            i = j
        else:
            i += 1
    # treat the whole day as one session so slot = order of the day
    return number_slots(rows)


if __name__ == "__main__":
    write_rows(parse(*sys.argv[1:4]), sys.argv[4])
