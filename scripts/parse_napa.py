"""Parse UC Davis-FMA Napa Finance Conference programs (fma.org pages, 2018-2026).

One-day, single-track, no discussants. Each slot is a time range, a title line, optional notes in
parentheses (journal status, "(Best Paper Award ...)"), then author lines "Name, Affil | ...".
Presenters are in bold (later years) or starred (2018).
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

TIME_RE = re.compile(r"^(\d{1,2}:\d{2} [ap]m) ?[-–] ?(\d{1,2}:\d{2} [ap]m)$")


def clean_lines(soup):
    raw = [re.sub(r"\s+", " ", l).strip() for l in soup.get_text("\n").splitlines()]
    raw = [l for l in raw if l and l != "*"]
    out, depth = [], 0
    for l in raw:
        if depth or l == "(" or (l.startswith("(") and ")" not in l):
            depth += l.count("(") - l.count(")")
            continue
        if re.fullmatch(r"\(.*\)", l):  # one-line note such as "(Best Paper Award Co-winner)"
            continue
        if out and (re.match(r"^- ?\d{1,2}:\d{2}", l) or out[-1].endswith("-") and not re.search(r"\d$", out[-1])):
            out[-1] = (out[-1] + (" " if l.startswith("-") else "") + l).replace("- -", "-")
            continue
        out.append(l)
    return out


def parse(html_path, conf_id, date):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    bold = {re.sub(r",.*", "", b.get_text(" ", strip=True)).strip(" *")
            for b in soup.find_all(["strong", "b"]) if "," in b.get_text()}
    for t in soup(["script", "style"]):
        t.decompose()
    lines = clean_lines(soup)
    idx = [i for i, l in enumerate(lines) if TIME_RE.match(l)]
    rows = []
    for k, i in enumerate(idx):
        stop = idx[k + 1] if k + 1 < len(idx) else len(lines)
        block = []
        for l in lines[i + 1:stop]:
            if re.match(r"^(Break|Luncheon|Lunch|Cave Tour|Private Tour|Conference Dinner|_+|Presenting authors|\(\* Presenter\))", l) or l.startswith(","):
                break
            block.append(l)
        if not block:
            continue
        looks_like_authors = lambda s: bool(re.search(r"\w, [A-Z][\w&.' -]+(\||$)", s)) and ("|" in s or "University" in s)
        if looks_like_authors(block[0]) and not looks_like_authors(block[1] if len(block) > 1 else ""):
            title, auth = "", block            # title missing on the page
        else:
            title, auth = block[0], block[1:]
        authors = re.sub(r"\s*\|+\s*", "; ", " ".join(auth)).strip("; ")
        names = [re.sub(r",.*", "", a).strip() for a in authors.split("; ")]
        pres = [n.strip("* ") for n in names if n.endswith("*") or n.strip("* ") in bold]
        if not pres and len(names) == 1:
            pres = names
        rows.append(dict(conf_id=conf_id, day_num=1, date=date, session_num=0,
                         session_start=TIME_RE.match(lines[i]).group(1),
                         session_end=TIME_RE.match(lines[i]).group(2), paper_title=title,
                         authors=authors.replace("*", ""), presenter="; ".join(pres)))
    # treat the whole day as one session so slot = order of the day
    return number_slots(rows)


if __name__ == "__main__":
    write_rows(parse(*sys.argv[1:4]), sys.argv[4])
