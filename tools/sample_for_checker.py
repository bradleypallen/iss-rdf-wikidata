#!/usr/bin/env python3
"""Draw spouse statements from each category of a full run, to put to Wikidata's checker.

    python3 tools/sample_for_checker.py sample data/full-p26/asserted.nt results/pipeline/full-p26/<timestamp>
        draws up to 50 spouse triples per category (fixed seed) and writes
        data/full-p26/calibration-sample.json and, per category, the query
        queries/calibration-statements-<nn>-<category>.rq that finds the statement
        behind each sampled triple

    python3 tools/sample_for_checker.py requests
        reads the latest result of those queries and writes one checker request per
        category, queries/calibration-<nn>-<category>.api.json, naming the statements

A category is defined by what the entries say about the asserted triple x spouse y.
"expected" lists the constraint types the entries make the checker's counterpart
of: the symmetric constraint when the reverse triple is a new default conclusion,
and the constraint of each incompatibility entry that applies to the triple at K.
Standard library only.
"""
import collections
import json
import pathlib
import random
import sys

from count_instances import CONTEMPORARY, checker_style, first_of_january, load, parties, spouse_triple, unknown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "full-p26" / "calibration-sample.json"
SEED, SIZE = 20261114, 50
CONSTRAINT = {"p26-symmetric": "Q21510862", "p26-contemporary-subject-first": "Q25796498",
              "p26-contemporary-value-first": "Q25796498", "p26-conflicts-with": "Q21502838",
              "p26-subject-type": "Q21503250", "p26-none-of-widowed": "Q52558054",
              "p26-none-of-unmarried": "Q52558054", "p26-none-of-name-or-status": "Q52558054"}
P26_CONSTRAINTS = ["P26$75392F51-A753-4451-B057-4C2719462EFB", "P26$862D87C1-BB05-45A8-934F-3585370F6253",
                   "P26$183C2471-ED90-45FD-949F-020CD7EF5F90", "P26$35E5D7A3-D2AC-4A9F-93D3-8630E85EC729",
                   "P26$46738363-4725-63da-853b-24a1190a343e", "P26$c75a4c3d-4806-8402-9d44-79166c9dad87",
                   "P26$f1e6c730-480b-deee-0bc5-792f91ba73e5"]
CATEGORIES = [
    ("reciprocated", "Reverse triple present; no incompatibility at K."),
    ("clean-default", "No reverse triple; the default conclusion is clean; no incompatibility at K."),
    ("conflict-conflicts-with", "No reverse triple; the default conclusion is in conflict with conflicts-with over Cons."),
    ("conflict-subject-type", "No reverse triple, value an item; the default conclusion is in conflict with subject type only."),
    ("conflict-contemporary", "No reverse triple; the default conclusion is in conflict with a contemporary entry over Cons."),
    ("unknown-value", "The value is an unknown value."),
    ("contemporary-no-1-january", "A contemporary entry applies at K; latest death precedes earliest birth; no compared date on 1 January."),
    ("contemporary-1-january", "A contemporary entry applies at K; latest death precedes earliest birth; a compared date falls on 1 January."),
    ("contemporary-several-dates", "A contemporary entry applies at K, but the latest death does not precede the earliest birth."),
    ("subject-type-at-k", "The subject type entry applies at K."),
    ("conflicts-with-at-k", "The conflicts-with entry applies at K."),
    ("none-of-at-k", "A none-of entry applies at K."),
]


def sample(data, run):
    d = load(data, run)
    conflict = collections.defaultdict(set)
    for row in d["only_cons"]:
        if spouse_triple(row) in d["new"]:
            conflict[spouse_triple(row)].add(row["entry"])
    at_k = collections.defaultdict(set)          # asserted triple -> entries applying at K
    contemporary = collections.defaultdict(lambda: {"checker_style": False, "january": False})
    for row in d["at_k"]:
        triple = spouse_triple(row)
        at_k[triple].add(row["entry"])
        if row["entry"] in CONTEMPORARY:
            flags = contemporary[triple]
            flags["checker_style"] |= checker_style(d, *parties(row))
            flags["january"] |= first_of_january(row["end"]) or first_of_january(row["start"])

    members = collections.defaultdict(list)
    for x, y in sorted(d["spouse"]):
        reverse_new = (y, x) in d["new"]
        entries = at_k.get((x, y), set())
        if unknown(y):
            members["unknown-value"].append((x, y))
        elif not reverse_new and not entries and (y, x) in d["spouse"]:
            members["reciprocated"].append((x, y))
        elif reverse_new and not entries and (y, x) not in conflict:
            members["clean-default"].append((x, y))
        if reverse_new and not unknown(y):
            hit = conflict.get((y, x), set())
            if "p26-conflicts-with" in hit:
                members["conflict-conflicts-with"].append((x, y))
            elif hit == {"p26-subject-type"}:
                members["conflict-subject-type"].append((x, y))
            if hit & set(CONTEMPORARY):
                members["conflict-contemporary"].append((x, y))
        if entries & set(CONTEMPORARY):
            flags = contemporary[(x, y)]
            if not flags["checker_style"]:
                members["contemporary-several-dates"].append((x, y))
            elif flags["january"]:
                members["contemporary-1-january"].append((x, y))
            else:
                members["contemporary-no-1-january"].append((x, y))
        if "p26-subject-type" in entries:
            members["subject-type-at-k"].append((x, y))
        if "p26-conflicts-with" in entries:
            members["conflicts-with-at-k"].append((x, y))
        if any(e.startswith("p26-none-of") for e in entries):
            members["none-of-at-k"].append((x, y))

    rng = random.Random(SEED)
    out = {"seed": SEED, "size": SIZE, "data": str(data), "run": str(run), "categories": {}}
    for number, (name, description) in enumerate(CATEGORIES, 1):
        population = members[name]
        drawn = sorted(rng.sample(population, min(SIZE, len(population))))
        items = []
        for x, y in drawn:
            expected = {CONSTRAINT[e] for e in at_k.get((x, y), set())}
            if (y, x) in d["new"]:
                expected.add(CONSTRAINT["p26-symmetric"])
            items.append({"x": x, "y": y, "expected": sorted(expected), "statements": []})
        out["categories"][name] = {"description": description, "population": len(population), "items": items}
        statements_query(number, name, drawn)
        print(f"{name}: {len(drawn)} of {len(population)}")
    SAMPLE.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


def statements_query(number, name, drawn):
    """One query per category (the endpoint refuses a long one): the statement behind each triple.
    An unknown value is a different term on the statement than on the direct triple, so those
    statements are found by subject, as the subject's statements whose value is not an item."""
    if name == "unknown-value":
        values = "\n".join(f"    {x}" for x in sorted({x for x, _ in drawn}))
        where = f"""  VALUES ?x {{
{values}
  }}
  ?x p:P26 ?statement .
  ?statement ps:P26 ?y .
  FILTER(!STRSTARTS(STR(?y), "http://www.wikidata.org/entity/"))"""
    else:
        values = "\n".join(f"    ({x} {y})" for x, y in drawn)
        where = f"""  VALUES (?x ?y) {{
{values}
  }}
  ?x p:P26 ?statement .
  ?statement ps:P26 ?y ."""
    (ROOT / "queries" / f"calibration-statements-{number:02d}-{name}.rq").write_text(
        f"""# Generated by tools/sample_for_checker.py (seed {SEED}). Do not edit.
# The statement behind each spouse triple sampled for the checker calibration,
# category '{name}', with its rank, so that the checker can be asked about
# that statement itself.
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?x ?y ?statement ?rank WHERE {{
{where}
  OPTIONAL {{ ?statement wikibase:rank ?rank }}
}}
""", encoding="utf-8")


def requests():
    doc = json.loads(SAMPLE.read_text(encoding="utf-8"))
    doc["statements_from"] = []
    for number, (name, category) in enumerate(doc["categories"].items(), 1):
        results = ROOT / "results" / f"calibration-statements-{number:02d}-{name}"
        body = [p for p in sorted(results.glob("*.json")) if not p.name.endswith(".meta.json")][-1]
        doc["statements_from"].append(str(body.relative_to(ROOT)))
        found = collections.defaultdict(list)
        for b in json.loads(body.read_text(encoding="utf-8"))["results"]["bindings"]:
            entity, guid = b["statement"]["value"].rsplit("/", 1)[1].split("-", 1)
            statement = {"claim": f"{entity}${guid}", "rank": b.get("rank", {}).get("value", "").rsplit("#", 1)[-1]}
            key = f"<{b['x']['value']}>" if name == "unknown-value" else (f"<{b['x']['value']}>", f"<{b['y']['value']}>")
            found[key].append(statement)
        claims = []
        for item in category["items"]:
            item["statements"] = found.get(item["x"] if name == "unknown-value" else (item["x"], item["y"]), [])
            claims += [s["claim"] for s in item["statements"]]
        claims = sorted(set(claims))
        missing = sum(not item["statements"] for item in category["items"])
        path = ROOT / "queries" / f"calibration-{number:02d}-{name}.api.json"
        for start in range(0, max(len(claims), 1), 50):   # the API takes at most 50 statements
            part = path if start == 0 else path.with_name(path.name.replace(".api.json", f"-part{start // 50 + 1}.api.json"))
            part.write_text(json.dumps({
                "purpose": f"Checker calibration for the full run, category '{name}': {category['description']} "
                           f"Statements drawn with seed {doc['seed']}; see data/full-p26/calibration-sample.json.",
                "claimid": claims[start:start + 50], "constraintid": P26_CONSTRAINTS, "status": "*"}, indent=1) + "\n",
                encoding="utf-8")
        print(f"{name}: {len(category['items'])} triples, {len(claims)} statements, {missing} with no statement found")
    SAMPLE.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "sample":
        sample(sys.argv[2], pathlib.Path(sys.argv[3]))
    elif len(sys.argv) == 2 and sys.argv[1] == "requests":
        requests()
    else:
        sys.exit(__doc__)
