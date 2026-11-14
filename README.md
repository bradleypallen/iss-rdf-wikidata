# Wikidata case study for implication-space semantics for RDF

Supplementary material for the Wikidata case study (spouse, P26) in Bradley P. Allen,
*Implication-Space Semantics for RDF*. Companion repositories:
[iss-rdf-lean](https://github.com/bradleypallen/iss-rdf-lean) (manuscript and Lean 4
formalization) and [iss-rdf-checks](https://github.com/bradleypallen/iss-rdf-checks)
(computational checks of the theorems).

**Status (14 November 2026):** a hand-sized example has been taken end to end: Wikidata's
own constraint checker consulted, a 65-triple subset selected, the pipeline run on it in
SPARQL on a local store, and the result checked against a direct computation from the
definition. The dated note is `notes/2026-11-14-hand-sized-example.md`. The entries in
`entries/entries.json` are still a draft. The full run over all spouse statements has not
been done.

## How this repository is kept

1. **Everything is dated.** Each query is a file in `queries/`. Each run saves the response
   as received, together with the time it was run, in `results/`. Wikidata's counts change
   daily, so any figure taken from here is a snapshot and must be cited with its timestamp.
2. **Data is kept with its provenance.** The subset the pipeline runs on is in `data/`, or
   can be regenerated from the saved queries; either way the query and run that produced
   each file are recorded.
3. **Entries are files.** The entries for spouse are written once, in `entries/`, in the
   form the pipeline reads. The listing in the paper is produced from those files.
4. **Archived at submission.** A tagged release will be deposited in an archive that issues
   a DOI, and the DOI recorded here and in `CITATION.cff`.

## Layout

```
queries/    one SPARQL query per .rq file, with its prefixes declared
results/    results/<query name>/<UTC timestamp>.json and .meta.json, one pair per run
data/       the subset the pipeline runs on, with its provenance
entries/    the entries, in the form the pipeline reads
pipeline/   the pipeline's SPARQL files, generated from entries/entries.json
tools/      run_query.py and run_api_check.py, the only ways Wikidata is queried;
            entries.py, make_pipeline.py, build_subset.py, run_pipeline.py,
            check_cons.py, checker_summary.py
notes/      dated notes of what was found
logs/       runs.jsonl and pipeline.jsonl, one line per run, failed runs included
```

## Running a query

Python 3.10 or later, standard library only.

```sh
export WDQS_USER_AGENT='<descriptive agent string with contact details>'
python3 tools/run_query.py queries/p26-constraints.rq
```

The Wikidata Query Service asks for a descriptive User-Agent with contact details. It is
read from the environment and is not written to any file. Each `.meta.json` holds the full
query text and its SHA-256, the endpoint, the start and end times in UTC, the HTTP status,
the row count and the SHA-256 of the response body, so a result can be checked against the
query that produced it even if the query file changes later.

## Licences

Code and queries: MIT (see `LICENSE`). Data retrieved from Wikidata, which is everything
under `results/` and `data/`, is in the public domain under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), as published by Wikidata.
