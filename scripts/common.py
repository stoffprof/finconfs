"""Shared helpers for building slot-level program files."""
import csv
import re

FIELDS = ["conf_id", "day_num", "date", "session_num", "session_start", "session_end",
          "session_title", "track", "chair", "slot_in_session", "n_slots_in_session",
          "paper_title", "authors", "presenter", "discussant"]


def number_slots(rows, key=("day_num", "session_num", "track")):
    """Fill slot_in_session and n_slots_in_session from row order within each session."""
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r.get(k, "") for k in key), []).append(r)
    for g in groups.values():
        for i, r in enumerate(g, 1):
            r["slot_in_session"], r["n_slots_in_session"] = i, len(g)
    return rows


def starred(authors):
    """Return names marked with a trailing * (presenter convention), stripping affiliations."""
    out = []
    for a in re.split(r",\s*(?![^()]*\))", authors):
        if "*" in a:
            out.append(re.sub(r"\s*\(.*?\)|\*", "", a).strip())
    return "; ".join(out)


def write_rows(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {path}")
