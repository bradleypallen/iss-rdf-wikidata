## Pipeline run 2026-11-14T17:03:54+00:00

Data: `data/hand-sized/asserted.nt` (65 triples). K has 92 triples, D* has 11, Cons has 97.

### Instances with no unknown value

#### Default conclusions not already in K: clean

| Entry | Premises | Conclusion |
|---|---|---|
| p26-symmetric | wd:Q235849 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) | wd:Q139464 (Zechariah) wdt:P26 wd:Q235849 (Elizabeth) |
| p47-symmetric | wd:Q134675 (Geta) wdt:P47 wd:Q25855 (international waters) | wd:Q25855 (international waters) wdt:P47 wd:Q134675 (Geta) |

#### Default conclusions not already in K: in conflict

| Entry | Premises | Conclusion | Incompatibility that applies over Cons, and its premises |
|---|---|---|---|
| p26-symmetric | wd:Q139464 (Zechariah) wdt:P26 wd:Q385468 (Elizabeth) | wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) | p26-conflicts-with: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah)<br>wd:Q385468 (Elizabeth) wdt:P31 wd:Q11879590 (female given name)<br>p26-conflicts-with: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah)<br>wd:Q385468 (Elizabeth) wdt:P31 wd:Q202444 (given name)<br>p26-subject-type: wd:Q385468 (Elizabeth) wdt:P26 wd:Q139464 (Zechariah) |

#### Defeated default instances

| Entry | Premises | Conclusion not drawn | Defeater triples in K |
|---|---|---|---|
| p47-symmetric | wd:Q81810310 (Numbani) wdt:P47 wd:Q1033 (Nigeria) | wd:Q1033 (Nigeria) wdt:P47 wd:Q81810310 (Numbani) | wd:P47 (shares border with) p:P2302 wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927<br>wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927 ps:P2302 wd:Q21510862 (symmetric constraint)<br>wds:P47-BDC21597-C3FC-417A-9437-E4B7FA4C7927 pq:P2303 wd:Q81810310 (Numbani) |

#### Incompatibilities at K

| Entry | Triples it applies to |
|---|---|
| p26-contemporary-subject-first | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner)<br>wd:Q112829435 (Berta Gerster) wdt:P570 1885-04-26T00:00:00Z<br>wd:Q364179 (Fritz Reiner) wdt:P569 1888-12-19T00:00:00Z |
| p26-contemporary-subject-first | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg)<br>wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P570 1529-08-20T00:00:00Z<br>wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P569 1530-06-30T00:00:00Z |
| p26-contemporary-value-first | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster)<br>wd:Q112829435 (Berta Gerster) wdt:P570 1885-04-26T00:00:00Z<br>wd:Q364179 (Fritz Reiner) wdt:P569 1888-12-19T00:00:00Z |
| p26-contemporary-value-first | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg)<br>wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P570 1529-08-20T00:00:00Z<br>wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P569 1530-06-30T00:00:00Z |

#### Default conclusions already in K

| Entry | Premises | Conclusion |
|---|---|---|
| p26-symmetric | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner) | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster) |
| p26-symmetric | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg) |
| p26-symmetric | wd:Q364179 (Fritz Reiner) wdt:P26 wd:Q112829435 (Berta Gerster) | wd:Q112829435 (Berta Gerster) wdt:P26 wd:Q364179 (Fritz Reiner) |
| p26-symmetric | wd:Q37463 (Pierre Curie) wdt:P26 wd:Q7186 (Marie Curie) | wd:Q7186 (Marie Curie) wdt:P26 wd:Q37463 (Pierre Curie) |
| p26-symmetric | wd:Q7186 (Marie Curie) wdt:P26 wd:Q37463 (Pierre Curie) | wd:Q37463 (Pierre Curie) wdt:P26 wd:Q7186 (Marie Curie) |
| p26-symmetric | wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) wdt:P26 wd:Q1330110 (Elisabeth Magdalene von Brandenburg) | wd:Q1330110 (Elisabeth Magdalene von Brandenburg) wdt:P26 wd:Q72936 (Francis Otto, Duke of Brunswick-Lüneburg) |

### Instances with an unknown value (Skolem IRI)

#### Default conclusions not already in K: clean

None.

#### Default conclusions not already in K: in conflict

| Entry | Premises | Conclusion | Incompatibility that applies over Cons, and its premises |
|---|---|---|---|
| p26-symmetric | wd:Q2139951 (David Von Erich) wdt:P26 unknown value …ddc353 | unknown value …ddc353 wdt:P26 wd:Q2139951 (David Von Erich) | p26-subject-type: unknown value …ddc353 wdt:P26 wd:Q2139951 (David Von Erich) |
| p26-symmetric | wd:Q2139951 (David Von Erich) wdt:P26 unknown value …e8d7de | unknown value …e8d7de wdt:P26 wd:Q2139951 (David Von Erich) | p26-subject-type: unknown value …e8d7de wdt:P26 wd:Q2139951 (David Von Erich) |

#### Defeated default instances

None.

#### Incompatibilities at K

None.

#### Default conclusions already in K

None.

### Answers to "who has whom as spouse" that are in Cons and not in K

| Who | has as spouse |
|---|---|
| unknown value …ddc353 | wd:Q2139951 (David Von Erich) |
| unknown value …e8d7de | wd:Q2139951 (David Von Erich) |
| wd:Q139464 (Zechariah) | wd:Q235849 (Elizabeth) |
| wd:Q385468 (Elizabeth) | wd:Q139464 (Zechariah) |
