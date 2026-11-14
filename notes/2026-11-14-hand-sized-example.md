# The hand-sized example, end to end

Dated note, Saturday 14 November 2026. All times are UTC. Everything here can be
regenerated from files in this repository; the last section lists them.

Each statement below is marked by what it rests on: **live** (Wikidata on the stated time),
**checker** (Wikidata's own constraint checker, through its API, on the stated time),
**documentation**, or **ours** (a stipulation or an encoding of the entries).

## 1. What the constraint checker itself says

The constraint-check API (`action=wbcheckconstraints` on wikidata.org) is available without
logging in. Requests of 16:43:46 to 16:43:51 (`results/checker-p26-name-values`,
`results/checker-p26-lifetimes`, `results/checker-p47-exceptions`).

| Question | Answer (checker) | Shown by |
|---|---|---|
| a. Does the contemporary constraint pass when a date is absent? | Yes. | `compliance` on Zechariah → Elizabeth (given name), Rudolf Vrba → Robin, Jonas Prapiestis → Regina; the values have no dates. Control: `warning` on George Key → Kerry Katona and on Berta Gerster → Fritz Reiner, where the dates do not overlap. |
| b. Is an exception to a symmetric constraint read on the subject? | Yes. | `exception` on the P47 statements of Numbani and of Belgorod People's Republic, both listed. `warning` on Geta → international waters, where the listed item is the value. |
| c. What is reported on the name-value pairs? | The symmetric constraint only. | On all three statements: `warning` for symmetric; `compliance` for conflicts-with, subject type, contemporary and the three none-of constraints. |

Also seen in the same responses:

* A violation of these constraints is reported with status `warning`; none of them is mandatory.
* On a spouse statement whose value is an unknown value, the checker reports `compliance`
  for the symmetric constraint (David Von Erich, two statements).
* The API's help text describes `exception` as "the subject entity of the statement is a
  known exception to the constraint" (documentation; agrees with b).

## 2. The cases and the subset

Fourteen items, chosen from the saved results of earlier queries.

| Case asked for | Items | Why these |
|---|---|---|
| Reciprocated spouse pair | Marie Curie (Q7186), Pierre Curie (Q37463) | Each has the other as its only spouse triple. |
| Missing reverse, both typed | Elizabeth (Q235849) → Zechariah (Q139464) | No reverse triple; both are instances of human biblical figure. |
| One of the 206 | Zechariah (Q139464) → Elizabeth (Q385468) | Q385468 is the female given name, not a person. |
| Unknown-value spouse | David Von Erich (Q2139951) | Two spouse statements, each with an unknown value. |
| Non-overlapping lifetimes | Berta Gerster (Q112829435), Fritz Reiner (Q364179) | Her recorded death, 1885, precedes his birth, 1888. The checker flags both statements. Her date of birth is an unknown value. |
| (added) Entries and checker disagree | Elisabeth Magdalene von Brandenburg (Q1330110), Francis Otto, Duke of Brunswick-Lüneburg (Q72936) | One of her two recorded deaths, 1529, precedes his birth, 1530. The checker does not flag this pair; see section 6. |
| P47 exception item | Numbani (Q81810310) → Nigeria (Q1033) | Numbani is a listed exception. Geta (Q134675) → international waters (Q25855) is added as the contrast: the listed item is the value. |

The subset is `data/hand-sized/asserted.nt`, 65 triples, built by
`tools/build_subset.py` from four query results of 17:01:45 to 17:01:53 (live):

* **Taken** (57 triples, `hand-sized-facts`): spouse and shares-border-with triples
  between two of the fourteen items; spouse triples from an item to an unknown value;
  instance of, date of birth and date of death of each item; for P26 and P47, the symmetric
  constraint statement and its listed exceptions.
* **Subclass triples** (`hand-sized-subclass-paths`): 365 P279
  triples lie above the classes of the fourteen items. 8 are kept,
  those on a path to one of the 15 classes that an entry names.
* **Left out** (23 triples, `hand-sized-touching-edges`):
  every spouse or border triple with exactly one end among the fourteen. All
  23 are P47 triples of Nigeria, Geta and international
  waters; no spouse triple of any of the fourteen is left out. They are listed in
  `data/hand-sized/PROVENANCE.json`.

**Closed for the entries.** Every triple that a premise, defeater or guard of an entry can
match on these fourteen items is in the subset, with one qualification: the regime's rules
can also read the 357 subclass
triples that were not kept. Those lead to no class an entry names. This was checked by
running the pipeline on `data/hand-sized-all-subclass/asserted.nt` (422
triples, all subclass triples kept): the default conclusions, the defeated instances, the
incompatibilities at K and over Cons, and the spouse answers are identical to those of the
subset (K has 6967 triples there, against 92).

The subset, with labels added for reading:

```
wd:P26 (spouse)  p:P2302  wds:P26-75392F51-A753-4451-B057-4C2719462EFB
wd:P47 (shares border with)  p:P2302  wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927
wd:Q1033 (Nigeria)  wdt:P31  wd:Q3624078 (sovereign state)
wd:Q1033 (Nigeria)  wdt:P31  wd:Q512187 (federal republic)
wd:Q1033 (Nigeria)  wdt:P31  wd:Q6256 (country)
wd:Q112829435 (Berta Gerster)  wdt:P26  wd:Q364179 (Fritz Reiner)
wd:Q112829435 (Berta Gerster)  wdt:P31  wd:Q5 (human)
wd:Q112829435 (Berta Gerster)  wdt:P569  unknown-value:b755e0
wd:Q112829435 (Berta Gerster)  wdt:P570  "1885-04-26T00:00:00Z"
wd:Q11879590 (female given name)  wdt:P279  wd:Q202444 (given name)
wd:Q12405827 (biblical character)  wdt:P279  wd:Q18563354 (religious character)
wd:Q12405827 (biblical character)  wdt:P279  wd:Q4271324 (mythical character)
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P26  wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P31  wd:Q5 (human)
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P569  "1528-01-01T00:00:00Z"
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P569  "1537-11-06T00:00:00Z"
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P570  "1529-08-20T00:00:00Z"
wd:Q1330110 (Elisabeth Magdalene von Brandenburg)  wdt:P570  "1595-09-01T00:00:00Z"
wd:Q134675 (Geta)  wdt:P31  wd:Q856076 (municipality of Finland)
wd:Q134675 (Geta)  wdt:P47  wd:Q25855 (international waters)
wd:Q139464 (Zechariah)  wdt:P26  wd:Q385468 (Elizabeth)
wd:Q139464 (Zechariah)  wdt:P31  wd:Q20643955 (human biblical figure)
wd:Q139464 (Zechariah)  wdt:P569  "-0100-01-01T00:00:00Z"
wd:Q139464 (Zechariah)  wdt:P570  "0100-01-01T00:00:00Z"
wd:Q18563354 (religious character)  wdt:P279  wd:Q13002315 (legendary figure)
wd:Q20643955 (human biblical figure)  wdt:P279  wd:Q12405827 (biblical character)
wd:Q2139951 (David Von Erich)  wdt:P26  unknown-value:e8d7de
wd:Q2139951 (David Von Erich)  wdt:P26  unknown-value:ddc353
wd:Q2139951 (David Von Erich)  wdt:P31  wd:Q5 (human)
wd:Q2139951 (David Von Erich)  wdt:P569  "1958-07-22T00:00:00Z"
wd:Q2139951 (David Von Erich)  wdt:P570  "1984-02-09T00:00:00Z"
wd:Q2139951 (David Von Erich)  wdt:P570  "1984-02-10T00:00:00Z"
wd:Q2250224 (individual person)  wdt:P279  wd:Q215627 (person)
wd:Q235849 (Elizabeth)  wdt:P26  wd:Q139464 (Zechariah)
wd:Q235849 (Elizabeth)  wdt:P31  wd:Q20643955 (human biblical figure)
wd:Q235849 (Elizabeth)  wdt:P569  "-0100-01-01T00:00:00Z"
wd:Q235849 (Elizabeth)  wdt:P570  "0100-01-01T00:00:00Z"
wd:Q25855 (international waters)  wdt:P31  wd:Q56061 (administrative territorial entity)
wd:Q364179 (Fritz Reiner)  wdt:P26  wd:Q112829435 (Berta Gerster)
wd:Q364179 (Fritz Reiner)  wdt:P31  wd:Q5 (human)
wd:Q364179 (Fritz Reiner)  wdt:P569  "1888-12-19T00:00:00Z"
wd:Q364179 (Fritz Reiner)  wdt:P570  "1963-11-15T00:00:00Z"
wd:Q37463 (Pierre Curie)  wdt:P26  wd:Q7186 (Marie Curie)
wd:Q37463 (Pierre Curie)  wdt:P31  wd:Q5 (human)
wd:Q37463 (Pierre Curie)  wdt:P569  "1859-05-15T00:00:00Z"
wd:Q37463 (Pierre Curie)  wdt:P570  "1906-04-19T00:00:00Z"
wd:Q385468 (Elizabeth)  wdt:P31  wd:Q11879590 (female given name)
wd:Q5 (human)  wdt:P279  wd:Q215627 (person)
wd:Q5 (human)  wdt:P279  wd:Q2250224 (individual person)
wd:Q7186 (Marie Curie)  wdt:P26  wd:Q37463 (Pierre Curie)
wd:Q7186 (Marie Curie)  wdt:P31  wd:Q5 (human)
wd:Q7186 (Marie Curie)  wdt:P569  "1867-11-07T00:00:00Z"
wd:Q7186 (Marie Curie)  wdt:P570  "1934-07-04T00:00:00Z"
wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)  wdt:P26  wd:Q1330110 (Elisabeth Magdalene von Brandenburg)
wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)  wdt:P31  wd:Q5 (human)
wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)  wdt:P569  "1530-06-30T00:00:00Z"
wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)  wdt:P570  "1559-05-09T00:00:00Z"
wd:Q81810310 (Numbani)  wdt:P31  wd:Q1145276 (fictional country)
wd:Q81810310 (Numbani)  wdt:P31  wd:Q1964689 (fictional city)
wd:Q81810310 (Numbani)  wdt:P47  wd:Q1033 (Nigeria)
wds:P26-75392F51-A753-4451-B057-4C2719462EFB  ps:P2302  wd:Q21510862 (symmetric constraint)
wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927  pq:P2303  wd:Q118629252
wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927  pq:P2303  wd:Q25855 (international waters)
wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927  pq:P2303  wd:Q81810310 (Numbani)
wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927  ps:P2302  wd:Q21510862 (symmetric constraint)
```

Data retrieved from Wikidata is in the public domain under CC0 1.0.

## 3. The pipeline

Run of 2026-11-14T17:03:54+00:00 on a local Oxigraph store (pyoxigraph 0.5.11), by
`tools/run_pipeline.py`. All reasoning is in the nine SPARQL files of `pipeline/`, which
`tools/make_pipeline.py` writes from `entries/entries.json` (two rules, nine entries).

| Step | File | What it does | Result |
|---|---|---|---|
| 0 | (loading) | Load the subset into `:asserted`. No blank node occurs; Wikidata's unknown values arrive as Skolem IRIs. | 65 triples |
| 1 | `1-closure.rq` | The regime's two rules, repeated until nothing is added, into `:closure`. | 27 triples added; K has 92 |
| 2 | `2-defaults.rq` | One round of the two default entries against K only, into `:defaults`. | D* has 11 triples |
| 2 | `2-incompatibilities.rq` | The incompatibility entries that apply at K. | 4 instances |
| 3 | `3-default-closure.rq` | The rules again over K with D*, into `:default-closure`. | 0 triples added; Cons has 97 |
| 4 | `4-recheck.rq` | The incompatibility entries over Cons. | 9 instances, of which 5 are not at K |

Two more files, `2-default-instances.rq` and `2-defeated.rq`, list for the report the
default instances that apply and those that are defeated. `q-spouse-of-at-closure.rq` and
`q-spouse-of-at-cons.rq` ask who has whom as spouse over K and over Cons.

Things to know about the run:

* The repetition of step 1 and step 3 to a fixed point is a loop in the runner, not SPARQL.
* Step 4 reads both premises and defeaters in Cons. For these entries reading defeaters in
  K gives the same result, since no default and no rule produces a triple a defeater reads.
* The store returns a row once per named graph in which a matching triple sits, so the
  SELECT files say `DISTINCT` and the rules add only triples not yet present. Earlier runs
  (16:54:31 to 17:02:08), on a first subset without Berta Gerster and Fritz Reiner or
  before changes to the generated files and to the notes in the entries file, were
  superseded and their output removed; `logs/pipeline.jsonl` keeps a line for each.

## 4. Results per instance

K is incoherent: four incompatibility instances apply at K, two on Berta Gerster and Fritz
Reiner and two on Elisabeth Magdalene von Brandenburg and Francis Otto. Each names the
spouse triple and the two dates it applies to. Nothing else is affected: with the triples
of those four items removed, the pipeline draws the same seven default conclusions for the
other cases (checked by a run on the reduced file).

Of the 11 default conclusions, 6 are already in K,
2 are new and clean, 1 is new and in
conflict, and 2 are new, in conflict, and involve an unknown
value. 1 default instance is defeated.

Berta Gerster's date of birth is an unknown value. The date guard does not apply to it, in
the SPARQL and in the independent check alike, so it gives rise to no instance.


#### Instances with no unknown value

**Default conclusions not already in K: clean**

| Entry | Premises | Conclusion |
|---|---|---|
| p26-symmetric | wd:Q235849 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) | wd:Q139464 (Zechariah) wdt:P26 wd:Q235849 (Elizabeth) |
| p47-symmetric | wd:Q134675 (Geta) wdt:P47 wd:Q25855 (international waters) | wd:Q25855 (international waters) wdt:P47 wd:Q134675 (Geta) |

**Default conclusions not already in K: in conflict**

| Entry | Premises | Conclusion | Incompatibility that applies over Cons, and its premises |
|---|---|---|---|
| p26-symmetric | wd:Q139464 (Zechariah) wdt:P26 wd:Q385468 (Elizabeth) | wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) | p26-conflicts-with: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah)<br>wd:Q385468 (Elizabeth) wdt:P31 wd:Q11879590 (female given name)<br>p26-conflicts-with: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah)<br>wd:Q385468 (Elizabeth) wdt:P31 wd:Q202444 (given name)<br>p26-subject-type: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) |

**Defeated default instances**

| Entry | Premises | Conclusion not drawn | Defeater triples in K |
|---|---|---|---|
| p47-symmetric | wd:Q81810310 (Numbani) wdt:P47 wd:Q1033 (Nigeria) | wd:Q1033 (Nigeria) wdt:P47 wd:Q81810310 (Numbani) | wd:P47 (shares border with) p:P2302 wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927<br>wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927 ps:P2302 wd:Q21510862 (symmetric constraint)<br>wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927 pq:P2303 wd:Q81810310 (Numbani) |

**Incompatibilities at K**

| Entry | Triples it applies to |
|---|---|
| p26-contemporary-subject-first | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner)<br>wd:Q112829435 (Berta Gerster) wdt:P570 1885-04-26T00:00:00Z<br>wd:Q364179 (Fritz Reiner) wdt:P569 1888-12-19T00:00:00Z |
| p26-contemporary-subject-first | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)<br>wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P570 1529-08-20T00:00:00Z<br>wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P569 1530-06-30T00:00:00Z |
| p26-contemporary-value-first | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster)<br>wd:Q112829435 (Berta Gerster) wdt:P570 1885-04-26T00:00:00Z<br>wd:Q364179 (Fritz Reiner) wdt:P569 1888-12-19T00:00:00Z |
| p26-contemporary-value-first | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg)<br>wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P570 1529-08-20T00:00:00Z<br>wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P569 1530-06-30T00:00:00Z |

**Default conclusions already in K**

| Entry | Premises | Conclusion |
|---|---|---|
| p26-symmetric | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner) | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster) |
| p26-symmetric | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg) |
| p26-symmetric | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster) | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner) |
| p26-symmetric | wd:Q37463 (Pierre Curie) wdt:P26 wd:Q7186 (Marie Curie) | wd:Q7186 (Marie Curie) wdt:P26 wd:Q37463 (Pierre Curie) |
| p26-symmetric | wd:Q7186 (Marie Curie) wdt:P26 wd:Q37463 (Pierre Curie) | wd:Q37463 (Pierre Curie) wdt:P26 wd:Q7186 (Marie Curie) |
| p26-symmetric | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg) | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) |

#### Instances with an unknown value (Skolem IRI)

**Default conclusions not already in K: clean**

None.

**Default conclusions not already in K: in conflict**

| Entry | Premises | Conclusion | Incompatibility that applies over Cons, and its premises |
|---|---|---|---|
| p26-symmetric | wd:Q2139951 (David Von Erich) wdt:P26 unknown value …ddc353 | unknown value …ddc353 wdt:P26 wd:Q2139951 (David Von Erich) | p26-subject-type: unknown value …ddc353 wdt:P26 wd:Q2139951 (David Von Erich) |
| p26-symmetric | wd:Q2139951 (David Von Erich) wdt:P26 unknown value …e8d7de | unknown value …e8d7de wdt:P26 wd:Q2139951 (David Von Erich) | p26-subject-type: unknown value …e8d7de wdt:P26 wd:Q2139951 (David Von Erich) |

**Defeated default instances**

None.

**Incompatibilities at K**

None.

**Default conclusions already in K**

None.

#### Answers to "who has whom as spouse" that are in Cons and not in K

| Who | has as spouse |
|---|---|
| unknown value …ddc353 | wd:Q2139951 (David Von Erich) |
| unknown value …e8d7de | wd:Q2139951 (David Von Erich) |
| wd:Q139464 (Zechariah) | wd:Q235849 (Elizabeth) |
| wd:Q385468 (Elizabeth) | wd:Q139464 (Zechariah) |

The last table answers "who has David Von Erich as spouse?" over Cons with two Skolem
terms, one for each unknown value; over K the question has no answer.

## 5. Independent check

`tools/check_cons.py` computes K, D*, Cons and the incompatibility instances from the
definition, in Python, reading `entries/entries.json` and the N-Triples file. It uses no
SPARQL and no store and imports nothing from the other tools.

| Compared | Subset | All-subclass set |
|---|---|---|
| Sizes from the definition | K 92; D* 11; Cons 97; incompatibilities at K 4; incompatibilities over Cons 9 | K 6967; D* 11; Cons 6972; incompatibilities at K 4; incompatibilities over Cons 9 |
| Agrees with the pipeline on all five | yes | yes |

The check was also run on a made-up fixture with a tampered pipeline output (one default
conclusion and one conflict removed), and reported both.

## 6. The entries against the checker, statement by statement

Checker response of 17:01:56 (`results/checker-hand-sized`), restricted to the seven P26
constraints that have entries and the symmetric constraint on P47. "Compliant" counts the
constraints reported as `compliance` on that statement.

| Entity | Property | Statement | Not compliant | Compliant |
|---|---|---|---|---|
| Q7186 (Marie Curie) | P26 | …28993D | none | 7 |
| Q37463 (Pierre Curie) | P26 | …F8C984 | none | 7 |
| Q235849 (Elizabeth) | P26 | …e52c07 | warning: symmetric constraint — Zechariah should also have the symmetric statement spouse Elizabeth. | 6 |
| Q139464 (Zechariah) | P26 | …43519c | warning: symmetric constraint — Elizabeth should also have the symmetric statement spouse Zechariah. | 6 |
| Q385468 (Elizabeth) | | no statement checked | | |
| Q2139951 (David Von Erich) | P26 | …a17929 | none | 7 |
| Q2139951 (David Von Erich) | P26 | …3fccb7 | none | 7 |
| Q1330110 (Elisabeth Magdalene von Brandenburg) | P26 | …fe4e4e | none | 7 |
| Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) | P26 | …b41620 | none | 7 |
| Q112829435 (Berta Gerster) | P26 | …8da668 | warning: contemporary constraint — The entities Berta Gerster and Fritz Reiner should be contemporary to be linked through spouse, but the latest end value of Berta Gerster is 26 April 1885Gregorian and the earliest start value of Fritz Reiner is 19 December 1888Gregorian. | 6 |
| Q364179 (Fritz Reiner) | P26 | …2991AB | warning: contemporary constraint — The entities Fritz Reiner and Berta Gerster should be contemporary to be linked through spouse, but the latest end value of Berta Gerster is 26 April 1885Gregorian and the earliest start value of Fritz Reiner is 19 December 1888Gregorian. | 6 |
| Q81810310 (Numbani) | P47 | …522c0b | exception: symmetric constraint — This entity is a known exception for this constraint and has been marked as such. | 0 |
| Q1033 (Nigeria) | P47 | …898e43 | none | 1 |
| Q1033 (Nigeria) | P47 | …D2F87E | none | 1 |
| Q1033 (Nigeria) | P47 | …732FF7 | none | 1 |
| Q1033 (Nigeria) | P47 | …B29CFB | none | 1 |
| Q1033 (Nigeria) | P47 | …B491C9 | none | 1 |
| Q134675 (Geta) | P47 | …4a4ff7 | warning: symmetric constraint — international waters should also have the symmetric statement shares border with Geta. | 0 |
| Q134675 (Geta) | P47 | …06d2bf | none | 1 |
| Q134675 (Geta) | P47 | …e111fa | none | 1 |
| Q134675 (Geta) | P47 | …d8b329 | none | 1 |
| Q25855 (international waters) | | no statement checked | | |

| Statement | Checker | Entries | Same? |
|---|---|---|---|
| Marie Curie ↔ Pierre Curie | nothing | nothing at K; both default conclusions already in K | yes |
| Elizabeth (Q235849) → Zechariah | symmetric `warning` | default conclusion drawn, clean | yes, reading a violation as a default consequence (ours) |
| Zechariah → Elizabeth (given name) | symmetric `warning` only | default conclusion drawn; nothing at K; over Cons, conflicts-with (twice) and subject type apply to the conclusion | yes at K; the conflict over Cons has no counterpart in the checker |
| Numbani → Nigeria | symmetric `exception` | default defeated | yes |
| Geta → international waters | symmetric `warning` | default conclusion drawn, clean | yes |
| Berta Gerster ↔ Fritz Reiner | contemporary `warning` on both statements | contemporary applies at K in both directions (death 1885-04-26 before birth 1888-12-19) | yes |

Kept apart, as asked:

| Statement | Checker | Entries | Same? |
|---|---|---|---|
| **Unknown value.** David Von Erich → unknown value (two statements) | nothing; symmetric is `compliance` | a default conclusion for each, with a Skolem subject, in conflict over Cons with subject type | **no** |
| **Several dates.** Elisabeth Magdalene von Brandenburg ↔ Francis Otto | nothing; contemporary is `compliance` | contemporary applies at K in both directions (death 1529-08-20 before birth 1530-06-30) | **no** |

On the second: Elisabeth Magdalene has two dates of death (1529-08-20 and 1595-09-01) and
two dates of birth. The contemporary entries apply when *some* date of death precedes
*some* date of birth of the other party. The checker's message on Berta Gerster and Fritz
Reiner says it compares "the latest end value" of one with "the earliest start value" of
the other, and it reports compliance here, where the latest death is 1595. So the two
agree when each party has one date and can differ when a party has several.

## 7. What rests on what

Confirmed by the checker (section 1): contemporary passes when a date is absent; a
symmetric exception is read on the subject; on the name-value pairs only the symmetric
constraint is reported.

Still from documentation or inference, not confirmed:

* Which date properties the contemporary constraint uses. The entries use date of birth
  and date of death only. (That it compares the latest end with the earliest start is in
  the checker's own message, section 6.)
* Whether the checker follows subclass-of for the conflicts-with constraint. Of the two
  conflicts-with instances on the given name Elizabeth, the one for "female given name" is
  a direct instance-of triple; the one for "given name" exists only through the regime's
  rule.

Ours:

* Reading a symmetric-constraint violation as a default consequence.
* Writing the subject type constraint as an incompatibility with the allowed types as
  defeaters. With the regime's rules it agrees with the checker on every typed subject
  here; Elizabeth (Q235849) and Zechariah are typed only through two subclass steps (human
  biblical figure, biblical character, mythical character).
* Applying the symmetric default when the value is an unknown value.
* The conflicts over Cons (the third status). The checker has nothing corresponding.

Not compared with any earlier published count: the missing-reverse figures in this
repository are counted over best-rank direct triples and are not on the same basis.

## 8. Open points

1. **Several dates.** On Elisabeth Magdalene von Brandenburg and Francis Otto the entries
   report an incompatibility and the checker does not. Making the contemporary entries
   compare the latest end with the earliest start needs a guard inside a defeater, which
   is an extension of the entry format. Left as it is, the entries are stricter than the
   checker whenever a party has several dates.
2. **Unknown values.** The entry draws a conclusion where the checker reports nothing.
3. **Date precision.** Zechariah and Elizabeth (Q235849) carry the dates -0100-01-01 and
   0100-01-01, which look like century precision. Direct triples carry no precision.

## Files

| What | Where |
|---|---|
| Entries and regime | `entries/entries.json`; listing by `python3 tools/entries.py list` |
| Pipeline | `pipeline/*.rq`, written by `tools/make_pipeline.py` |
| Subset and provenance | `data/hand-sized/asserted.nt`, `PROVENANCE.json`, `labels.json`; built by `tools/build_subset.py` |
| Comparison subset | `data/hand-sized-all-subclass/asserted.nt` |
| Pipeline runs | `results/pipeline/hand-sized/20261114T170354Z` (this note), `results/pipeline/hand-sized-all-subclass/20261114T170354Z` (comparison); `logs/pipeline.jsonl` |
| Independent check | `tools/check_cons.py`; `check.json` in each run directory |
| Checker responses | `results/checker-*/`; table by `tools/checker_summary.py` |
| Wikidata queries and runs | `queries/`, `results/`, `logs/runs.jsonl` |

To regenerate from the saved results:

```sh
python3 tools/build_subset.py
python3 tools/run_pipeline.py data/hand-sized/asserted.nt --labels data/hand-sized/labels.json
python3 tools/check_cons.py data/hand-sized/asserted.nt results/pipeline/hand-sized/<timestamp>
```
