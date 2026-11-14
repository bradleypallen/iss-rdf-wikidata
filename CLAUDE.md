# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of this repository

Public at `github.com/bradleypallen/iss-rdf-wikidata`. It is the supplementary material for
the paper's Wikidata case study, so everything committed here is published and will be
archived. As of 14 Nov 2026 it holds the layout, the query runner, twenty queries and one
dated run of each (five timed out; see `logs/runs.jsonl`), and a draft `entries/entries.json`.
There is no pipeline or data subset yet. There is no build and no test suite.

Brad's `WDQS_USER_AGENT` is set only in his own Terminal tab. Shells and tabs opened by
Claude do not have it, so write the query files, then give him one command to run there.
Counting anti-joins over all spouse triples (`FILTER NOT EXISTS`, `MINUS`) time out on the
query service at 60 s; a join that drives from a small class does not.

**Read `WIKIDATA-HANDOFF.md` first**; it is the specification for the work. It is a working
note, kept out of the public repository by `.gitignore`, so it exists only in this checkout.

## Commands

```sh
export WDQS_USER_AGENT='...'                           # ask Brad for the string; see below
python3 tools/run_query.py queries/p26-constraints.rq  # SELECT or ASK, saved as JSON
python3 tools/run_query.py queries/<name>.rq --format ttl          # CONSTRUCT
python3 tools/run_query.py queries/<name>.rq --endpoint <url>      # another store
python3 tools/entries.py check    # entries.json is well-formed; run after every edit to it
python3 tools/entries.py list     # print the entries from the file
```

Python 3.10 or later, standard library only. Each run writes
`results/<query name>/<UTC timestamp>.json` and `.meta.json` and appends a line to
`logs/runs.jsonl`; a failed run is recorded too and exits 1.

## Supplementary-material rules

These four rules come from Brad and decide where things go.

1. **Everything dated.** A query is run only from a file in `queries/` and only through
   `tools/run_query.py`; never paste a query into `curl` or a browser and report the number.
   Results are never edited or overwritten. Any count given to Brad carries the timestamp of
   its run, because the paper can only cite a snapshot.
2. **Data kept with its provenance.** The subset the pipeline runs on is committed in
   `data/`, or regenerable from saved queries, and each file is traceable to the run that
   produced it. Wikidata's data is CC0 1.0; the code and queries are MIT.
3. **Entries as files.** The spouse entries are written once in `entries/`, in the form the
   pipeline reads. The paper's listing is generated from those files; do not keep a second
   copy of an entry in prose, in code, or in a query. `entries/entries.json` is a draft:
   its format is a proposal and each entry's `choices` are Brad's to settle. When showing
   entries, print them with `tools/entries.py list`; do not retype them.
4. **A deposit at submission.** TGDK asks for a Supplementary Material Statement. Plan on a
   tagged release archived with a DOI, the DOI then recorded in `README.md` and
   `CITATION.cff`. Until then, keep the repository in a state that could be released.

## What the work is

A worked Wikidata example (spouse, P26) for B. P. Allen's paper *Implication-Space Semantics
for RDF*, extended to nonmonotone bases (TGDK special issue on rules and reasoning, deadline
14 December 2026). The example must show, on constraints Wikidata really publishes and using
only a triple store and plain SPARQL, that:

* a "violation" of a constraint with a conclusion is a default consequence;
* an exception defeats it;
* a conflict is located and does not destroy the graph's other consequences.

The paper claims a more principled formalization, not new capability or tooling. The example
therefore has to be exact about Wikidata and exact about which parts are the paper's own
stipulation.

Sibling folders, both outside this one:

* `../iss-rdf-lean` — the manuscript (`manuscript.tex`) and its Lean 4 formalization. A
  separate session works there; do not edit it from here. The companion `HANDOFF.md` that
  the Wikidata handoff refers to is at `../iss-rdf-lean/Claude outputs/handoff/HANDOFF.md`
  (sections 1 to 3 and 7 give the background).
* `../iss-rdf-checks` — the Python `issrdf` package and computational checks of the paper's
  theorems (monotone case).

## Working mode

* Brad writes the paper's prose himself. Do not draft paper text unless asked. Produce data,
  queries, tables, checks, and plain statements of what was found.
* No commits or pushes unless asked. A push here publishes.
* In every finding, separate what was **confirmed on live data** (with the date and time of
  the query), what comes **from documentation**, and what is a **guess**. Everything in the
  handoff about Wikidata came from documentation and is a list of things to confirm.
* The Wikidata Query Service asks for a descriptive User-Agent with contact details. Brad's
  email address is private: ask him what to put there; never fill it in yourself. The
  runner reads it from `WDQS_USER_AGENT` and does not store it. Keep it out of every
  committed file, including results, logs and commit messages.
* Note the rank handling in every count: `wdt:` triples are best-rank only, so a reverse
  statement at a non-best rank counts as missing.

## The base the example instantiates

A regime `R` plus single-conclusion entries `⟨A, c; E⟩`: premises `A`, conclusion `c` (a
triple, or ⊥ for an incompatibility entry), defeaters `E`, optional guards.

* `K = cl_R(Γ) \ {⊥}`.
* An entry instance applies when its premises are in `K` and no defeater instance is
  contained in `K`. A defeater's own variables are existential.
* `D*` = conclusions of the applying entries. **One round**: entries never see each other's
  conclusions.
* `Cons(Γ) = cl_R(K ∪ D*) \ {⊥}`.
* Γ is incoherent iff `R` derives ⊥ from Γ or an incompatibility entry applies at `K`.
* `Γ |~ Δ` iff `Δ ∩ Cons(Γ) ≠ ∅`, or `Δ = ∅` and Γ is incoherent. No explosion.

Restrictions on entries that shape every query written here:

* A conclusion is a single triple and introduces no new terms. A default cannot create a
  statement node, so it cannot produce qualifiers. Qualifiers may be read in premises,
  defeaters and guards. The example is therefore over direct ("truthy") triples.
* Guards must not depend on the identity of blank or Skolem terms. Comparisons on literals
  (dates) are fine.
* Any item an entry names (for example a listed exception) must be in the fixed vocabulary.

## The pipeline (named graphs)

| Stage | Action | Output graph |
|---|---|---|
| 0 | Skolemize the input | `:asserted` |
| 1 | Materialize under `R`; record ⊥-rule violations | `:closure` |
| 2 | One round of entries against `:asserted ∪ :closure` only: `CONSTRUCT` with `FILTER NOT EXISTS` for defaults, `SELECT` for incompatibilities | `:defaults` |
| 3 | Materialize again | `:default-closure` |
| 4 | Optional re-check for conflicts among defaults | — |

Stage 2 must never read `:defaults`; that is what "one round" means. Operationally this is a
three-stratum Datalog program with negation, and the paper says so first.

A data subset used for a run must be **closed for the entries**: every triple an entry's
premises, defeaters or guards can read is in it (spouse statements, birth and death dates,
instance-of and subclass-of as needed, and the constraint statements themselves if
exceptions are read from the graph).

## Open decisions (Brad's to make; do not settle them silently)

* How an exception becomes a defeater: a ground defeater naming the listed items, or a
  pattern over the published constraint statement (`wd:P26 p:P2302 ?c . ?c pq:P2303 ?item`).
* Whether to keep a third status, "coherent with conflicting defaults" (a conflict that
  appears over `Cons` but not over `K`). Non-overlapping lifetimes do not show it, because
  the contemporary check is not directional. It needs a constraint the asserted direction
  satisfies and the reverse violates; if P26 has none, it can only be shown with an entry of
  the paper's own, labelled as such.
* The mapping from Wikidata constraint types to entries (handoff section 4) is a proposal.
  Wikidata documents constraints as hints for editors; reading a symmetric-constraint
  violation as a default consequence is the paper's stipulation.

The questions the live data must answer are in handoff section 6, and the deliverables in
section 7.
