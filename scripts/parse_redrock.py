"""Parse BYU Red Rock Finance Conference program pages (marriott.byu.edu/event/redrock<YYYY>/presentations)."""
import re
import sys

from bs4 import BeautifulSoup

from common import number_slots, starred, write_rows


def parse(html_path, conf_id):
    soup = BeautifulSoup(open(html_path, "rb").read(), "lxml")
    main = soup.find(id="event-main-content")
    rows, day_num, date, sess = [], 0, "", 0
    for el in main.find_all(["h2", "h3", "li"]):
        txt = el.get_text(" ", strip=True)
        if el.name == "h2":
            day_num += 1
            date = txt
        elif el.name == "h3":
            m = re.search(r"Session (\d+)", txt)
            sess = int(m.group(1)) if m else sess + 1
        else:
            parts = [p.strip() for p in el.get_text("|").replace("\n", " ").split("|")]
            # rebuild lines split at <br/>
            lines = [BeautifulSoup(x, "lxml").get_text(" ", strip=True)
                     for x in re.split(r"<br\s*/?>", el.decode_contents())]
            lines = [re.sub(r"\s+", " ", l).replace(" ,", ",").replace("( ", "(").replace(" )", ")")
                     for l in lines if l.strip()]
            title, authors = lines[0], lines[1]
            disc = next((l.split(":", 1)[1].strip() for l in lines if l.startswith("Discussant")), "")
            rows.append(dict(conf_id=conf_id, day_num=day_num, date=date, session_num=sess,
                             paper_title=title, authors=authors.replace("*", "").strip(),
                             presenter=starred(authors), discussant=re.sub(r"\s*\(.*?\)", "", disc)))
    return number_slots(rows)


if __name__ == "__main__":
    write_rows(parse(sys.argv[1], sys.argv[2]), sys.argv[3])
