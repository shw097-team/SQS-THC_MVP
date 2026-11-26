The mount is read-only and `apply_patch` was rejected, so `40_OPS/b2_checker_round1_verdict.md` could not be created. No separate `-o` value was exposed. The verdict is below for whoever holds write authority.

---

# B2 separated checker — round 1

**Claim ceiling tested:** `ROW_SEMANTICS_AND_CLASS_MUTATION`  
**Result: NOT SUPPORTED as written.**

The underlying row data is actually strong: I independently verified all 1,465 `source_payload`s against the declared original sources, and all 1,465 `direct_clause_sha` values against the rebound parent. But the receipt's quadrant method, requiredness independence, pin reconciliation, NEG oracles and clause-identity declaration are wrong or vacuous.

## Frozen candidate and pins

`40_OPS/b2_candidate_freeze_20261126T141949.json` — 2,059 B, highest timestamp, own sha256 `9314320d…`.

Re-hashed every pinned artefact: **9/9 bytes + raw sha256 exact**.

| pinned path | bytes | sha prefix |
|---|---:|---|
| `b2_ops_qrows.py` | 5,680 | `b9bad6a1` |
| `b2_ops_qrows2.py` | 12,331 | `fc8784e1` |
| `b2_ops_tqaep.py` | 5,863 | `720477ba` |
| `b2_ops_tqaep2.py` | 10,729 | `5d5feca4` |
| `b2_parse.py` | 4,533 | `ae2c0208` |
| `b2_semantics.py` | 11,117 | `443b82c5` |
| `b1_locator_bindings.json` | 2,502 | `a8025e2f` |
| `b2_toolreadset_20261126T141706.json` | 2,649,780 | `450d30bd` |
| `b2_tqaep_20261126T141735.json` | 2,071,976 | `eb75ddd0` |

`candidate_digest` reproduces exactly over sorted `sha256<two spaces>path` lines, LF-joined, **no trailing LF**: `095ddf2591bf67676c977202f0b3697c858e0c260df94bd248889194fdb7bb96`.  
Spec: **8,016,371 B / `140de5bc…` exact**.  
Parent: **2,712,933 B / `d95c8ac6…` exact**.

## 1. Quadrant census — numbers correct, method claim false

Independently derived: **Q1 440 / Q2 513 / Q3 378 / Q4 54 = 1,385**. Non-Q = **80 = HARD 18 + E00_TECH 8 + TECH_ROUTE 54**. PASS.

But `all_three_signals_agree` is not what was run:

- `q_of()` has exactly **two** votes, `key_namespace_prefix` and `q_row_full_key` (`b2_semantics.py:218-232`); its own docstring says “two data-derived identity signals”.
- The named H4 signal is not implemented. Section 05 has only `05.KIND.HARD`, `05.KIND.E00_TECH`, `05.KIND.TECH_ROUTE`, `05.KIND.Q_SOURCE_ROW`; there is no per-quadrant section.
- The two implemented votes are collinear: for all 1,385 Q rows, `q_row.full_key == key` minus the final `::ROW=<n>` suffix. They are the same key prefix.
- There is a genuinely independent signal in `q_row.source_row`: disjoint ranges Q1 233–672, Q2 680–1192, Q3 1200–1577, Q4 1585–1638. It corroborates the counts, but the receipt did not use it.

The receipt's rule text also says “the 54 non-Q rows are HARD/E00_TECH/TECH_ROUTE”; it is **80**.

## 2. Requiredness — 18 HARD true, `disagreement_count = 0` vacuous

The 18 HARD units all carry `HARD` in `source_payload[1]`, match the original blueprint, and none is removed. That result is true as a data fact. It is not an independent check:

- **Q_SOURCE_ROW: 1,385 rows, literally self-compared.** `row_requiredness()` uses `norm_req(source_payload[2])` (`b2_semantics.py:190-191`); `independent_requiredness()` uses `norm_req(source_payload[2])` again (`b2_semantics.py:208-214`).
- **1,014 / 1,385 Q rows** have prose in column 2 (`SOFT/CONDITIONAL`, `REUSE_SELECTED`, `ADAPT_WHEEL`, `RESEARCH SLOT; …`). `requiredness_applicable()` returns false and `req_ok` is set true without comparison (`b2_ops_tqaep2.py:44-47,108-109`). The other **371** pass the same-field tautology.
- **TECH_ROUTE: 54 rows**, both sides constant `"ROUTE_ONLY"`, applicability false — skipped.
- **HARD: 18 rows**, `source_payload[1]` vs `HARD Requiredness` in the same unit's `input_rule` — cross-field, same unit.
- **E00_TECH: 8 rows**, `source_payload[2]` vs `selection=` in the same unit's `input_rule` — cross-field, same unit.

So **1,439 / 1,465** rows have no real requiredness check; **26** are same-unit cross-field only; **0 / 1,465** compare against the original source row. `disagreement_count = 0` is structurally guaranteed.

The POS record also does not expose `requiredness_applicable` or `requ_reason`, so the 1,014 skips are invisible (`b2_ops_tqaep2.py:108-121`).

**The Q4 premise is false:** in the frozen SPEC **0 Q4 rows are `EVAL_ONLY`**. The **17** `EVAL_ONLY` rows are all in **Q1**, alongside the 18 Q1 `HARD` rows. “Q4 EVAL_ONLY never downgrades Q1 HARD” describes a nonexistent set.

## 3. Pin reconciliation — historical 72 is reproducible; receipt wrong

The old predicate is recorded in the pinned old code: `pin = source_payload[5]` for every kind; count if `not pin or "UNBOUND" in pin` (`b2_ops_qrows.py:76-79`). Applying it:

| kind | count | why |
|---|---:|---|
| HARD | 16 | 16 pin texts contain `UNBOUND` |
| E00_TECH | 2 | `B2.U0023` has `EFFECT_UNBOUND`; `B2.U0026` has `EXECUTOR_UNBOUND` |
| TECH_ROUTE | 54 | `source_payload` has one element, so `[5]` is absent |
| **total** | **72** | |

The old receipt's `sample_unbound` first 20 matches this reconstruction exactly, and its own count is 72. The old TQAEP's **54** is exactly the old rows with no `pin`, all TECH_ROUTE. **Both historical numbers are true.**

The new receipt instead computes a per-kind predicate:

- `predicate_A = 645 = HARD 16 + Q_SOURCE_ROW 629`; `historical_72.hard_unbound` is set to 645, which is not HARD-only.
- `historical_72.measured = 645 + 54 = 699`, not 72.
- The conclusion says “16 + 54 = 70”, omitting the 2 E00 rows.
- “The old 72 cannot be rebuilt from the SPEC” is false; it is rebuilt above from the same SPEC and the pinned old code.
- The old 72 is still a semantically poor pin count (2 E00 status sentinels, 54 missing columns). A clean no-version count is **1,407** (16 HARD + 5 E00 + 54 route + 1,332 Q).

## 4. NEG class mutations

Counts are real: **1,385 / 72 / 8**, 1,465 NEG PASS, 0 null `first_fail`. Semantics are mixed.

### `NAMESPACE_JOIN_DENY` — 1,385 — non-discriminating

- Baseline: exact-key join returns exactly **1** row for all 1,385 Q rows.
- Naive suffix lookup returns exactly **1** for all 1,385 (all tails unique), so it would have matched.
- But `join_rows` denies purely on selector shape: `if set(selector) != {"key"}: raise OracleError("NAMESPACE_JOIN_DENY")` (`b2_semantics.py:246-247`). It never inspects the tail.

Direct probes:

| selector | result |
|---|---|
| `{"key": exact Q key}` | 1 row |
| `{"suffix": tail}` | `NAMESPACE_JOIN_DENY` |
| `{"suffix": "garbage"}` | `NAMESPACE_JOIN_DENY` |
| `{}` | `NAMESPACE_JOIN_DENY` |
| `{"key": tail without Q namespace}` | `[]`, not DENY |
| `{"key": "WRONG-NS::"+tail}` | `[]`, not DENY |

So the oracle returns the expected code for **any selector not exactly `{"key": …}`**, while a wrong namespace with `::` is not denied. The 1,385 PASS do not test namespace identity. `baseline_first_fail` is also the integer `1` (a row count) in a field named “first_fail” (`b2_ops_tqaep2.py:158`).

### `TOOL_REQUIREDNESS_HOLD` — 72 — partial

- HARD baseline clean (`None`); route baseline clean (`None`).
- The gate returns HOLD for **any** `declared != independent` (`b2_semantics.py:260-265`), not specifically HARD-loss or unauthorized enablement.
- The route mutation sets both `declared="HARD"` and `claimed_enable=True`; the mismatch branch fires first, so the enablement branch is never exercised (`b2_ops_tqaep2.py:149-151`).
- The route mutation is two changes, violating single-mutation.
- **9 / 18 HARD cases do not execute their §06 mutation.** Their §06 mutations are wrong type, unknown forbidden field, maker self-attest, missing property, daily-as-intraday, future row, orphan run, lookahead/canonical override, and CI-green-as-release. The TQAEP applies `HARD -> EVAL_ONLY` to all 18.
- **54 / 54 route cases** say “change one protected field”; the TQAEP instead upgrades requiredness and enables.

At least **63 / 72** HOLD cases are class reachability, not the specified case mutation.

### `STATE_CONFLICT` — 8 — overbroad

Baseline `state_gate([state])` is `None`; mutation `state_gate([state,"ENABLED"])` is `STATE_CONFLICT` for all 8. These 8 are genuinely contradictory.

But `state_gate` returns conflict for **any two distinct non-empty states** (`b2_semantics.py:268-271`). It would also flag compatible `INSTALLED + ENABLED`. It has no contradiction relation.

### Expected code for any input?

- `NAMESPACE_JOIN_DENY`: **yes**, for any selector that is not exactly `{"key": …}`. This class must be rejected.
- `TOOL_REQUIREDNESS_HOLD`: no, but any mismatch returns HOLD; enablement is untested.
- `STATE_CONFLICT`: no, but any two distinct states returns conflict.

## 5. Clause identity — “UNBOUND” is false; 1,465/1,465 reproduce

I reproduced `direct_clause_sha` for **all 1,465 units**, not one. The rule is:

> SHA-256 of the UTF-8 bytes of parent lines `a..b` inclusive, including the LF terminating line `b` (parent is LF-only).

Examples:

- `B2.U0081`, parent `L751–751`: `c7c50c0e0943fe0d7b1cd621b5b5ba312e45be7f6f0e5fe1c490cae7f1a8dd6e` — exact.
- `B2.U0001`, parent `L93–116`: `07870b8e9197a2de6e87c7e3a84f33862fe16101656d286e5f3197aeb3faee69` — exact.

By kind: HARD 18/18, E00_TECH 8/8, TECH_ROUTE 54/54, Q_SOURCE_ROW 1,385/1,385.

The receipt's `parent_reproduced = 0` is a wrong-reference bug. `b2_ops_qrows2.py:99` parses `original_source_ref`, but `direct_clause_sha` is computed from `direct_parent_ref`. For Q rows the former is `EVIDENCE@2cd8…`; for non-Q it is `PARENT@dd37…`, a different parent. Example: HARD `B2.U0001` direct-parent `L93–116` hashes to `07870b8e…`, while `dd37…:L1867` hashes to `4c30dae2…`.

`clause_identity` is also hardcoded to `"UNBOUND_RULE"` in POS (`b2_ops_tqaep2.py:121`; `_clause` is never set). Clause identity is silently carried in `direct_clause_sha` and `resolved_direct_parent`, but not checked.

## 6. Parent source — PASS, plus a second stale-path family

The rebound parent exists at the `W0_B0-B8` path, is 2,712,933 B, and hashes to `d95c8ac6…`. The declared `W0_B0-m` path does not exist. The receipt labels it `PARENT_SOURCE_REBOUND_BY_SHA` / `CANDIDATE_NOT_RATIFIED — locator rebind only; no SPEC amendment`. Correct.

However, all 1,385 Q rows' `q_row.verified_carrier_ref` point to `...\PHASE 00~04\...\SST_PLP_共用實質正文_工具合約_2026-11-23_r2.md@463dcf33…`. That path does not exist; the bytes are at `PHASE 01~04`. The sha resolves, and I verified all 1,385 carrier rows (key, source_row, payload, `carrier_status`) match. The receipt has no `CARRIER_SOURCE_REBOUND_BY_SHA` and does not expose the stale locator.

## 7. Independent positive: row payload identity is real

The receipts do not compare `source_payload` to the original sources. I did:

- **Q_SOURCE_ROW: 1,385/1,385** match the declared evidence document `2cd8ab8b…` at the declared line: `q_row.full_key`, `source_row`, `carrier_line`, and the nine-element JSON payload exact.
- **Non-Q: 80/80** match the declared blueprint `dd37a40b…` at their declared lines: all `source_payload` cells exact.
- All **1,465/1,465** `payload_sha` values also recompute.

The candidate's rows are genuinely original and complete. That is a stronger result than the receipt proves — but it is the checker's result, not the receipt's.

## 8. Standing checks

| check | result |
|---|---|
| SPEC pin | PASS — 8,016,371 B / `140de5bc…` |
| Candidate pins | PASS — 9/9; digest `095ddf25…` |
| 2,930 case IDs | PASS — 2,930 unique, 1,465 POS + 1,465 NEG; 0 orphan, 0 missing |
| §06 NEG distribution | PASS — 1,385 / 72 / 8 |
| `first_fail` on NEG PASS | PASS — 0 null |
| Payload pins | PASS — 1,465/1,465 |
| No candidate write | PASS — no SPEC/parent/source/receipt/code changed |
| Parent rebind | PASS — `d95c8ac6…`, `CANDIDATE_NOT_RATIFIED` |
| Original row identity | PASS (checker) — 1,465/1,465 value-exact |

## 9. Answer: what B2 may and may not claim

**`ROW_SEMANTICS_AND_CLASS_MUTATION` is not supported as written.**

With a corrected receipt, B2 may claim:

1. **`ROW_PAYLOAD_AND_PROVENANCE_IDENTITY`** — 1,465/1,465 value-exact against `dd37…` / `2cd8…`, plus 2,930 exact case bindings.
2. **`CLAUSE_SPAN_IDENTITY`** — 1,465/1,465 `direct_clause_sha` reproduce from parent r2 `d95c…` under the explicit line-span rule.
3. **`QUADRANT_CENSUS`** — 440/513/378/54, corroborated by disjoint `source_row` ranges; state that the key prefix and `q_row.full_key` are collinear.
4. **`HARD_PRESENCE_18`** — 18 HARD rows present, 0 removed, as a data fact.
5. **`PIN_HISTORY_72_AND_54`** — 72 reproducible as 16 HARD + 2 E00 + 54 route; 54 exactly TECH_ROUTE.
6. **`PARENT_REBIND_BY_SHA`** — `d95c8ac6…`, labelled `CANDIDATE_NOT_RATIFIED`.
7. **`CASE_CENSUS_2930`** — no orphan/missing; non-null `first_fail` on NEG PASS.

B2 must not claim:

1. `all_three_signals_agree` — two collinear key-derived signals, no per-quadrant SPEC section.
2. Independent requiredness / `disagreement_count = 0` as evidence — 1,439 rows vacuous/skipped; 26 same-unit cross-field; 0 original-source comparisons; Q4 `EVAL_ONLY` is 0 rows.
3. “Historical 72 not reproducible” — false; it is 16 HARD + 2 E00 + 54 route under the pinned old predicate.
4. `NAMESPACE_JOIN_DENY` as a namespace test — it is a selector-shape denial; a wrong namespace with `::` is not denied.
5. Per-case NEG mutation fidelity — 9/18 HARD and 54/54 route do not execute their §06 mutation; the route mutation is two-field and the enablement branch is untested.
6. A general `STATE_CONFLICT` oracle — it flags any two distinct states.
7. “Clause-sha rule UNBOUND / no clause identity” — 1,465/1,465 reproduce.
8. `B2_TQAEP_EXECUTED` / `B2_ACCEPTED` / `B2_COMPLETE` — no product case was executed.

## 10. Defect split

### Maker-fixable

1. Quadrant claim: replace `all_three_signals_agree` with `two_collinear_key_signals_agree`; add the `source_row` range signal; fix “54 non-Q” to 80. `b2_semantics.py:218-232`; `b2_ops_qrows2.py:177`.
2. Q requiredness self-comparison: `b2_semantics.py:208-214` uses the same `source_payload[2]` as `row_requiredness()`. Compare to the original row or label `VERBATIM_ONLY`; record applicability and the 1,014 prose rows; stop treating `disagreement_count = 0` as evidence.
3. Remove the false `Q4 EVAL_ONLY` premise; 0 Q4 rows, 17 Q1 rows.
4. Pin reconciliation: reconstruct the old predicate from `b2_ops_qrows.py:76-79`; fix `hard_unbound = 645`, `measured = 699`, and the “70” arithmetic; keep 54 route; report the clean 1,407 separately.
5. Clause reproduction: check `direct_parent_ref`, not `original_source_ref` (`b2_ops_qrows2.py:99`); this yields 1,465/1,465; make `clause_identity` a real field (`b2_ops_tqaep2.py:121`).
6. `NAMESPACE_JOIN_DENY` oracle: reject a tail-only **key** and a wrong namespace, not merely a `suffix` field; add a discriminating pair.
7. HOLD mutation fidelity: apply the §06 mutation for the 9 non-HARD-loss HARD cases; split the route mutation into declared-HARD and separate enablement tests.
8. `STATE_CONFLICT` gate: replace “any two distinct states” with a declared mutual-exclusion relation; add a legal-coexistence baseline.
9. Reporting types: `baseline_first_fail = 1` should be `baseline_rows = 1`; expose `requiredness_applicable`/`requ_reason`.
10. Carrier locator: add `CARRIER_SOURCE_REBOUND_BY_SHA` for `463dcf33…` (`PHASE 00~04` -> `PHASE 01~04`) and check `q_row.verified_carrier_ref`.

### Owner-authority

1. Parent ratification: `d95c8ac6…` is still `CANDIDATE_NOT_RATIFIED`; ratify or accept candidate-only clause identity.
2. SPEC stale paths: 1,465 `direct_parent_ref` fields contain `W0_B0-m`; 1,385 Q carrier refs contain `PHASE 00~04`. Correcting them changes the frozen SPEC sha; that is an Owner amendment/addendum.
3. Requiredness vocabulary: deciding how 1,014 prose Q values map to tokens is an Owner decision.
4. Namespace policy: define what namespace-qualified join means and whether a unique tail-only join must be denied.
5. State relation: define which disposition pairs are mutually exclusive vs compatible (`INSTALLED + ENABLED` is the obvious test).
6. B5 selection / pin / licence / lock remain B5/Owner duties.
7. B2 acceptance/promotion: not supported this round.

### Original-Domain-Owner

1. 18 HARD obligations: R17 / OriginalConsumer must ratify HARD and the HOLD consequence.
2. 54 TECH_ROUTE dispositions: original tool/consumer owner.
3. 8 E00 design selections and state conflicts: E02/E05/PIPD owner.
4. 1,014 prose Q requiredness values: original Q-registry owner; “verbatim preserved” is supportable, “semantically parsed” is not.
5. Original source authority (`dd37…`, `2cd8…`, `463dcf…`): original domain owners.
6. Tool availability/pin/licence/lock: original tool owners and B5.

## One-line answer

`ROW_SEMANTICS_AND_CLASS_MUTATION` is not supported: the row payloads and clause spans are actually good (1,465/1,465 each, independently measured), the census numbers are right, and the parent rebind is correct, but requiredness is vacuous for 1,439/1,465 rows, the namespace NEG oracle is selector-shape-only, 63/72 HOLD NEGs are not their §06 mutations, the historical 72 is reproducible, and clause identity is bound, not UNBOUND.