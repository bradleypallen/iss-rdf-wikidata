#!/usr/bin/env python3
"""Compute K, D*, Cons and the incompatibilities straight from the definition,
and compare them with what a pipeline run wrote.

    python3 tools/check_cons.py data/hand-sized/asserted.nt results/pipeline/hand-sized/<timestamp>

Shares nothing with the SPARQL side: no SPARQL, no store, no import from the
other tools. It reads entries/entries.json and N-Triples files with its own
few lines. The definition (terms of the input read as constants):

    K        = cl_R(G) without BOT
    an entry instance applies at X when its premises are in X, its guards hold,
             and no defeater has an instance contained in X
    D*       = the conclusions of the default entries that apply at K
    Cons     = cl_R(K with D*) without BOT
    G is incoherent when an incompatibility entry applies at K

Writes check.json into the run directory. Exits 1 on any disagreement.
Standard library only.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE = re.compile(r'^(<[^>]*>|_:\S+)\s+(<[^>]*>)\s+(<[^>]*>|_:\S+|".*"(?:\^\^<[^>]*>|@[\w-]+)?)\s*\.\s*$')
DATE = re.compile(r'^"(-?)(\d+)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z"\^\^<http://www.w3.org/2001/XMLSchema#dateTime>$')


def read_nt(path):
    triples = set()
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            triples.add(LINE.match(line).groups())
    return triples


def ground(term, prefixes):
    if term.startswith("?"):
        return term
    prefix, local = term.split(":", 1)
    return f"<{prefixes[prefix]}{local}>"


def matches(patterns, graph, binding):
    """Every extension of binding that sends all patterns into graph."""
    if not patterns:
        yield binding
        return
    for triple in graph:
        new = dict(binding)
        for want, have in zip(patterns[0], triple):
            if want.startswith("?"):
                if new.setdefault(want, have) != have:
                    break
            elif want != have:
                break
        else:
            yield from matches(patterns[1:], graph, new)


def closure(graph, rules):
    graph = set(graph)
    while True:
        new = {tuple(b[t] if t.startswith("?") else t for t in rule["conclusion"])
               for rule in rules for b in matches(rule["premises"], graph, {})} - graph
        if not new:
            return graph
        graph |= new


def date(literal):
    found = DATE.match(literal)
    if not found:
        return None
    sign, *parts = found.groups()
    year, *rest = (int(p) for p in parts)
    return (-year if sign else year, *rest)


def holds(guard, binding):
    """A comparison holds only between two dates; anything else (an unknown value, say) fails it."""
    left, right = date(binding[guard["left"]]), date(binding[guard["right"]])
    if left is None or right is None:
        return False
    return {"<": left < right, ">": left > right}[guard["op"]]


def applying(entry, graph):
    """The bindings of the premise variables at which the entry applies at graph."""
    starts = [{}]
    for var, values in entry.get("expand", {}).items():
        starts = [{**s, var: value} for s in starts for value in values]
    for start in starts:
        for binding in matches(entry["premises"], graph, start):
            if all(holds(g, binding) for g in entry.get("guards", [])) and not any(
                    next(matches(d, graph, binding), None) is not None for d in entry.get("defeaters", [])):
                yield binding


def instances(entries, graph):
    return {(e["id"], tuple(sorted(b.items()))) for e in entries for b in applying(e, graph)}


def rows_as_instances(path):
    found = set()
    for row in json.loads(pathlib.Path(path).read_text(encoding="utf-8")):
        found.add((row["entry"], tuple(sorted(("?" + k, v) for k, v in row.items() if k != "entry" and v is not None))))
    return found


def main():
    data, run = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    doc = json.loads((ROOT / "entries" / "entries.json").read_text(encoding="utf-8"))
    g = lambda triples: [tuple(ground(t, doc["prefixes"]) for t in triple) for triple in triples]
    rules = [{"premises": g(r["premises"]), "conclusion": g([r["conclusion"]])[0]} for r in doc["regime"]["rules"]]
    entries = []
    for e in doc["entries"]:
        entries.append({
            "id": e["id"], "kind": e["kind"], "premises": g(e["premises"]), "guards": e.get("guards", []),
            "conclusion": None if e["conclusion"] == "BOT" else g([e["conclusion"]])[0],
            "defeaters": [g(d) for d in e.get("defeaters", [])],
            "expand": {v: [ground(x, doc["prefixes"]) for x in xs] for v, xs in e.get("expand", {}).items()},
        })
    defaults = [e for e in entries if e["kind"] == "default"]
    incompatibilities = [e for e in entries if e["kind"] == "incompatibility"]

    gamma = read_nt(data)
    blank = any(t.startswith("_:") for triple in gamma for t in triple)
    if blank:  # the pipeline Skolemizes blank nodes; start from what it loaded
        gamma = read_nt(run / "asserted.nt")
    k = closure(gamma, rules)
    d_star = {tuple(b[t] if t.startswith("?") else t for t in e["conclusion"])
              for e in defaults for b in applying(e, k)}
    cons = closure(k | d_star, rules)
    mine = {"K": k, "D*": d_star, "Cons": cons,
            "incompatibilities at K": instances(incompatibilities, k),
            "incompatibilities over Cons": instances(incompatibilities, cons)}

    nt = lambda *names: set().union(*(read_nt(run / f"{n}.nt") for n in names))
    theirs = {"K": nt("asserted", "closure"), "D*": nt("defaults"),
              "Cons": nt("asserted", "closure", "defaults", "default-closure"),
              "incompatibilities at K": rows_as_instances(run / "2-incompatibilities.json"),
              "incompatibilities over Cons": rows_as_instances(run / "4-recheck.json")}

    result, agree = {}, True
    for name in mine:
        only_definition, only_pipeline = mine[name] - theirs[name], theirs[name] - mine[name]
        same = not only_definition and not only_pipeline
        agree = agree and same
        result[name] = {"definition": len(mine[name]), "pipeline": len(theirs[name]), "agree": same,
                        "only_definition": sorted(map(str, only_definition)),
                        "only_pipeline": sorted(map(str, only_pipeline))}
        print(f"{'agree   ' if same else 'DISAGREE'}  {name}: definition {len(mine[name])}, pipeline {len(theirs[name])}")
    result["incoherent at K"] = bool(mine["incompatibilities at K"])
    result["asserted is the data file"] = "not compared: blank nodes were Skolemized" if blank else (
        read_nt(run / "asserted.nt") == gamma)
    agree = agree and result["asserted is the data file"] is not False
    (run / "check.json").write_text(json.dumps({"data": str(data), "agree": agree, **result}, indent=2) + "\n",
                                    encoding="utf-8")
    print(f"{'ALL AGREE' if agree else 'DISAGREEMENT'}  incoherent at K: {result['incoherent at K']}  -> {run / 'check.json'}")
    sys.exit(0 if agree else 1)


if __name__ == "__main__":
    main()
