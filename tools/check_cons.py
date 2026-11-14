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

It also computes, for each conclusion in D* that is not in K, the
incompatibility entries it is in conflict with, under two readings:

    over Cons       an instance applies at Cons, does not apply at K, and has
                    the conclusion among its premises
    one at a time   an instance applies at cl_R(G with that one conclusion) and
                    does not apply at K

Writes check.json and conflicts.json into the run directory. Exits 1 on any
disagreement with the pipeline. Standard library only.
"""
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE = re.compile(r'^(<[^>]*>|_:\S+)\s+(<[^>]*>)\s+(<[^>]*>|_:\S+|".*"(?:\^\^<[^>]*>|@[\w-]+)?)\s*\.\s*$')
DATE = re.compile(r'^"(-?)(\d+)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z"\^\^<http://www.w3.org/2001/XMLSchema#dateTime>$')
INTERN = {}


def read_nt(path):
    """The triples of an N-Triples file. Equal terms are one string object, to save memory."""
    triples = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                triples.add(tuple(INTERN.setdefault(t, t) for t in LINE.match(line).groups()))
    return triples


class Graph:
    """A set of triples with the lookups pattern matching needs. Predicates are never variables."""

    def __init__(self, triples=()):
        self.all, self.by_subject, self.by_object, self.pairs = set(), {}, {}, {}
        for triple in triples:
            self.add(triple)

    def add(self, triple):
        if triple in self.all:
            return False
        s, p, o = triple
        self.all.add(triple)
        self.by_subject.setdefault(p, {}).setdefault(s, []).append(o)
        self.by_object.setdefault(p, {}).setdefault(o, []).append(s)
        self.pairs.setdefault(p, set()).add((s, o))
        return True

    def remove(self, triple):
        s, p, o = triple
        self.all.discard(triple)
        self.by_subject[p][s].remove(o)
        self.by_object[p][o].remove(s)
        self.pairs[p].discard((s, o))

    def candidates(self, pattern, binding):
        """The triples that the pattern can match under the binding."""
        s, p, o = (binding.get(t, t) for t in pattern)
        s_free, o_free = s.startswith("?"), o.startswith("?")
        if not s_free and not o_free:
            return ((s, p, o),) if (s, p, o) in self.all else ()
        if not s_free:
            return ((s, p, x) for x in self.by_subject.get(p, {}).get(s, ()))
        if not o_free:
            return ((x, p, o) for x in self.by_object.get(p, {}).get(o, ()))
        return ((a, p, b) for a, b in self.pairs.get(p, ()))

    def cost(self, pattern, binding):
        free = sum(binding.get(t, t).startswith("?") for t in (pattern[0], pattern[2]))
        return (free, len(self.pairs.get(pattern[1], ())))


def ground(term, prefixes):
    if term.startswith("?"):
        return term
    prefix, local = term.split(":", 1)
    iri = f"<{prefixes[prefix]}{local}>"
    return INTERN.setdefault(iri, iri)


def unify(pattern, triple, binding):
    new = dict(binding)
    for want, have in zip(pattern, triple):
        if want.startswith("?"):
            if new.setdefault(want, have) != have:
                return None
        elif want != have:
            return None
    return new


def matches(patterns, graph, binding):
    """Every extension of binding that sends all patterns into graph."""
    if not patterns:
        yield binding
        return
    first = min(patterns, key=lambda p: graph.cost(p, binding))
    rest = [p for p in patterns if p is not first]
    for triple in graph.candidates(first, binding):
        new = unify(first, triple, binding)
        if new is not None:
            yield from matches(rest, graph, new)


def instantiate(triple, binding):
    return tuple(binding[t] if t.startswith("?") else t for t in triple)


def close(graph, rules, delta=None):
    """Add to graph everything the rules derive; return what was added.
    With delta, only derivations that use a triple of delta are looked for."""
    added = []
    if delta is None:
        delta = [instantiate(r["conclusion"], b) for r in rules for b in matches(r["premises"], graph, {})]
        delta = [t for t in delta if graph.add(t)]
        added += delta
    while delta:
        new = []
        for rule in rules:
            for i, premise in enumerate(rule["premises"]):
                rest = rule["premises"][:i] + rule["premises"][i + 1:]
                for triple in delta:
                    start = unify(premise, triple, {})
                    if start is not None:
                        new += [instantiate(rule["conclusion"], b) for b in matches(rest, graph, start)]
        delta = [t for t in new if graph.add(t)]
        added += delta
    return added


DATES = {}


def date(literal):
    if literal not in DATES:
        found = DATE.match(literal)
        if found:
            sign, *parts = found.groups()
            year, *rest = (int(p) for p in parts)
            DATES[literal] = (-year if sign else year, *rest)
        else:
            DATES[literal] = None
    return DATES[literal]


def holds(guard, binding):
    """A comparison holds only between two dates; anything else (an unknown value, say) fails it."""
    left, right = date(binding[guard["left"]]), date(binding[guard["right"]])
    if left is None or right is None:
        return False
    return {"<": left < right, ">": left > right}[guard["op"]]


def passes(entry, graph, binding):
    """Guards hold and no defeater has an instance in graph."""
    return all(holds(g, binding) for g in entry["guards"]) and not any(
        next(matches(d, graph, binding), None) is not None for d in entry["defeaters"])


def starts(entry):
    found = [{}]
    for var, values in entry["expand"].items():
        found = [{**s, var: value} for s in found for value in values]
    return found


def applying(entry, graph, through=None):
    """The bindings of the premise variables at which the entry applies at graph.
    With through, only instances that have one of those triples among their premises."""
    for start in starts(entry):
        if through is None:
            for binding in matches(entry["premises"], graph, start):
                if passes(entry, graph, binding):
                    yield binding
            continue
        seen = set()
        for i, premise in enumerate(entry["premises"]):
            rest = entry["premises"][:i] + entry["premises"][i + 1:]
            for triple in through:
                first = unify(premise, triple, start)
                if first is None:
                    continue
                for binding in matches(rest, graph, first):
                    key = tuple(sorted(binding.items()))
                    if key not in seen and passes(entry, graph, binding):
                        seen.add(key)
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
    clock = time.monotonic()
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
    by_id = {e["id"]: e for e in entries}

    gamma = read_nt(data)
    blank = any(t.startswith("_:") for triple in gamma for t in triple)
    if blank:  # the pipeline Skolemizes blank nodes; start from what it loaded
        gamma = read_nt(run / "asserted.nt")

    # The definition, step by step. One Graph is grown from G to K to Cons.
    graph = Graph(gamma)
    close(graph, rules)
    k = set(graph.all)
    at_k = instances(incompatibilities, graph)
    d_star = {instantiate(e["conclusion"], b) for e in defaults for b in applying(e, graph)}
    new = sorted(d_star - k)

    # Reading "one at a time": each new conclusion alone, added to G.
    one_at_a_time = {}
    for conclusion in new:
        graph.add(conclusion)
        extra = [conclusion] + close(graph, rules, [conclusion])
        hit = sorted({e["id"] for e in incompatibilities for _ in applying(e, graph, through=extra)})
        if hit:
            one_at_a_time[conclusion] = hit
        for triple in extra:
            graph.remove(triple)

    for conclusion in new:
        graph.add(conclusion)
    close(graph, rules, new)
    cons = graph.all
    over_cons = instances(incompatibilities, graph)

    # Reading "over Cons": instances that apply at Cons and not at K, by the conclusions among their premises.
    over_cons_reading, new_set, elsewhere = {}, set(new), 0
    for ident, binding in over_cons - at_k:
        touched = [t for t in (instantiate(p, dict(binding)) for p in by_id[ident]["premises"]) if t in new_set]
        elsewhere += not touched
        for conclusion in touched:
            over_cons_reading.setdefault(conclusion, set()).add(ident)
    over_cons_reading = {c: sorted(ids) for c, ids in over_cons_reading.items()}

    mine = {"K": k, "D*": d_star, "Cons": cons,
            "incompatibilities at K": at_k, "incompatibilities over Cons": over_cons}
    nt = lambda *names: set().union(*(read_nt(run / f"{n}.nt") for n in names))
    result, agree = {}, True

    def compare(name, theirs):
        nonlocal agree
        only_definition, only_pipeline = mine[name] - theirs, theirs - mine[name]
        same = not only_definition and not only_pipeline
        agree = agree and same
        result[name] = {"definition": len(mine[name]), "pipeline": len(theirs), "agree": same,
                        "only_definition": sorted(map(str, only_definition))[:50],
                        "only_pipeline": sorted(map(str, only_pipeline))[:50]}
        print(f"{'agree   ' if same else 'DISAGREE'}  {name}: definition {len(mine[name])}, pipeline {len(theirs)}")

    asserted = nt("asserted")
    result["asserted is the data file"] = "not compared: blank nodes were Skolemized" if blank else (asserted == gamma)
    agree = agree and result["asserted is the data file"] is not False
    theirs_k = asserted | nt("closure")
    del asserted, gamma
    compare("K", theirs_k)
    theirs_d = nt("defaults")
    compare("D*", theirs_d)
    compare("Cons", theirs_k | theirs_d | nt("default-closure"))
    del theirs_k, theirs_d
    compare("incompatibilities at K", rows_as_instances(run / "2-incompatibilities.json"))
    compare("incompatibilities over Cons", rows_as_instances(run / "4-recheck.json"))

    conflicts = sorted(set(one_at_a_time) | set(over_cons_reading))
    differ = [c for c in conflicts if one_at_a_time.get(c, []) != over_cons_reading.get(c, [])]
    (run / "conflicts.json").write_text(json.dumps({
        "new_conclusions": len(new),
        "in_conflict_over_cons": len(over_cons_reading),
        "in_conflict_one_at_a_time": len(one_at_a_time),
        "conclusions_where_the_readings_differ": len(differ),
        "instances_over_cons_not_at_K_touching_no_new_conclusion": elsewhere,
        "conclusions": [{"conclusion": list(c), "over_cons": over_cons_reading.get(c, []),
                         "one_at_a_time": one_at_a_time.get(c, [])} for c in conflicts],
    }, indent=1) + "\n", encoding="utf-8")
    print(f"{'agree   ' if not differ else 'DIFFER  '}  the two readings of 'in conflict': over Cons "
          f"{len(over_cons_reading)}, one at a time {len(one_at_a_time)}, of {len(new)} new conclusions")

    seconds = round(time.monotonic() - clock, 1)
    (run / "check.json").write_text(json.dumps({
        "data": str(data), "agree": agree, "seconds": seconds, "incoherent at K": bool(at_k),
        "readings_of_in_conflict_differ_on": len(differ), **result}, indent=2) + "\n", encoding="utf-8")
    print(f"{'ALL AGREE' if agree else 'DISAGREEMENT'}  incoherent at K: {bool(at_k)}  {seconds}s  -> {run / 'check.json'}")
    sys.exit(0 if agree else 1)


if __name__ == "__main__":
    main()
