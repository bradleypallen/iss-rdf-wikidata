#!/usr/bin/env python3
"""Check, on samples of items, that dropping subclass-of triples loses nothing.

    python3 tools/sample_hierarchy_check.py [--seed 20261114] [--n 200]

The full run keeps only the P279 triples that lie on a path to a class named
in an entry. This draws two samples of spouse parties from data/full-p26:

    random      n parties drawn at random
    off-named   n parties drawn at random among those that have a class and none of
                whose direct classes is named in an entry, so that only the hierarchy
                can connect them to a named class

For each it writes the facts about the sample (every spouse triple touching a
sampled party, and the classes and dates of every party in those triples)
twice: with the kept P279 triples, and with every P279 triple fetched (all
those at or above a class of any spouse party). It runs the pipeline and the
independent check on both and compares what the entries produce.

Writes data/sample-*/asserted.nt and results/pipeline/sample-*/comparison.json.
Needs pyoxigraph (through tools/run_pipeline.py).
"""
import argparse
import collections
import json
import pathlib
import random
import re
import subprocess
import sys

from build_subset import ROOT, named_classes

WDT = "<http://www.wikidata.org/prop/direct/"
P26, P31, P279 = WDT + "P26>", WDT + "P31>", WDT + "P279>"
GENID = "/.well-known/genid/"
LINE = re.compile(r'^(\S+) (\S+) (.*) \.$')
COMPARED = ["defaults.nt", "2-default-instances.json", "2-defeated.json", "2-incompatibilities.json",
            "4-recheck.json", "q-spouse-of-at-closure.json", "q-spouse-of-at-cons.json"]


def run(*command):
    done = subprocess.run([sys.executable, *map(str, command)], capture_output=True, text=True)
    return done.returncode, done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-300:]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--n", type=int, default=200)
    args = ap.parse_args()
    doc = json.loads((ROOT / "entries" / "entries.json").read_text(encoding="utf-8"))
    named = named_classes(doc)

    spouse, about, classes, kept, other = [], collections.defaultdict(list), collections.defaultdict(set), [], []
    with (ROOT / "data" / "full-p26" / "asserted.nt").open(encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            s, p, o = LINE.match(line).groups()
            if p == P26:
                spouse.append((s, o, line))
            elif p == P279:
                kept.append(line)
            elif p.startswith(WDT):
                about[s].append(line)
                if p == P31:
                    classes[s].add(o)
            else:
                other.append(line)      # the constraint statement
    everything = (ROOT / "data" / "full-p26" / "subclass-all.nt").read_text(encoding="utf-8").splitlines()

    parties = sorted({t for s, o, _ in spouse for t in (s, o) if GENID not in t})
    off_named = [p for p in parties if classes[p] and not (classes[p] & named)]
    rng = random.Random(args.seed)
    samples = {"random": rng.sample(parties, args.n), "off-named": rng.sample(off_named, min(args.n, len(off_named)))}

    summary = {"seed": args.seed, "n": args.n, "parties": len(parties), "parties_off_named": len(off_named),
               "subclass_triples_kept": len(kept), "subclass_triples_all": len(everything), "samples": {}}
    for name, sample in samples.items():
        chosen = set(sample)
        touching = [(s, o, line) for s, o, line in spouse if s in chosen or o in chosen]
        members = {t for s, o, _ in touching for t in (s, o)}
        facts = [line for _, _, line in touching] + [line for m in sorted(members) for line in about.get(m, [])] + other
        runs = {}
        for variant, subclass in (("", kept), ("-all-subclass", everything)):
            directory = ROOT / "data" / f"sample-{name}{variant}"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "asserted.nt").write_text("".join(sorted(x + "\n" for x in set(facts) | set(subclass))),
                                                   encoding="utf-8")
            code, last = run(ROOT / "tools" / "run_pipeline.py", directory / "asserted.nt")
            out = sorted((ROOT / "results" / "pipeline" / directory.name).iterdir())[-1]
            check_code, check_last = run(ROOT / "tools" / "check_cons.py", directory / "asserted.nt", out)
            runs[variant] = {"run": str(out.relative_to(ROOT)), "pipeline": last, "check": check_last,
                             "check_agrees": check_code == 0, "record": json.loads((out / "run.json").read_text())}
        a, b = (ROOT / runs[""]["run"]), (ROOT / runs["-all-subclass"]["run"])
        same = {f: (a / f).read_bytes() == (b / f).read_bytes() for f in COMPARED}
        result = {
            "sampled_parties": len(sample), "spouse_triples": len(touching), "parties_in_those_triples": len(members),
            "identical": same, "all_identical": all(same.values()),
            "kept": {"run": runs[""]["run"], "K": runs[""]["record"]["K"], "Cons": runs[""]["record"]["Cons"],
                     "check_agrees": runs[""]["check_agrees"],
                     "incompatibilities_at_K": runs[""]["record"]["select_rows"]["2-incompatibilities"],
                     "incompatibilities_over_Cons": runs[""]["record"]["select_rows"]["4-recheck"]},
            "all_subclass": {"run": runs["-all-subclass"]["run"], "K": runs["-all-subclass"]["record"]["K"],
                             "Cons": runs["-all-subclass"]["record"]["Cons"],
                             "check_agrees": runs["-all-subclass"]["check_agrees"]},
        }
        summary["samples"][name] = result
        (ROOT / "results" / "pipeline" / f"sample-{name}" / "comparison.json").write_text(
            json.dumps({**{k: v for k, v in summary.items() if k != "samples"}, **result}, indent=2) + "\n",
            encoding="utf-8")
        print(f"{name}: {len(touching)} spouse triples, {len(members)} parties; entry-level results identical: "
              f"{result['all_identical']}; checks agree: {result['kept']['check_agrees']} and "
              f"{result['all_subclass']['check_agrees']}; K {result['kept']['K']} against {result['all_subclass']['K']}; "
              f"incompatibilities at K {result['kept']['incompatibilities_at_K']}, "
              f"over Cons {result['kept']['incompatibilities_over_Cons']}")
    sys.exit(0 if all(r["all_identical"] for r in summary["samples"].values()) else 1)


if __name__ == "__main__":
    main()
