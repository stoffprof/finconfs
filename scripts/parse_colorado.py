"""Parse Colorado Finance Summit programs (coloradofinancesummit.com, Google Sites), 2015-2025.

Formats vary by year:
  * session header: "7:05 am -- 8:30 am — Title" or "7:05 am — 8:30 am Session Chair: X"
  * paper: "Title , Author (Affil), ..." or "Title - Author (Affil) ..." with the discussant either in
    the same paragraph or the next one ("Discussant: Name (Affil)")
  * job market session: one paper per paragraph ("Title , Name (Affil)") or all in one paragraph
    ("Name (Affil) - Title Name (Affil) - Title ..."); no discussants.
Presenters are underlined or bold when marked at all.
"""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, write_rows

DAY_RE = re.compile(r"^(Thursday|Friday|Saturday|Sunday|Monday) ?, (\w+ \d+)")
TIME_RE = re.compile(r"^(\d{1,2}: ?\d{2} ?[ap]m) ?(?:—|--|-)+ ?(\d{1,2}: ?\d\s?\d? ?[ap]m)\s*(?:—|--)?\s*(.*)$")
NAME_AFF = r"[A-Z][^,()]*?\s*\([^)]*\)"
AUTHORS_TAIL = re.compile(rf"^(.*?)\s*,\s*((?:{NAME_AFF})(?:\s*(?:,|and)\s*{NAME_AFF})*)\s*$")


def emphasized(p):
    out = []
    for sp in p.find_all(["span", "b", "strong", "u"]):
        st = sp.get("style", "").replace(" ", "")
        if sp.name in ("b", "strong", "u") or "underline" in st or "font-weight:700" in st:
            t = re.sub(r"\s+", " ", sp.get_text(" ", strip=True)).strip(" ,")
            if t and t[0].isupper() and len(t.split()) <= 4:
                out.append(t)
    return out


def split_paper(text):
    """Return (title, authors) from 'Title - authors' or 'Title , Author (Affil), ...'."""
    m = AUTHORS_TAIL.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if " - " in text:
        t, a = text.split(" - ", 1)
        return t.strip(), a.strip()
    # no separator: authors are a trailing run of "First [M.] Last (Affil)"
    name = r"[A-Z][\w'\-]+(?: [A-Z]\.)? [A-Z][\w'\-]+ \([^)]*\)"
    m = re.match(rf"^(.*?)\s+({name}(?:\s*,?\s*(?:and\s+)?{name})*)\s*$", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text.strip(), ""


def presenters(authors, emph):
    names = [re.sub(r"\s*\(.*", "", n).strip() for n in re.split(r",\s*|\s+and\s+", authors)]
    return "; ".join(n for n in names if n and any(n == e or n in e for e in emph))


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    for t in soup(["script", "style"]):
        t.decompose()
    paras = []
    for p in soup.find_all(["p", "h1", "h2", "h3"]):
        t = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).replace(" ,", ",").replace("( ", "(").replace(" )", ")")
        if t:
            paras.append((t, emphasized(p)))
    start = max(i for i, (t, _) in enumerate(paras) if re.match(r"^20\d\d Program$", t))
    rows, day_num, date, sess, start_t, end_t, chair, jm, title = [], 0, "", 0, "", "", "", False, ""
    pending = None
    def flush():
        nonlocal pending
        if pending:
            rows.append(pending)
            pending = None

    for t, emph in paras[start + 1:]:
        if re.search(r"Conference Awards|Google Sites|Report abuse", t):
            break
        m = DAY_RE.match(t)
        if m or TIME_RE.match(t):
            flush()
        if m:
            day_num, date = day_num + 1, m.group(2)
            continue
        m = TIME_RE.match(t)
        if m and not re.search(r"Breakfast|Reception|Welcome|Introduction|Dinner", t):
            sess += 1
            start_t, end_t, rest = m.group(1).replace(" ", ""), m.group(2).replace(" ", ""), m.group(3)
            jm = "Job Market" in rest
            title = "Job Market Session" if jm else re.sub(r"Session Chair:.*", "", rest).strip(" :—-")
            chair = rest.split("Session Chair:", 1)[1].strip() if "Session Chair:" in rest else ""
            rest_after = re.sub(r"^.*?Session Chair:\s*[^)]*\)?\s*", "", rest) if jm else ""
            if jm and " - " in rest_after:
                t = rest_after  # job market entries in the header paragraph
            elif jm and re.search(NAME_AFF, rest_after):
                # names only, no titles (2022)
                for name, aff in re.findall(r"([A-Z][^()]*?)\s*\(([^)]*)\)", rest_after):
                    rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                                     session_start=start_t, session_end=end_t, chair=chair,
                                     session_title=title, discussant="", paper_title="",
                                     authors=f"{name.strip()} ({aff})", presenter=name.strip()))
                continue
            else:
                continue
        if re.match(r"^Session Chair\s*[:-]", t):
            chair = re.split(r"[:-]", t, 1)[1].strip()
            continue
        if re.match(r"^\d{1,2}: ?\d{2} ?[ap]m", t) or not sess:
            continue
        if t.startswith("Discussant:") and pending:
            pending["discussant"] = re.sub(r"\s*\(.*", "", t.split(":", 1)[1]).strip()
            rows.append(pending)
            pending = None
            continue
        base = dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess, session_start=start_t,
                    session_end=end_t, chair=chair, session_title=title, discussant="")
        if jm:
            if t.count(" - ") > 1 or re.match(rf"^{NAME_AFF}\s+-\s+", t):
                # "Name (Affil) - Title Name (Affil) - Title ..."
                names = [e for e in emph if re.match(r"^[A-Z][\w.'\-]+( [A-Z][\w.'\-]+)+$", e)]
                pat = "|".join(re.escape(n) for n in names) if names else r"[A-Z][\w.'\-]+ [A-Z][\w.'\-]+"
                parts = re.split(f"({pat})\\s*\\(([^)]*)\\)\\s*-\\s*", t)
                for k in range(1, len(parts) - 2, 3):
                    rows.append(dict(base, paper_title=parts[k + 2].strip(), presenter=parts[k],
                                     authors=f"{parts[k]} ({parts[k + 1]})"))
            else:
                ptitle, authors = split_paper(t)
                if authors:
                    rows.append(dict(base, paper_title=ptitle, authors=authors,
                                     presenter=presenters(authors, emph) or re.sub(r"\s*\(.*", "", authors.split(",")[0])))
            continue
        disc = ""
        if "Discussant:" in t:
            t, disc = t.rsplit("Discussant:", 1)
            disc = re.sub(r"\s*\(.*", "", disc).strip()
        ptitle, authors = split_paper(t.strip())
        if not authors:
            continue
        flush()
        row = dict(base, paper_title=ptitle, authors=authors, presenter=presenters(authors, emph), discussant=disc)
        if disc:
            rows.append(row)
        else:
            pending = row
    flush()
    return number_slots(rows, key=("day_num", "session_num"))


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
