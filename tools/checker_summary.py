#!/usr/bin/env python3
"""Print, from a saved wbcheckconstraints response, what the checker reported.

    python3 tools/checker_summary.py results/checker-hand-sized/<timestamp>.json [labels.json]

One row per entity, property and statement: the constraints that are not
'compliance', each with its status and the checker's message, and the number
of constraints that are. Reads a saved response; asks Wikidata nothing.
Standard library only.
"""
import json
import re
import sys


def main():
    doc = json.load(open(sys.argv[1], encoding="utf-8"))["wbcheckconstraints"]
    labels = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else {}
    name = lambda q: f"{q} ({labels['http://www.wikidata.org/entity/' + q]})" if (
        "http://www.wikidata.org/entity/" + q) in labels else q
    print("| Entity | Property | Statement | Not compliant | Compliant |\n|---|---|---|---|---|")
    for entity, report in doc.items():
        claims = report.get("claims", {})
        checked = False
        for prop, statements in sorted(claims.items()):
            for statement in statements:
                results = statement.get("mainsnak", {}).get("results", [])
                if not results:
                    continue
                checked = True
                other = [f"{r['status']}: {r['constraint']['typeLabel']}"
                         + (" — " + re.sub(r"<[^>]+>", "", r["message-html"]) if r.get("message-html") else "")
                         for r in results if r["status"] != "compliance"]
                compliant = sum(r["status"] == "compliance" for r in results)
                print(f"| {name(entity)} | {prop} | …{statement['id'][-6:]} | {'<br>'.join(other) or 'none'} | {compliant} |")
        if not checked:
            print(f"| {name(entity)} | | no statement checked | | |")


if __name__ == "__main__":
    main()
