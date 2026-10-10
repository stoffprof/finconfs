# finconfs: does presentation timing affect conference awards?

Hypothesis: primacy and recency effects shape who wins best paper and best
discussant awards at finance conferences.

## Scope (first pass)

- Finance conferences held Oct 2024 – Oct 2026.
- Small conferences only: fewer than 15 papers on the program. Large association
  meetings (AFA, WFA, FMA Annual) are excluded; they have too many papers and
  their awards are mostly decided before the meeting.
- Keep only conferences that (a) give a best paper and/or best discussant award
  and (b) post a program with paper order.
- Finding conferences: SSRN FEN blocks automated access, so we snowball from
  the CVs of presenters and discussants on programs we already have.

## Data to collect

`data/conferences.csv`: one row per conference-year

| field | notes |
|---|---|
| conf_id | e.g. `fdu_2025` |
| name, year, start_date, end_date, location | |
| program_url, awards_url | source links |
| n_days, parallel_sessions (y/n) | |
| has_best_paper, has_best_discussant | |
| award_decision | `pre_conference` (committee reads submissions), `at_conference` (judges or attendees watch talks), or `unknown` |
| award_source | conference site / news item / CVs |

`data/presentations.csv`: one row per paper slot

| field | notes |
|---|---|
| conf_id, session_id, session_title | |
| day_num, session_start, session_end | session position in the conference |
| slot_in_session, n_slots_in_session | paper order within session |
| is_plenary | plenary or keynote vs. parallel |
| paper_title, presenter, coauthors | |
| discussant, discussant_affiliation | |
| won_best_paper, won_best_discussant | 0/1 |
| award_evidence | URL or CV mention |

From these we can build several position measures: overall order in the
conference, first or last day, first or last session of a day, and first or
last slot within a session.

## Identification notes

- Awards decided before the conference from submissions can't reflect
  presentation order. Order can still matter through organizers putting
  strong papers in prominent slots. These conferences serve as a placebo for
  conferences where awards are decided at the meeting.
- Best discussant awards are usually decided at the meeting, often by
  attendee vote, so they are the cleanest test.
- Controls: session fixed effects (for within-session order), plenary vs.
  parallel, presenter seniority and affiliation, and whether a session is
  dedicated to award finalists.
- Winners are often announced on the conference site or in school news. Use
  presenter and discussant CVs only when that fails.
