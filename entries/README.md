# Entries

`entries.json` holds the regime rules and the entries for the case study. It is a
**draft**: the file format is a proposal, and every item listed under an entry's `choices`
is undecided.

There is one source for each entry. The pipeline reads this file, and any listing is
printed from it, so the two cannot differ:

```sh
python3 tools/entries.py check   # well-formedness
python3 tools/entries.py list    # the entries as premises A, conclusion c, defeaters E
```

Each entry records its premises, conclusion, defeaters and guards, the Wikidata constraint
statement it comes from, the choices made in writing it, and the dated result files that
bear on it. Entries that share a `variant_of` value are alternatives, of which one is to be
kept. Constraints on P26 for which no entry is written are listed under `not_written`, with
the reason.
