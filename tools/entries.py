#!/usr/bin/env python3
"""Check entries/entries.json and print the entries from it.

    python3 tools/entries.py check     well-formedness; exits 1 on any error
    python3 tools/entries.py list      the entries as <A, c; E>, generated from the file

The file is the only copy of the entries. Listings are printed from it, never
written by hand. Standard library only.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries" / "entries.json"
BOT = "BOT"


def is_var(term):
    return term.startswith("?")


def variables(triples):
    return {t for triple in triples for t in triple if is_var(t)}


def names(triples):
    return {t for triple in triples for t in triple if not is_var(t)}


def all_triples(item):
    """Every triple of a rule or entry: premises, conclusion, defeaters."""
    out = list(item["premises"])
    if item["conclusion"] != BOT:
        out.append(item["conclusion"])
    for defeater in item.get("defeaters", []):
        out.extend(defeater)
    return out


def check(doc):
    errors, notes = [], []
    prefixes = doc["prefixes"]
    seen = set()
    for item in doc["regime"]["rules"] + doc["entries"]:
        ident = item.get("id", "<no id>")
        err = lambda msg: errors.append(f"{ident}: {msg}")
        if ident in seen:
            err("duplicate id")
        seen.add(ident)

        for triple in all_triples(item):
            if len(triple) != 3:
                err(f"not a triple: {triple}")
            for term in triple:
                if not is_var(term) and term.split(":", 1)[0] not in prefixes:
                    err(f"unknown prefix in {term}")

        kind = item.get("kind", "rule")
        if kind == "default" and item["conclusion"] == BOT:
            err("a default must conclude a triple")
        if kind == "incompatibility" and item["conclusion"] != BOT:
            err("an incompatibility must conclude BOT")

        bound = variables(item["premises"])
        expand = item.get("expand", {})
        for var in expand:
            if var not in bound:
                err(f"expanded variable {var} does not occur in the premises")
        if item["conclusion"] != BOT:
            free = variables([item["conclusion"]]) - bound
            if free:
                err(f"conclusion introduces {sorted(free)} (range restriction)")
        for guard in item.get("guards", []):
            for side in (guard["left"], guard["right"]):
                if is_var(side) and side not in bound:
                    err(f"guard variable {side} is not bound by the premises")
        for defeater in item.get("defeaters", []):
            existential = variables(defeater) - bound
            if existential:
                notes.append(f"{ident}: defeater variables {sorted(existential)} are existential")
        for line in item.get("evidence", []):
            for path in re.findall(r"results/\S+?\.json", line):
                if not (ROOT / path).exists():
                    err(f"evidence file missing: {path}")

    groups = {}
    for entry in doc["entries"]:
        if "variant_of" in entry:
            groups.setdefault(entry["variant_of"], []).append(entry["id"])
    for group, members in groups.items():
        notes.append(f"{group}: {len(members)} alternatives, one to be kept: {', '.join(members)}")
    return errors, notes


def vocabulary(doc):
    vocab = set()
    for item in doc["regime"]["rules"] + doc["entries"]:
        vocab |= names(all_triples(item))
        for values in item.get("expand", {}).values():
            vocab |= set(values)
    return vocab


def show_triple(triple):
    return " ".join(triple)


def show_graph(triples):
    return "{" + " . ".join(show_triple(t) for t in triples) + "}"


def show(item):
    conclusion = "⊥" if item["conclusion"] == BOT else show_triple(item["conclusion"])
    defeaters = item.get("defeaters", [])
    lines = [f"  A  {show_graph(item['premises'])}", f"  c  {conclusion}"]
    if defeaters:
        lines += [f"  E  {show_graph(d)}" for d in defeaters]
    elif "kind" in item:
        lines.append("  E  none")
    for guard in item.get("guards", []):
        lines.append(f"  guard  {guard['left']} {guard['op']} {guard['right']}")
    for var, values in item.get("expand", {}).items():
        lines.append(f"  for each {var} in  {' '.join(values)}")
    return "\n".join(lines)


def listing(doc):
    print(doc["status"])
    print("\nRegime")
    for rule in doc["regime"]["rules"]:
        print(f"\n{rule['id']}  [rule]")
        print(show(rule))
    print("\nEntries")
    for entry in doc["entries"]:
        source = entry["source"]
        variant = f"  (alternative for {entry['variant_of']})" if "variant_of" in entry else ""
        print(f"\n{entry['id']}  [{entry['kind']}]{variant}")
        print(f"  from  {source['statement'] or 'statement IRI not recorded'}"
              f"  ({source['constraint_type']} on {source['property']})")
        print(show(entry))
        print(f"  choices marked: {len(entry['choices'])}")
    print(f"\nNot written: {len(doc['not_written'])} constraints on P26 (see the file for reasons)")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in ("check", "list"):
        sys.exit(__doc__)
    doc = json.loads(ENTRIES.read_text(encoding="utf-8"))
    if command == "list":
        listing(doc)
        return
    errors, notes = check(doc)
    for note in notes:
        print("note   ", note)
    for error in errors:
        print("ERROR  ", error)
    vocab = sorted(vocabulary(doc))
    print(f"{len(doc['regime']['rules'])} rules, {len(doc['entries'])} entries, "
          f"{len(vocab)} named terms in the vocabulary, {len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
