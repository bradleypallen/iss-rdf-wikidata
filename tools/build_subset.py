#!/usr/bin/env python3
"""Build the data subset for the hand-sized example from saved query results.

    python3 tools/build_subset.py

Reads the latest successful result of four saved queries:

    hand-sized-facts            (CONSTRUCT, Turtle)   the facts about the chosen items
    hand-sized-subclass-paths   (CONSTRUCT, Turtle)   every P279 triple above their classes
    hand-sized-labels           (CONSTRUCT, Turtle)   labels, for printing only
    hand-sized-touching-edges   (SELECT, JSON)        to list what the subset leaves out

and writes:

    data/hand-sized/asserted.nt                the facts, with the P279 triples that lie on
                                               a path to a class named in an entry
    data/hand-sized-all-subclass/asserted.nt   the facts, with every P279 triple fetched
    data/hand-sized/labels.json
    data/hand-sized/PROVENANCE.json            sources with hashes and times, counts,
                                               the named classes, the triples left out

No inference is done here: the only selection is which fetched P279 triples to
keep, by reachability of a named class. Needs pyoxigraph to read Turtle.
"""
import argparse
import hashlib
import json
import pathlib

import pyoxigraph as ox

ROOT = pathlib.Path(__file__).resolve().parent.parent
P279 = "<http://www.wikidata.org/prop/direct/P279>"
LABEL = "<http://www.w3.org/2000/01/rdf-schema#label>"


def latest(results, name, suffix):
    """The newest result body of a query whose run succeeded, with its metadata."""
    for meta_path in sorted((results / name).glob("*.meta.json"), reverse=True):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        body = pathlib.Path(str(meta_path).removesuffix(".meta.json") + suffix)
        if meta["ok"] and body.exists():
            return body, meta
    raise SystemExit(f"no successful {suffix} result for {name}; run the query first")


def source(body, meta):
    return {"query_file": meta["query_file"], "query_sha256": meta["query_sha256"],
            "result_file": str(body.relative_to(ROOT)) if body.is_relative_to(ROOT) else str(body),
            "result_sha256": hashlib.sha256(body.read_bytes()).hexdigest(),
            "run_started_utc": meta["started_utc"], "endpoint": meta["endpoint"]}


def turtle(path):
    return {(str(t.subject), str(t.predicate), str(t.object))
            for t in ox.parse(path=str(path), format=ox.RdfFormat.TURTLE)}


def named_classes(doc):
    """The classes an entry tests instance-of against: these decide which P279 triples matter."""
    iri = lambda term: f"<{doc['prefixes'][term.split(':', 1)[0]]}{term.split(':', 1)[1]}>"
    found = set()
    for entry in doc["entries"]:
        for triples in [entry["premises"]] + entry.get("defeaters", []):
            for s, p, o in triples:
                if p == "wdt:P31":
                    found |= {iri(v) for v in entry.get("expand", {}).get(o, [])} if o.startswith("?") else {iri(o)}
    return found


def write_nt(path, triples):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(sorted(" ".join(t) + " .\n" for t in triples)), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=pathlib.Path, default=ROOT / "results")
    ap.add_argument("--data", type=pathlib.Path, default=ROOT / "data")
    args = ap.parse_args()
    doc = json.loads((ROOT / "entries" / "entries.json").read_text(encoding="utf-8"))

    facts_body, facts_meta = latest(args.results, "hand-sized-facts", ".ttl")
    paths_body, paths_meta = latest(args.results, "hand-sized-subclass-paths", ".ttl")
    labels_body, labels_meta = latest(args.results, "hand-sized-labels", ".ttl")
    edges_body, edges_meta = latest(args.results, "hand-sized-touching-edges", ".json")

    facts = turtle(facts_body)
    subclass = {t for t in turtle(paths_body) if t[1] == P279}

    targets = named_classes(doc)
    reaches, grew = set(targets), True
    while grew:  # the classes from which a named class is reachable by P279
        new = {m for m, _, n in subclass if n in reaches} - reaches
        reaches |= new
        grew = bool(new)
    kept = {t for t in subclass if t[2] in reaches}

    labels = {}
    for triple in ox.parse(path=str(labels_body), format=ox.RdfFormat.TURTLE):
        if str(triple.predicate) == LABEL:
            iri, language = triple.subject.value, triple.object.language
            if language == "en" or iri not in labels:
                labels[iri] = triple.object.value

    touching = json.loads(edges_body.read_text(encoding="utf-8"))["results"]["bindings"]
    left_out = sorted(
        {(f"<{b['s']['value']}>", f"<{b['p']['value']}>", f"<{b['o']['value']}>") for b in touching} - facts)

    small, full = args.data / "hand-sized", args.data / "hand-sized-all-subclass"
    write_nt(small / "asserted.nt", facts | kept)
    write_nt(full / "asserted.nt", facts | subclass)
    (small / "labels.json").write_text(
        json.dumps(dict(sorted(labels.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance = {
        "licence": "Data retrieved from Wikidata, public domain under CC0 1.0.",
        "built_by": "tools/build_subset.py",
        "sources": {"facts": source(facts_body, facts_meta), "subclass_paths": source(paths_body, paths_meta),
                    "labels": source(labels_body, labels_meta), "touching_edges": source(edges_body, edges_meta)},
        "counts": {"facts": len(facts), "subclass_triples_fetched": len(subclass),
                   "subclass_triples_kept": len(kept), "asserted": len(facts | kept),
                   "asserted_all_subclass": len(facts | subclass), "labels": len(labels),
                   "spouse_or_border_triples_left_out": len(left_out)},
        "named_classes": sorted(targets),
        "subclass_selection": "A fetched P279 triple is kept when its object is a class named in an entry "
                              "or has a P279 path to one. data/hand-sized-all-subclass keeps all of them.",
        "left_out": [" ".join(t) for t in left_out],
    }
    (small / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    print(f"facts {len(facts)}  subclass kept {len(kept)} of {len(subclass)}  asserted {len(facts | kept)}  "
          f"all-subclass {len(facts | subclass)}  labels {len(labels)}  left out {len(left_out)}")


if __name__ == "__main__":
    main()
