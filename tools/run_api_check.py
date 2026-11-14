#!/usr/bin/env python3
"""Ask Wikidata's own constraint checker about some entities and save the answer.

    WDQS_USER_AGENT='...' python3 tools/run_api_check.py queries/checker-p47-exceptions.api.json

The request is a file in queries/ ending in .api.json, with the parameters of
the wbcheckconstraints API module (id, claimid, constraintid, status; lists
are joined with '|'). The response body is saved as received under
results/<request name>/<UTC timestamp>.json with a .meta.json beside it, and
one line is appended to logs/runs.jsonl, as tools/run_query.py does.

The User-Agent is read from WDQS_USER_AGENT and is never written to disk.
Standard library only.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from run_query import KEPT_HEADERS, ROOT, relative, stamp, utc_now

API = "https://www.wikidata.org/w/api.php"
ALLOWED = ("id", "claimid", "constraintid", "status")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("request", type=pathlib.Path, help="a .api.json file under queries/")
    ap.add_argument("--api", default=API)
    ap.add_argument("--timeout", type=float, default=90.0, help="seconds")
    ap.add_argument("--results-dir", type=pathlib.Path, default=ROOT / "results")
    ap.add_argument("--log", type=pathlib.Path, default=ROOT / "logs" / "runs.jsonl")
    args = ap.parse_args()

    user_agent = os.environ.get("WDQS_USER_AGENT", "").strip()
    if not user_agent:
        sys.exit("WDQS_USER_AGENT is not set. Set it in the environment (it is not stored).")

    request_text = args.request.read_text(encoding="utf-8")
    spec = json.loads(request_text)
    params = {"action": "wbcheckconstraints", "format": "json", "formatversion": "2"}
    for key in ALLOWED:
        if key in spec:
            value = spec[key]
            params[key] = "|".join(value) if isinstance(value, list) else value
    url = args.api + "?" + urllib.parse.urlencode(params)

    name = args.request.name.removesuffix(".api.json")
    out_dir = args.results_dir / name
    out_dir.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
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

    entities = None
    if error is None:
        try:
            doc = json.loads(body)
            if "error" in doc:  # the API reports its own errors with HTTP 200
                error = f"API error {doc['error'].get('code')}: {doc['error'].get('info')}"
            else:
                entities = len(doc.get("wbcheckconstraints", {}))
        except ValueError:
            error = "response is not JSON"

    ok = error is None
    base = out_dir / stamp(started)
    body_path = base.with_suffix(".json" if ok else ".error.txt")
    if body:
        body_path.write_bytes(body)

    record = {
        "query_file": relative(args.request),
        "query_sha256": hashlib.sha256(request_text.encode("utf-8")).hexdigest(),
        "endpoint": args.api,
        "request_url": url,
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "seconds": seconds,
        "http_status": status,
        "ok": ok,
        "error": error,
        "rows": entities,
        "body_file": relative(body_path) if body else None,
        "body_bytes": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest() if body else None,
        "response_headers": {h: headers[h] for h in KEPT_HEADERS if headers.get(h)},
    }
    meta_path = pathlib.Path(str(base) + ".meta.json")
    meta_path.write_text(
        json.dumps({**record, "query": spec}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.log.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{'ok' if ok else 'FAILED'}  {record['query_file']}  {record['started_utc']}  "
          f"status={status}  entities={entities}  {seconds}s  -> {relative(meta_path)}"
          + ("" if ok else f"  ({error})"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
