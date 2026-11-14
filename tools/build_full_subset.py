#!/usr/bin/env python3
"""Build the data subset for the full run over spouse (P26) from the saved snapshot.

    python3 tools/build_full_subset.py

Reads the latest successful result of the full-p26-snapshot query (one
CONSTRUCT, one triple per line) and writes:

    data/full-p26/asserted.nt        every fetched triple except the subclass-of (P279)
                                     triples that lie on no path to a class named in an
                                     entry (too large for git; its checksum is recorded)
    data/full-p26/subclass-all.nt    every fetched P279 triple, for the full-hierarchy
                                     comparison on a sample
    data/full-p26/PROVENANCE.json    source, hashes, times and counts

No inference is done here: the only selection is which fetched P279 triples to
keep, by reachability of a named class. Standard library only.
"""
import collections
import hashlib
import json
import pathlib
import re

from build_subset import ROOT, latest, named_classes, source

P279 = "<http://www.wikidata.org/prop/direct/P279>"
LINE = re.compile(r'^(<[^>]*>) (<[^>]*>) (<[^>]*>|".*"(?:\^\^<[^>]*>|@[\w-]+)?) \.$')


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    doc = json.loads((ROOT / "entries" / "entries.json").read_text(encoding="utf-8"))
    body, meta = latest(ROOT / "results", "full-p26-snapshot", ".ttl")

    lines, subclass, by_predicate = [], set(), collections.Counter()
    with body.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            found = LINE.match(line)
            if not found:
                raise SystemExit(f"{body}:{number}: not one triple per line: {line[:120]}")
            by_predicate[found.group(2)] += 1
            if found.group(2) == P279:
                subclass.add(found.groups())
            else:
                lines.append(line)

    targets = named_classes(doc)
    reaches, grew = set(targets), True
    while grew:  # the classes from which a named class is reachable by P279
        new = {s for s, _, o in subclass if o in reaches} - reaches
        reaches |= new
        grew = bool(new)
    kept = {t for t in subclass if t[2] in reaches}

    out = ROOT / "data" / "full-p26"
    out.mkdir(parents=True, exist_ok=True)
    asserted = sorted(set(lines) | {" ".join(t) + " ." for t in kept})
    (out / "asserted.nt").write_text("".join(line + "\n" for line in asserted), encoding="utf-8")
    (out / "subclass-all.nt").write_text("".join(sorted(" ".join(t) + " .\n" for t in subclass)), encoding="utf-8")
    provenance = {
        "licence": "Data retrieved from Wikidata, public domain under CC0 1.0.",
        "built_by": "tools/build_full_subset.py",
        "as_of": meta["started_utc"],
        "source": source(body, meta),
        "counts": {"triples_fetched": sum(by_predicate.values()),
                   "by_predicate": dict(sorted(by_predicate.items())),
                   "subclass_triples_fetched": len(subclass), "subclass_triples_kept": len(kept),
                   "asserted": len(asserted)},
        "named_classes": sorted(targets),
        "subclass_selection": "A fetched P279 triple is kept when its object is a class named in an entry "
                              "or has a P279 path to one.",
        "files": {"asserted.nt": {"sha256": sha256(out / "asserted.nt"), "bytes": (out / "asserted.nt").stat().st_size,
                                  "in_git": False},
                  "subclass-all.nt": {"sha256": sha256(out / "subclass-all.nt"),
                                      "bytes": (out / "subclass-all.nt").stat().st_size, "in_git": True}},
    }
    (out / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"fetched {sum(by_predicate.values())}  subclass kept {len(kept)} of {len(subclass)}  asserted {len(asserted)}")


if __name__ == "__main__":
    main()
