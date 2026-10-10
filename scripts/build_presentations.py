"""Merge data/programs/*.csv with data/awards.csv into data/presentations.csv.

Adds, per slot: order_in_conf (1 = first paper of the meeting), n_in_conf, and award flags.
Paper awards match on normalized title; best_discussant matches on discussant surname.
"""
import csv
import difflib
import glob
import re
import unicodedata

from common import FIELDS


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def surname(name):
    return norm(name).split()[-1] if norm(name) else ""


def same_title(a, b):
    a, b = norm(a)[:60], norm(b)[:60]
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.85


awards = list(csv.DictReader(open("data/awards.csv")))
award_types = sorted({a["award"] for a in awards})
rows = []
for path in sorted(glob.glob("data/programs/*.csv")):
    prog = list(csv.DictReader(open(path)))
    for k, r in enumerate(prog, 1):  # program files are in presentation order
        r["order_in_conf"], r["n_in_conf"] = k, len(prog)
        mine = [a for a in awards if a["conf_id"] == r["conf_id"]]
        for t in award_types:
            hit = 0
            for a in mine:
                if a["award"] != t:
                    continue
                if t == "best_discussant":
                    discs = [surname(d) for d in r["discussant"].split(";")]
                    hit |= surname(a["winner"]) in discs
                elif r["paper_title"]:
                    hit |= same_title(a["paper_title"], r["paper_title"])
                else:  # program lists presenter only (no title): match on presenter surname
                    hit |= surname(r["presenter"]) in [surname(w) for w in a["winner"].split(";")]
            r[f"won_{t}"] = int(hit)
        rows.append(r)

# day_rank: 1 = first day with papers (some programs number a reception-only day)
for c in {r["conf_id"] for r in rows}:
    days = sorted({int(r["day_num"] or 0) for r in rows if r["conf_id"] == c})
    for r in rows:
        if r["conf_id"] == c:
            r["day_rank"] = days.index(int(r["day_num"] or 0)) + 1

out_fields = FIELDS + ["day_rank", "order_in_conf", "n_in_conf"] + [f"won_{t}" for t in award_types]
with open("data/presentations.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

# sanity check: every award should match exactly one slot (or be flagged)
expected = {}
for a in awards:
    k = (a["conf_id"], a["award"])
    expected[k] = expected.get(k, 0) + 1
for (c, t), n_exp in expected.items():
    if t.endswith("_poster"):  # poster awards have no program slot
        continue
    n = sum(r[f"won_{t}"] for r in rows if r["conf_id"] == c)
    if n != n_exp:
        print(f"WARNING {c} {t}: {n_exp} winner(s) listed, matched {n} slots")
# one row per conference-year
with open("data/conference_years.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["conf_id", "series", "year", "n_papers", "n_sessions", "n_days", "awards"])
    for c in sorted({r["conf_id"] for r in rows}):
        rs = [r for r in rows if r["conf_id"] == c]
        w.writerow([c, c.rsplit("_", 1)[0], c.rsplit("_", 1)[1], len(rs),
                    len({(r["day_num"], r["session_num"]) for r in rs}), len({r["day_num"] for r in rs}),
                    "; ".join(sorted({a["award"] for a in awards if a["conf_id"] == c}))])

print(f"{len(rows)} slots from {len({r['conf_id'] for r in rows})} conference-years -> data/presentations.csv")
