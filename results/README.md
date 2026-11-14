# Results

One directory per query, named after the query file. Each run of
`tools/run_query.py` adds two files, named by the UTC time the run started:

* `<timestamp>.json` (or `.ttl`): the response body exactly as received.
* `<timestamp>.meta.json`: the query text and its SHA-256, the endpoint, start and end
  times, HTTP status, row count, and the SHA-256 of the body.

A failed run leaves a `.meta.json` and, if the server sent a body, a `.error.txt`.
Results are never edited or overwritten; a re-run adds a new pair.

Data retrieved from Wikidata is CC0 1.0.
