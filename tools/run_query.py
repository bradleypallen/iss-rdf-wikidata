#!/usr/bin/env python3
"""Run one saved SPARQL query and save the result with the time it was run.

    WDQS_USER_AGENT='...' python3 tools/run_query.py queries/p26-constraints.rq

Writes, under results/<query name>/:

    <UTC timestamp>.json        the response body, byte for byte (.ttl with --format ttl)
    <UTC timestamp>.meta.json   query text and hash, endpoint, start and end time,
                                HTTP status, row count, hash of the body

and appends one line per run, failed runs included, to logs/runs.jsonl.

The User-Agent is read from the environment variable WDQS_USER_AGENT and is
never written to disk: it carries contact details. Standard library only.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINT = "https://query.wikidata.org/sparql"
ACCEPT = {"json": "application/sparql-results+json", "ttl": "text/turtle"}
KEPT_HEADERS = ("Date", "Content-Type", "Server", "X-Served-By", "Retry-After")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(t):
    return t.strftime("%Y%m%dT%H%M%SZ")


def relative(path):
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def count_rows(body, fmt):
    """Rows of a SELECT result, or the boolean of an ASK; None otherwise."""
    if fmt != "json":
        return None
    try:
        doc = json.loads(body)
    except ValueError:
        return None
    if "boolean" in doc:
        return doc["boolean"]
    return len(doc.get("results", {}).get("bindings", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", type=pathlib.Path, help="a .rq file under queries/")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--format", choices=sorted(ACCEPT), default="json",
                    help="json for SELECT and ASK, ttl for CONSTRUCT")
    ap.add_argument("--timeout", type=float, default=90.0, help="seconds")
    ap.add_argument("--results-dir", type=pathlib.Path, default=ROOT / "results")
    ap.add_argument("--log", type=pathlib.Path, default=ROOT / "logs" / "runs.jsonl")
    args = ap.parse_args()

    user_agent = os.environ.get("WDQS_USER_AGENT", "").strip()
    if not user_agent:
        sys.exit("WDQS_USER_AGENT is not set. The query service asks for a "
                 "descriptive User-Agent with contact details; set it in the "
                 "environment (it is not stored).")

    query_text = args.query.read_text(encoding="utf-8")
    out_dir = args.results_dir / args.query.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        args.endpoint,
        data=urllib.parse.urlencode({"query": query_text}).encode("utf-8"),
        headers={"Accept": ACCEPT[args.format], "User-Agent": user_agent},
        method="POST",
    )

    started = utc_now()
    clock = time.monotonic()
    status, headers, body, error = None, {}, b"", None
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            status, headers, body = response.status, response.headers, response.read()
    except urllib.error.HTTPError as e:
        status, headers, body = e.code, e.headers, e.read()
        error = f"HTTP {e.code} {e.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        error = f"{type(e).__name__}: {e}"
    seconds = round(time.monotonic() - clock, 3)
    finished = utc_now()

    ok = error is None
    base = out_dir / stamp(started)
    body_path = base.with_suffix("." + args.format if ok else ".error.txt")
    if body:
        body_path.write_bytes(body)

    record = {
        "query_file": relative(args.query),
        "query_sha256": hashlib.sha256(query_text.encode("utf-8")).hexdigest(),
        "endpoint": args.endpoint,
        "accept": ACCEPT[args.format],
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "seconds": seconds,
        "http_status": status,
        "ok": ok,
        "error": error,
        "rows": count_rows(body, args.format) if ok else None,
        "body_file": relative(body_path) if body else None,
        "body_bytes": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest() if body else None,
        "response_headers": {h: headers[h] for h in KEPT_HEADERS if headers.get(h)},
    }
    meta_path = pathlib.Path(str(base) + ".meta.json")
    meta_path.write_text(
        json.dumps({**record, "query": query_text}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    with args.log.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{'ok' if ok else 'FAILED'}  {record['query_file']}  {record['started_utc']}  "
          f"status={status}  rows={record['rows']}  {seconds}s  -> {relative(meta_path)}"
          + ("" if ok else f"  ({error})"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
