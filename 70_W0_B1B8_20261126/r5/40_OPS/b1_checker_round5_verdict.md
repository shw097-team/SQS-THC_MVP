The read-only mount refused the write (`Set-Content` to `40_OPS/b1_checker_round5_verdict.md` → PermissionDenied; no file created). The turn also exposed no separate `-o` value. The verdict is below for whoever holds write authority to persist.

## Read-only round 5 — measured

**Candidate.** `40_OPS/b1_candidate_freeze_20261126T141853.json` (2,218 B; highest timestamp; `frozen_at` 2026-11-26T14:18:53+08:00). Re-hashed all ten pinned artefacts: **10/10 bytes + raw sha256 exact**:

`b1_cases.py 0f4601df…/23,117` · `b1_fda_static.py c98cdb37…/10,404` · `b1_reader.py ea20240e…/13,813` · `b1_reader2.py 4e5c2200…/41,527` · `run_b1.py ad64cb05…/6,307` · `summarize_b1.py 16b810b9…/2,883` · bindings `a8025e2f…/2,502` · allow-list `de92bd2c…/3,105` · run `591808fa…/127,559` · TQAEP `821f3e61…/41,636`.

**Digest.** Declared `9666c7ed52eaab1b4edb8dad589fd6a8667fef71fef4c585b3690a20420ab63a` recomputes exactly over ordinal-sorted `sha256␠␠path` lines, LF-joined, **no trailing LF**. With trailing LF: `e9babee1…`; declaration order: `e9167fac…`.

**Baseline.** Spec `13294cada156a2c0…`, 185,197 B; **30/30** `source_payload` compact-JSON pins re-derived. Allow-list primary **16/16 raw sha256 + bytes exact**; mirror 0/16 raw (CRLF) but **16/16 content-identical** after CRLF→LF. Brownfield HEAD `9a70501a…`, tree `688de895…`, 132 status entries, status sha `59a313ed…` — equal before/after and now. **60** cases (30 POS + 30 NEG): 53 PASS / 1 `HOLD_SCOPE_NOT_COVERED` / 1 `HOLD_BASELINE_NOT_VALID` / 5 `HOLD_ORACLE_UNBOUND`; 0 NEG `first_fail=null`; every NEG PASS matches its §06 expectation.

### The five round-4 defects

| # | Item | Verdict | Measured basis |
|---|---|---|---|
| 1 | `carrier_present_out_of_scope` per carrier, primary first, primary `allow_listed_root=true` | **PASS** | `b1_reader2.py:602-623` emits one entry per carrier, allow-listed root first. BASE-018 `tests/test_fda_*` names primary `…\FHS\Fabric\FABRIC\fabric-desktop-automation` (`allow_listed_root:true`) then mirror `…\Fabric-rebind-publish\…` (`false`). TQAEP `B1.POS.BASE-018.observed.present_but_unread` carries both in the same order. |
| 2 | `discrimination` reaches TQAEP `observed` for both POS and NEG of `broker_live_submit` | **PASS** | `b1_cases.py:210-218` copies `r0.get("discrimination")` into `observed`; `b1_fda_static.py:180-212` builds the read-side probe. Both `B1.POS.FDA_broker_live_submit` and `B1.NEG.FDA_broker_live_submit` show `{record:{action:"read",…}, admitted_first_fail:null}`; POS `pos_first_fail` and NEG `arms` (`replace`, `cancel`) are `FIN_ORDER_DENY_ALWAYS`. Caveat: the probe is the same read record in both; POS/NEG distinction is carried by `pos_first_fail`/`arms`, not by differing `discrimination` contents. |
| 3 | Carrier `commit_reason` says “no brownfield commit identity …” | **PASS** | `b1_reader2.py:731-741`: **12/12** carrier resolutions now say `carrier artefact: no brownfield commit identity exists outside the brownfield repo (the carrier may have its own git history)`. The 7 disk-only reasons still say `no commit identity exists`; all 7 paths are `??`/untracked, so true. Primary carrier is git-tracked (`FHS/Fabric@765df6289cfb…`, blob `573b5acd…`, clean), which is why the old carrier wording was false. |
| 4 | `candidate_digest_rule` reproduces the digest | **PASS** | Recomputed sorted/no-trailing-LF digest = `9666c7ed52eaab1b4edb8dad589fd6a8667fef71fef4c585b3690a20420ab63a` — exact. |
| 5 | `DELIVERY_MANIFEST.json` currency | **FAIL — still stale** | `generated_at` `2026-11-26T13:22:18+08:00` predates freeze `14:18:53`. `current_pointers.b1_run` = `…T130447.json`, `b1_tqaep` = `…T130448.json`, not `…T141840`/`…T141842`. Code pins pre-freeze: `b1_cases.py` 18,438/`9456b61e` (frozen 23,117/`0f4601df`); `b1_fda_static.py` 9,061/`a2dd7df8` (10,404/`c98cdb37`); `b1_reader2.py` 32,869/`4f2e4aaa` (41,527/`4e5c2200`); `run_b1.py` 5,734/`71c237c2` (6,307/`ad64cb05`). Round-5 run/TQAEP/freeze absent; manifest still lists only rounds 1–3. |

### Regression / standing checks

| Check | Verdict | Basis |
|---|---|---|
| 30/30 payload pins | **PASS** | All 30 UNIT JSON blocks parsed; `sha256(JSON.stringify(source_payload, UTF-8))` equals every `payload_sha`. `payload_pin_failures=[]`; `units=30`. |
| Spec sha/size | **PASS** | `13294cada156a2c0beb485bb940a316dd540173273c90dc721570604ca4a3753`, 185,197 B. |
| Allow-list 16/16 | **PASS** | Primary 16/16 raw sha256 + bytes; mirror 16/16 content after CRLF→LF (0 raw, expected). |
| No-write equality | **PASS** | Receipt before/after and current HEAD `9a70501a…`, tree `688de895…`, status sha `59a313ed…`, 132 entries are identical. No git write command used. |
| Case tally 60 | **PASS** | 60 unique cases, 30 POS + 30 NEG; computed tally equals declared 53/1/1/5; §06 case-id set equals TQAEP set, no extras/drops. |
| 5 `HOLD_ORACLE_UNBOUND` | **PASS** | Exactly `B1.NEG.KERNEL_{fsdt,temporal,knowledge,harness,capability}`; each has `declared_mutation_executed=false`, `semantic_acceptance=NOT_CLAIMED`. D-4, not a Maker defect. |
| 11 round-3 items not regressed | **PASS** | Recursive diff of round-4 `T140445` vs round-5 `T141840` found only `generated_at`, the intended carrier-list length 1→2 (including its `missing.out_of_scope` copy), and the added `discrimination` field; TQAEP likewise only `generated_at` and `present_but_unread` 1→2 beyond `discrimination`. All other fields and all **39** resolution objects identical. Items 1–11 remain PASS: `FDA_ARTEFACTS=16`; `BASE-012` prefix propagation intact; `BASE-009` 3/3 `REPO_ROOT`, glob `TRACKED_GLOB` with 2 measured blobs, carrier escalation gated by `not _repo_exact` (`:626-633`); 12 commits, all `REPO_ROOT`, 0 fabricated; 13/13 carrier resolutions allow-list true, 0 unlisted carrier path true. |

## B1_ACCEPTED supported? **NO**

Four of the five round-4 Maker defects are closed. The manifest remains stale, and acceptance is independently blocked by Owner-authority and oracle items.

**Maker-fixable (1)**
1. `DELIVERY_MANIFEST.json` is stale. Rebuild after the freeze so `current_pointers` name the frozen round-5 run/TQAEP and all code hashes/bytes match `b1_candidate_freeze_20261126T141853.json`; include the round-5 freeze, run, TQAEP and checker record.

**Owner-authority (4; unchanged, not re-litigated)**
1. **D-1** — three `CANDIDATE_NOT_RATIFIED` locator bindings (BASE-009 ×2 → `data_plane/src/`; BASE-017 bare → `governance/`); ratify or amend the SPEC path with a new sha.
2. **D-2** — allow-list scope vs BASE-018 `tests/test_fda_*`: extend the 16 or record a waiver for `B1.POS.BASE-018`; also decide the mirror carrier’s status.
3. **D-3** — slot↔artefact mapping remains unproven (`slot_reference_counts=0` for 7/7 slots; 7 FDA POS remain `CARRIER_LEVEL_ONLY`).
4. **SPEC/allow-list inconsistency** — §06 declares `tests/test_fda_*` while the Owner allow-list caps the surface at 16 paths; root of the single `HOLD_SCOPE_NOT_COVERED`.

**Oracle-blocked (5)**
- `B1.NEG.KERNEL_fsdt` — `HOLD_ORACLE_UNBOUND`
- `B1.NEG.KERNEL_temporal` — `HOLD_ORACLE_UNBOUND`
- `B1.NEG.KERNEL_knowledge` — `HOLD_ORACLE_UNBOUND`
- `B1.NEG.KERNEL_harness` — `HOLD_ORACLE_UNBOUND`
- `B1.NEG.KERNEL_capability` — `HOLD_ORACLE_UNBOUND`

These are **D-4**: a ratified semantic oracle from the original Domain Owner is still absent; not a Maker defect.