#!/usr/bin/env python3
"""Count the instances of a pipeline run over spouse (P26), per category.

    python3 tools/count_instances.py data/full-p26/asserted.nt results/pipeline/full-p26/<timestamp>

Bookkeeping over what the pipeline wrote (the graph dumps and the rows of
2-incompatibilities and 4-recheck) and, for the two readings of "in conflict",
over conflicts.json from tools/check_cons.py. No reasoning is done here.
Every count is given twice: for instances with no unknown value, and for
instances with one (a Skolem IRI). Writes counts.json and counts.md into the
run directory. Standard library only.
"""
import collections
import json
import pathlib
import re
import sys

WDT = "http://www.wikidata.org/prop/direct/"
P26, P31, P569, P570 = f"<{WDT}P26>", f"<{WDT}P31>", f"<{WDT}P569>", f"<{WDT}P570>"
GENID = "/.well-known/genid/"
LINE = re.compile(r'^(\S+) (\S+) (.*) \.$')
DATE = re.compile(r'^"(-?)(\d+)-(\d\d)-(\d\d)T')
CONTEMPORARY = ("p26-contemporary-subject-first", "p26-contemporary-value-first")


def triples(path, predicates):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            found = LINE.match(line.rstrip("\n"))
            if found and found.group(2) in predicates:
                yield found.groups()


def unknown(*terms):
    return any(GENID in t for t in terms)


def date(literal):
    found = DATE.match(literal)
    if not found:
        return None
    sign, year, month, day = found.groups()
    return (-int(year) if sign else int(year), int(month), int(day))


def first_of_january(literal):
    parsed = date(literal)
    return parsed is not None and parsed[1:] == (1, 1)


def spouse_triple(row):
    """The spouse triple an incompatibility instance is about. The none-of entries bind the value as ?item."""
    return (row["x"], row["y"] if row.get("y") else row["item"])


def parties(row):
    """For a contemporary instance: the party whose death is used, the party whose birth is used."""
    return (row["x"], row["y"]) if row["entry"] == CONTEMPORARY[0] else (row["y"], row["x"])


def load(data, run):
    """Everything the counts and the checker sample are taken from."""
    run = pathlib.Path(run)
    spouse = {(s, o) for s, _, o in triples(data, {P26})}
    births, deaths = collections.defaultdict(list), collections.defaultdict(list)
    for s, p, o in triples(data, {P569, P570}):
        (births if p == P569 else deaths)[s].append(o)
    in_k = spouse | {(s, o) for s, _, o in triples(run / "closure.nt", {P26})}
    conclusions = {(s, o) for s, _, o in triples(run / "defaults.nt", {P26})}
    at_k = json.loads((run / "2-incompatibilities.json").read_text(encoding="utf-8"))
    over_cons = json.loads((run / "4-recheck.json").read_text(encoding="utf-8"))
    key = lambda row: json.dumps(row, sort_keys=True)
    seen = {key(r) for r in at_k}
    only_cons = [r for r in over_cons if key(r) not in seen]
    return {"spouse": spouse, "births": births, "deaths": deaths, "in_k": in_k, "conclusions": conclusions,
            "new": conclusions - in_k, "at_k": at_k, "only_cons": only_cons, "run": run}


def checker_style(d, end_party, start_party):
    """Does the latest death of one party precede the earliest birth of the other? (dates only)"""
    ends = [date(x) for x in d["deaths"].get(end_party, []) if date(x)]
    begins = [date(x) for x in d["births"].get(start_party, []) if date(x)]
    return bool(ends and begins) and max(ends) < min(begins)


def main():
    data, run = sys.argv[1], pathlib.Path(sys.argv[2])
    d = load(data, run)
    two = lambda: {"no unknown value": 0, "unknown value": 0}
    counts = collections.defaultdict(two)

    def add(name, *terms, n=1):
        counts[name]["unknown value" if unknown(*terms) else "no unknown value"] += n

    # Spouse triples.
    for s, o in d["spouse"]:
        add("spouse triples", s, o)
        add("spouse triples: reciprocated" if (o, s) in d["spouse"] else "spouse triples: missing reverse", s, o)
        if s == o:
            add("spouse triples: subject and value the same", s, o)

    # Default conclusions, and "in conflict" as step 4 has it.
    conflict = collections.defaultdict(set)   # conclusion -> entries
    elsewhere = 0
    for row in d["only_cons"]:
        pair = spouse_triple(row)
        if pair in d["new"]:
            conflict[pair].add(row["entry"])
        else:
            elsewhere += 1
    for pair in d["conclusions"]:
        add("default conclusions", *pair)
        if pair in d["in_k"]:
            add("default conclusions: already in K", *pair)
        else:
            add("default conclusions: new to K", *pair)
            if pair in conflict:
                add("new conclusions: in conflict", *pair)
                for entry in sorted(conflict[pair]):
                    add(f"new conclusions: in conflict with {entry}", *pair)
                add("new conclusions: in conflict with exactly " + " + ".join(sorted(conflict[pair])), *pair)
            else:
                add("new conclusions: clean", *pair)

    # Incompatibilities at K.
    statements_at_k = collections.defaultdict(set)
    for row in d["at_k"]:
        add(f"incompatibility instances at K: {row['entry']}", *spouse_triple(row))
        statements_at_k[row["entry"]].add(spouse_triple(row))
    for entry, pairs in statements_at_k.items():
        for pair in pairs:
            add(f"spouse triples with an incompatibility at K: {entry}", *pair)
    for pair in set().union(*statements_at_k.values()) if statements_at_k else ():
        add("spouse triples with an incompatibility at K: any entry", *pair)

    # Contemporary instances: several dates, the checker's comparison, 1 January.
    for where, rows in (("at K", d["at_k"]), ("over Cons only", d["only_cons"])):
        seen_pairs = set()
        for row in rows:
            if row["entry"] not in CONTEMPORARY:
                continue
            end_party, start_party = parties(row)
            terms = (row["x"], row["y"])
            add(f"contemporary instances {where}", *terms)
            several = len(d["deaths"].get(end_party, [])) > 1 or len(d["births"].get(start_party, [])) > 1
            any_several = several or len(d["births"].get(end_party, [])) > 1 or len(d["deaths"].get(start_party, [])) > 1
            if several:
                add(f"contemporary instances {where}: the death or the birth compared is one of several", *terms)
            if any_several:
                add(f"contemporary instances {where}: a party has several birth or death dates", *terms)
            if first_of_january(row["end"]) or first_of_january(row["start"]):
                add(f"contemporary instances {where}: a compared date falls on 1 January", *terms)
            if (end_party, start_party) not in seen_pairs:
                seen_pairs.add((end_party, start_party))
                add(f"contemporary, distinct (died, born) party pairs {where}", *terms)
                style = "latest death precedes earliest birth" if checker_style(d, end_party, start_party) \
                    else "some death precedes some birth, but not the latest the earliest"
                add(f"contemporary, distinct party pairs {where}: {style}", *terms)

    # Conflicts-with: is the forbidden class a class of the subject itself, or reached by subclass-of?
    subjects = {r["x"] for r in d["at_k"] + d["only_cons"] if r["entry"] == "p26-conflicts-with"}
    direct = collections.defaultdict(set)
    for s, _, o in triples(data, {P31}):
        if s in subjects:
            direct[s].add(o)
    for where, rows in (("at K", d["at_k"]), ("over Cons only", d["only_cons"])):
        by_triple = collections.defaultdict(bool)
        for row in rows:
            if row["entry"] == "p26-conflicts-with":
                by_triple[spouse_triple(row)] |= row["class"] in direct[row["x"]]
        for triple, is_direct in by_triple.items():
            how = "a forbidden class is a direct class of the subject" if is_direct \
                else "only through subclass of"
            add(f"conflicts-with, spouse triples {where}: {how}", *triple)

    # Dates in the snapshot.
    for name, table in (("date of birth", d["births"]), ("date of death", d["deaths"])):
        for values in table.values():
            for value in values:
                if date(value) is None:
                    counts[f"{name} values"]["unknown value"] += 1
                else:
                    counts[f"{name} values"]["no unknown value"] += 1
                    if first_of_january(value):
                        counts[f"{name} values: on 1 January"]["no unknown value"] += 1
        counts[f"parties with several {name} values"]["no unknown value"] = sum(len(v) > 1 for v in table.values())

    result = {"data": str(data), "run": str(run), "counts": dict(sorted(counts.items())),
              "instances over Cons, not at K, whose spouse triple is not a new conclusion": elsewhere}
    readings = run / "conflicts.json"
    if readings.exists():
        c = json.loads(readings.read_text(encoding="utf-8"))
        by_entry = {"over Cons": collections.Counter(), "one at a time": collections.Counter()}
        for item in c["conclusions"]:
            for entry in item["over_cons"]:
                by_entry["over Cons"][entry] += 1
            for entry in item["one_at_a_time"]:
                by_entry["one at a time"][entry] += 1
        mine = {tuple(pair): sorted(entries) for pair, entries in conflict.items()}
        theirs = {(i["conclusion"][0], i["conclusion"][2]): i["over_cons"] for i in c["conclusions"] if i["over_cons"]}
        result["readings of 'in conflict'"] = {
            "new conclusions": c["new_conclusions"],
            "in conflict, over Cons": c["in_conflict_over_cons"],
            "in conflict, one at a time": c["in_conflict_one_at_a_time"],
            "conclusions where the readings differ": c["conclusions_where_the_readings_differ"],
            "by entry, over Cons": dict(sorted(by_entry["over Cons"].items())),
            "by entry, one at a time": dict(sorted(by_entry["one at a time"].items())),
            "pipeline's step 4 and the definition's 'over Cons' give the same conclusions and entries": mine == theirs,
        }
    (run / "counts.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    lines = ["| Count | No unknown value | Unknown value |", "|---|---:|---:|"]
    lines += [f"| {name} | {v['no unknown value']:,} | {v['unknown value']:,} |" for name, v in sorted(counts.items())]
    (run / "counts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if "readings of 'in conflict'" in result:
        print(json.dumps(result["readings of 'in conflict'"], indent=1))
    print("elsewhere:", elsewhere)


if __name__ == "__main__":
    main()
