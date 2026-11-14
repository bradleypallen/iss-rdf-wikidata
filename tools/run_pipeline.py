#!/usr/bin/env python3
"""Run the pipeline in pipeline/*.rq over a data file, on a local Oxigraph store.

    python3 tools/run_pipeline.py data/hand-sized/asserted.nt

All reasoning is done by the SPARQL files; this script only loads the data,
runs the files in order, repeats the two materialization updates until they
add nothing, and writes down what the store then holds. Output goes to
results/pipeline/<data name>/<UTC timestamp>/:

    asserted.nt closure.nt defaults.nt default-closure.nt   the four named graphs
    *.json                                                   each SELECT's rows
    report.md                                                the per-instance report
    run.json                                                 inputs, hashes, counts, timings

and one line is appended to logs/pipeline.jsonl. Needs pyoxigraph.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import time

import pyoxigraph as ox

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
ENTRIES = ROOT / "entries" / "entries.json"
GRAPHS = "https://github.com/bradleypallen/iss-rdf-wikidata/graph/"
NAMES = ["asserted", "closure", "defaults", "default-closure"]
GENID = "/.well-known/genid/"
SKOLEM_BASE = "https://github.com/bradleypallen/iss-rdf-wikidata" + GENID
FORMATS = {".nt": ox.RdfFormat.N_TRIPLES, ".ttl": ox.RdfFormat.TURTLE}


def graph(name):
    return ox.NamedNode(GRAPHS + name)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def skolem(term):
    """Step 0: a blank node becomes an IRI. Wikidata's own unknown values already are IRIs."""
    return ox.NamedNode(SKOLEM_BASE + term.value) if isinstance(term, ox.BlankNode) else term


def triples_of(store, names):
    found = set()
    for name in names:
        for quad in store.quads_for_pattern(None, None, None, graph(name)):
            found.add((str(quad.subject), str(quad.predicate), str(quad.object)))
    return found


def rows(store, file_name):
    result = store.query((PIPELINE / file_name).read_text(encoding="utf-8"))
    names = [v.value for v in result.variables]
    # ?entry and ?defeater are labels the query itself binds; every other column is an RDF term.
    text = lambda n, t: None if t is None else (t.value if n in ("entry", "defeater") else str(t))
    return [{n: text(n, s[n]) for n in names} for s in result]


def fixpoint(store, file_name):
    update, rounds = (PIPELINE / file_name).read_text(encoding="utf-8"), 0
    while True:
        before = len(store)
        store.update(update)
        rounds += 1
        if len(store) == before:
            return rounds


# ---- the report: bookkeeping over what the SPARQL returned, no reasoning ----

def term_of(text, prefixes):
    if text.startswith("?"):
        return text
    prefix, local = text.split(":", 1)
    return f"<{prefixes[prefix]}{local}>"


def instantiate(triples, row, prefixes):
    out = []
    for triple in triples:
        out.append(tuple(row[t[1:]] if t.startswith("?") else term_of(t, prefixes) for t in triple))
    return out


def short(term, prefixes, labels):
    if term.startswith("<"):
        iri = term[1:-1]
        if GENID in iri:
            return "unknown value …" + iri[-6:]
        for prefix, base in sorted(prefixes.items(), key=lambda kv: -len(kv[1])):
            if iri.startswith(base):
                name = f"{prefix}:{iri[len(base):]}"
                label = labels.get(iri)
                return f"{name} ({label})" if label else name
        return iri
    return term.split("^^")[0].strip('"')


def show(triple, prefixes, labels):
    return " ".join(short(t, prefixes, labels) for t in triple)


def has_unknown(triples):
    return any(GENID in term for triple in triples for term in triple)


def key(row):
    return json.dumps(row, sort_keys=True)


def table(header, lines):
    if not lines:
        return "None.\n"
    return "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n" + "".join(
        "| " + " | ".join(line) + " |\n" for line in sorted(lines))


def report(doc, labels, k, selects):
    prefixes = doc["prefixes"]
    entries = {e["id"]: e for e in doc["entries"]}
    sh = lambda triples: "<br>".join(show(t, prefixes, labels) for t in triples)

    at_k = {key(r) for r in selects["2-incompatibilities"]}
    only_cons = [r for r in selects["4-recheck"] if key(r) not in at_k]
    conflicts = [(r["entry"], instantiate(entries[r["entry"]]["premises"], r, prefixes)) for r in only_cons]

    sections = {"known": {"clean": [], "conflict": [], "already": [], "defeated": [], "incompatible": []},
                "unknown": {"clean": [], "conflict": [], "already": [], "defeated": [], "incompatible": []}}
    counts = {}

    def put(kind, triples, line):
        group = "unknown" if has_unknown(triples) else "known"
        sections[group][kind].append(line)
        counts[f"{kind}/{group}"] = counts.get(f"{kind}/{group}", 0) + 1

    for row in selects["2-default-instances"]:
        entry = entries[row["entry"]]
        premises = instantiate(entry["premises"], row, prefixes)
        conclusion = instantiate([entry["conclusion"]], row, prefixes)[0]
        base = [row["entry"], sh(premises), sh([conclusion])]
        if conclusion in k:
            put("already", premises + [conclusion], base)
            continue
        hits = [(name, triples) for name, triples in conflicts if conclusion in triples]
        if hits:
            put("conflict", premises + [conclusion], base + ["<br>".join(f"{n}: {sh(t)}" for n, t in hits)])
        else:
            put("clean", premises + [conclusion], base)

    for row in selects["2-defeated"]:
        entry = entries[row["entry"]]
        premises = instantiate(entry["premises"], row, prefixes)
        conclusion = instantiate([entry["conclusion"]], row, prefixes)[0]
        defeater = instantiate(entry["defeaters"][int(row["defeater"]) - 1], row, prefixes)
        put("defeated", premises + [conclusion], [row["entry"], sh(premises), sh([conclusion]), sh(defeater)])

    for row in selects["2-incompatibilities"]:
        premises = instantiate(entries[row["entry"]]["premises"], row, prefixes)
        put("incompatible", premises, [row["entry"], sh(premises)])

    explained = {json.dumps(t) for _, triples in conflicts for t in triples if t not in k}
    drawn = {json.dumps(instantiate([entries[r["entry"]]["conclusion"]], r, prefixes)[0])
             for r in selects["2-default-instances"]}
    counts["conflicts over Cons not touching a default conclusion"] = sum(
        1 for _, triples in conflicts if all(t in k for t in triples))
    counts["conflict triples outside K that no default drew"] = len(explained - drawn)

    def part(group):
        s = sections[group]
        return (
            "#### Default conclusions not already in K: clean\n\n"
            + table(["Entry", "Premises", "Conclusion"], s["clean"])
            + "\n#### Default conclusions not already in K: in conflict\n\n"
            + table(["Entry", "Premises", "Conclusion", "Incompatibility that applies over Cons, and its premises"], s["conflict"])
            + "\n#### Defeated default instances\n\n"
            + table(["Entry", "Premises", "Conclusion not drawn", "Defeater triples in K"], s["defeated"])
            + "\n#### Incompatibilities at K\n\n"
            + table(["Entry", "Triples it applies to"], s["incompatible"])
            + "\n#### Default conclusions already in K\n\n"
            + table(["Entry", "Premises", "Conclusion"], s["already"]))

    text = ("### Instances with no unknown value\n\n" + part("known")
            + "\n### Instances with an unknown value (Skolem IRI)\n\n" + part("unknown"))
    return text, counts


def has_blank_nodes(path):
    with path.open("rb") as handle:
        return any(line.startswith(b"_:") or b" _:" in line for line in handle)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("data", type=pathlib.Path, help="the subset, N-Triples (.nt) or Turtle (.ttl)")
    ap.add_argument("--labels", type=pathlib.Path, help="JSON object from IRI to label, for the report only")
    ap.add_argument("--summary", action="store_true",
                    help="for a large subset: no per-instance tables and no spouse listings; counts only")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "results" / "pipeline")
    ap.add_argument("--log", type=pathlib.Path, default=ROOT / "logs" / "pipeline.jsonl")
    args = ap.parse_args()

    stale = subprocess.run([sys.executable, str(ROOT / "tools" / "make_pipeline.py"), "--check"],
                           capture_output=True, text=True)
    if stale.returncode != 0:
        sys.exit("pipeline/*.rq do not match entries/entries.json; run tools/make_pipeline.py\n" + stale.stdout)

    started = datetime.datetime.now(datetime.timezone.utc)
    clock = time.monotonic()
    timings, lap = {}, [time.monotonic()]

    def timed(name):
        timings[name] = round(time.monotonic() - lap[0], 3)
        lap[0] = time.monotonic()

    doc = json.loads(ENTRIES.read_text(encoding="utf-8"))
    labels = json.loads(args.labels.read_text(encoding="utf-8")) if args.labels else {}

    store = ox.Store()
    blank = 0
    if has_blank_nodes(args.data):  # step 0 proper: blank nodes become IRIs, one triple at a time
        for triple in ox.parse(path=str(args.data), format=FORMATS[args.data.suffix]):
            blank += isinstance(triple.subject, ox.BlankNode) + isinstance(triple.object, ox.BlankNode)
            store.add(ox.Quad(skolem(triple.subject), triple.predicate, skolem(triple.object), graph("asserted")))
    else:
        store.bulk_load(path=str(args.data), format=FORMATS[args.data.suffix], to_graph=graph("asserted"))
    timed("0-load")

    selects = {}
    rounds_1 = fixpoint(store, "1-closure.rq")
    timed("1-closure")
    store.bulk_extend(ox.Quad(t.subject, t.predicate, t.object, graph("defaults"))
                      for t in store.query((PIPELINE / "2-defaults.rq").read_text(encoding="utf-8")))
    timed("2-defaults")
    for name in ("2-defeated", "2-incompatibilities") + (() if args.summary else ("2-default-instances",)):
        selects[name] = rows(store, name + ".rq")
        timed(name)
    rounds_3 = fixpoint(store, "3-default-closure.rq")
    timed("3-default-closure")
    for name in ("4-recheck",) + (() if args.summary else ("q-spouse-of-at-closure", "q-spouse-of-at-cons")):
        selects[name] = rows(store, name + ".rq")
        timed(name)

    out = args.out / args.data.parent.name / started.strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=True)
    sizes, k, cons = {}, set(), set()
    for name in NAMES:
        triples = triples_of(store, [name])
        (out / f"{name}.nt").write_text("".join(sorted(" ".join(t) + " .\n" for t in triples)), encoding="utf-8")
        sizes[name] = len(triples)
        cons |= triples
        if name in NAMES[:2]:
            k |= triples
    k_size, cons_size = len(k), len(cons)
    for name, result in selects.items():
        (out / f"{name}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    timed("write-graphs")

    header = (f"## Pipeline run {started.isoformat(timespec='seconds')}\n\n"
              f"Data: `{relative(args.data)}` ({sizes['asserted']} triples). "
              f"K has {k_size} triples, D* has {sizes['defaults']}, Cons has {cons_size}.\n\n")
    counts = {}
    if args.summary:
        (out / "report.md").write_text(
            header + "Summary run: per-instance tables are not written for a subset of this size.\n", encoding="utf-8")
    else:
        body, counts = report(doc, labels, k, selects)
        new_answers = [r for r in selects["q-spouse-of-at-cons"] if r not in selects["q-spouse-of-at-closure"]]
        prefixes = doc["prefixes"]
        answers = table(["Who", "has as spouse"],
                        [[short(r["who"], prefixes, labels), short(r["spouse"], prefixes, labels)] for r in new_answers])
        (out / "report.md").write_text(
            header + body + "\n### Answers to \"who has whom as spouse\" that are in Cons and not in K\n\n" + answers,
            encoding="utf-8")
    del k, cons

    record = {
        "started_utc": started.isoformat(timespec="seconds"),
        "seconds": round(time.monotonic() - clock, 3),
        "seconds_per_step": timings,
        "summary_only": args.summary,
        "data_file": relative(args.data),
        "data_sha256": sha256(args.data),
        "entries_sha256": sha256(ENTRIES),
        "pipeline_sha256": {p.name: sha256(p) for p in sorted(PIPELINE.glob("*.rq"))},
        "store": f"pyoxigraph {ox.__version__}",
        "blank_nodes_skolemized": blank,
        "fixpoint_rounds": {"1-closure": rounds_1, "3-default-closure": rounds_3},
        "graph_sizes": sizes,
        "K": k_size,
        "Cons": cons_size,
        "select_rows": {name: len(result) for name, result in selects.items()},
        "instances": counts,
        "out_dir": relative(out),
    }
    (out / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    print(f"ok  {record['data_file']}  K={k_size}  D*={sizes['defaults']}  Cons={cons_size}  "
          f"incompatible at K={len(selects['2-incompatibilities'])}  over Cons={len(selects['4-recheck'])}  "
          f"{record['seconds']}s  -> {record['out_dir']}")


if __name__ == "__main__":
    main()
