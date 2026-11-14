# Data

The subsets of Wikidata that the pipeline runs on. Wikidata's structured data is in the
public domain under CC0 1.0.

| Directory | What it is |
|---|---|
| `hand-sized/` | The hand-sized example: 65 triples about fourteen items, fetched 14 November 2026. `asserted.nt` is the pipeline's input, `labels.json` is for printing only, and `PROVENANCE.json` names the query runs it was built from, with hashes and times, and lists the triples left out. |
| `hand-sized-all-subclass/` | The same facts with every subclass-of triple above the items' classes (422 triples), for the comparison run that shows the smaller set loses nothing an entry reads. |

| `full-p26/` | The full run over spouse (P26), as of 14 November 2026, 17:51:57 UTC. `asserted.nt` (3,046,484 triples, 400 MB) is **not in git**; `PROVENANCE.json` gives its checksum and the query run it was built from. `subclass-all.nt` holds every subclass-of triple fetched, and `calibration-sample.json` the statements put to the constraint checker. |
| `sample-random/`, `sample-off-named/` and their `-all-subclass` twins | Two samples of 200 spouse parties from the full subset, each with the kept subclass-of triples and with all of them, for the comparison that justifies not materializing the full class hierarchy. |

The hand-sized pair is written by `tools/build_subset.py`, the full subset by
`tools/build_full_subset.py`, the samples by `tools/sample_hierarchy_check.py`. They are built from saved query results and are never edited by hand. Every file here must be traceable to the runs that produced it. A subset must be
closed for the entries: every triple that an entry's premises, defeaters or guards can read
is in it.
