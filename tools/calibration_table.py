#!/usr/bin/env python3
"""Set the checker's answers on the calibration sample beside what the entries say.

    python3 tools/calibration_table.py results/pipeline/full-p26/<timestamp>

Reads data/full-p26/calibration-sample.json (from tools/sample_for_checker.py)
and the latest saved response of each queries/calibration-*.api.json request.
For every sampled statement it compares two sets of constraint types:

    entries   the symmetric constraint when the reverse triple is a new default
              conclusion, and the constraint of each incompatibility entry that
              applies to the triple at K
    checker   the constraints the checker reports as violation, warning or
              suggestion on that statement

Writes calibration.json and calibration.md into the run directory. Reads saved
responses only; asks Wikidata nothing. Standard library only.
"""
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TYPES = {"Q21510862": "symmetric", "Q25796498": "contemporary", "Q21502838": "conflicts-with",
         "Q21503250": "subject type", "Q52558054": "none-of"}
REPORTED = {"violation", "warning", "suggestion"}


def responses(results, number, name):
    """statement id (lower case) -> list of check results, from every part of one category's request."""
    found = {}
    for directory in sorted(results.glob(f"calibration-{number:02d}-{name}*")):
        if directory.name.startswith("calibration-statements"):
            continue
        bodies = [p for p in sorted(directory.glob("*.json")) if not p.name.endswith(".meta.json")]
        if not bodies:
            continue
        doc = json.loads(bodies[-1].read_text(encoding="utf-8")).get("wbcheckconstraints", {})
        for report in doc.values():
            for statements in report.get("claims", {}).values():
                for statement in statements:
                    found[statement["id"].lower()] = statement.get("mainsnak", {}).get("results", [])
    return found


def names(types):
    return ", ".join(sorted(TYPES.get(t, t) for t in types)) or "nothing"


def main():
    run = pathlib.Path(sys.argv[1])
    sample = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "full-p26" / "calibration-sample.json"
    results = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "results"
    doc = json.loads(sample.read_text(encoding="utf-8"))

    out, lines = {}, [
        "| Category | Population | Statements checked | Entries expect | Same as entries | Entries only | Checker only |",
        "|---|---:|---:|---|---:|---|---|"]
    for number, (name, category) in enumerate(doc["categories"].items(), 1):
        answers = responses(results, number, name)
        tally = {"statements": 0, "not_returned": 0, "same": 0, "deprecated": 0,
                 "entries_only": collections.Counter(), "checker_only": collections.Counter(),
                 "checker_reports": collections.Counter(), "expected": collections.Counter(), "differences": []}
        counted = set()
        for item in category["items"]:
            expected = set(item["expected"])
            for statement in item["statements"]:
                if statement["claim"] in counted:   # two sampled triples of one subject can share statements
                    continue
                counted.add(statement["claim"])
                checks = answers.get(statement["claim"].lower())
                if checks is None:
                    tally["not_returned"] += 1
                    continue
                tally["statements"] += 1
                statuses = {c["status"] for c in checks}
                if statuses == {"deprecated"}:
                    tally["deprecated"] += 1
                reported = {c["constraint"]["type"] for c in checks if c["status"] in REPORTED}
                tally["expected"][names(expected)] += 1
                tally["checker_reports"][names(reported)] += 1
                if reported == expected:
                    tally["same"] += 1
                else:
                    tally["entries_only"].update(TYPES.get(t, t) for t in expected - reported)
                    tally["checker_only"].update(TYPES.get(t, t) for t in reported - expected)
                    tally["differences"].append({"statement": statement["claim"], "x": item["x"], "y": item["y"],
                                                 "entries": names(expected), "checker": names(reported)})
        show = lambda counter: "; ".join(f"{k}: {v}" for k, v in sorted(counter.items())) or "none"
        lines.append(f"| {name} | {category['population']:,} | {tally['statements']} | {show(tally['expected'])} | "
                     f"{tally['same']} | {show(tally['entries_only'])} | {show(tally['checker_only'])} |")
        out[name] = {"description": category["description"], "population": category["population"],
                     **{k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in tally.items()}}
    (run / "calibration.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    (run / "calibration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    for name, tally in out.items():
        print(f"{name}: checker reports {tally['checker_reports']}; not returned {tally['not_returned']}; "
              f"deprecated {tally['deprecated']}")


if __name__ == "__main__":
    main()
