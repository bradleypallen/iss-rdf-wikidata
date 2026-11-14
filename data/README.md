# Data

The subsets of Wikidata that the pipeline runs on. Wikidata's structured data is in the
public domain under CC0 1.0.

| Directory | What it is |
|---|---|
| `hand-sized/` | The hand-sized example: 65 triples about fourteen items, fetched 14 November 2026. `asserted.nt` is the pipeline's input, `labels.json` is for printing only, and `PROVENANCE.json` names the query runs it was built from, with hashes and times, and lists the triples left out. |
| `hand-sized-all-subclass/` | The same facts with every subclass-of triple above the items' classes (422 triples), for the comparison run that shows the smaller set loses nothing an entry reads. |

Both are written by `tools/build_subset.py` from saved query results and are never edited
by hand. Every file here must be traceable to the runs that produced it. A subset must be
closed for the entries: every triple that an entry's premises, defeaters or guards can read
is in it.
