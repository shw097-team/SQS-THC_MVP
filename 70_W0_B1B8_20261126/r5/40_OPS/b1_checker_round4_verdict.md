The wave root is mounted read-only — I tried the round-4 record path (`40_OPS/b1_checker_round4_verdict.md`) and a temp fallback; both returned `EPERM`. Nothing was created, modified or deleted. The verdict is therefore delivered here verbatim for whoever holds write authority to persist.

---

## Read-only round 4 — measured

Checker record. Every value below was re-derived from bytes on disk; the freeze's self-report and the Maker's TQAEP verdicts were not used as evidence. Read-only: no repo command wrote (git used only as `-c safe.directory=* -C <repo> …` plumbing, no config persisted); no wave input was modified.

**Baseline.** Candidate frozen at `40_OPS/b1_candidate_freeze_20261126T140527.json` (2,101 B); I re-hashed all ten pinned artefacts — **10/10 raw sha256 + byte length match**: `b1_cases.py 886bd8cb…`/22,959 · `b1_fda_static.py c98cdb37…`/10,404 · `b1_reader.py ea20240e…`/13,813 · `b1_reader2.py c8779e61…`/41,031 · `run_b1.py ad64cb05…`/6,307 · `summarize_b1.py 16b810b9…`/2,883 · bindings `a8025e2f…`/2,502 · allow-list `de92bd2c…`/3,105 · run `30bd64d2…`/125,717 · tqaep `84944566…`/40,355. `candidate_digest 68550cdd…` reproduces only over **declaration-order** `sha␠␠path` lines (sorted ⇒ `978add87…`). Round-3 pair confirmed by hashing the files, not by the prompt: `b1_run_…130421.json = 9303ce87…`, `b1_tqaep_…130423.json = 22613ebc…`.

Spec `13294cada156a2c0…`, 185,197 B — exact on both on-disk copies (workspace `docs/` and 知識庫); **30/30 `payload_sha` re-derived by me**, 0 failures.
Brownfield repo: HEAD `9a70501a…`, tree `688de895…`, 295 tracked paths, `git status --porcelain` 132 entries, `sha256`(nl + trailing LF) `59a313ed…` — equal to the receipt's before **and** after, and to my measurement now.
Allow-list: **16/16 raw sha + bytes exact** against `FHS\Fabric\FABRIC\fabric-desktop-automation`. Mirror: 16/16 byte-different, **0** content-different after CRLF→LF normalisation.

### The 11 round-3 items

| # | Item | Verdict | Measured basis |
|---|---|---|---|
| 1 | Receipt pins its inputs | **PASS** | `b1_reader2.py:425-434,808`; receipt `inputs.b1_locator_bindings.json` = 2,502 B / `a8025e2f…`, `inputs.b1_source_allowlist.json` = 3,105 B / `de92bd2c…`; I re-hashed both files → identical. `EDGE.B1.INPUT_PINS_PINNED` re-reads them at run time and matches. |
| 2 | BASE-017 `measured` not an echo | **PASS** | Target `FDA_INTEROP_DISPOSITION.yaml` → `measured:[{path:…\governance\FDA_INTEROP_DISPOSITION.yaml, raw_sha256:9fac4d25…, bytes:3487, measured:true, tracked:false}]`; value produced by `sha_file(bind["resolved_path"])` and gated at `b1_reader2.py:679-686`. My hash of that file: `9fac4d25…`/3,487 — equal. |
| 3 | `commit_reason` specific and true | **PARTIAL** | Four classes exist and are applied (`:726-735`): 16 null (tracked), 7 `disk-only (untracked)`, 3 `locator binding…`, 12 `carrier artefact…`, 1 `no locator resolved…`. Round-3's defect is closed — all 3 bound targets carry the binding reason. Verified true: all 7 disk-untracked paths are `??` in git. **False as worded:** the carrier sentence says no commit identity exists outside the brownfield repo, but the primary carrier is tracked at FHS/Fabric@`765df628`, blob `573b5acd`, clean, 3,487 B. `commit=null` itself is correct (the field is the brownfield HEAD). |
| 4 | `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` falsifiable | **PASS** | `b1_cases.py:287-310` asserts three probes: poisoned declared path → `ABSENT_IN_TREE_AND_DISK`/`[]`; same poison + real tree → `TRACKED_PRESENT`/`[src/kernel/fsdt/__init__.py]`; poisoned glob → `ABSENT`/`[]`. A resolver taking identity from the index flips probe 1 or 3. Structurally (repo code not executed): EXACT requires tree membership (:193), a real file at the declared path (:211), a carrier hit drawn only from the 16 (:591-601), or a binding whose sha is re-measured (:679-686); an index entry equal to the declared path is discarded (:228) and every index glob hit is `os.path.isfile`-gated (:186). No index-only path to a declared-path EXACT/tracked claim. |
| 5 | Collision inventory over all 16 | **PASS** | `FDA_ARTEFACTS` = 16 incl. `README.md` (`:259-265`). Both carrier inventories 16/16 with sha; authority collision 0 byte / 0 content diffs; mirror observation 16 byte-diffs / 0 content-diffs = my independent re-hash (16 differing raws, 0 differing after CRLF→LF). |
| 6 | `NEG.FDA_broker_live_submit` not constant | **PASS** (evidence gap) | `b1_fda_static.py:102-114` reads `action`: submit/replace/cancel → `FIN_ORDER_DENY_ALWAYS`, `read` → `None`, unknown → deny; `:182-185` adds a `read` discrimination record and `:205-208` makes the slot PASS depend on it being admitted, so a constant deny fails its own slot. Caveat: `discrimination` is not copied into TQAEP `observed` (`b1_cases.py:209-216`), so POS and NEG still print the same spec-mandated `FIN_ORDER_DENY_ALWAYS` and the discriminating measurement is invisible in the receipt. |
| 7 | Glob escalation honours the prefix | **PASS** | `resolve()` glob branch requires prefix + suffix (:178-183); the disk fallback is `os.path.isfile(repo/…)` (:184-186); carrier escalation matches only inside `carrier_paths`, built from the 16 allow-listed rels (:562-570,592-596). `data_plane/config/*.yaml` → 2 hits, both direct children, `read_domain=REPO_ROOT`, 0 carrier hits; blobs `f077290d`/`6267f8d0` = `git ls-tree HEAD -- data_plane/config`. Round-3's 12 bare-`*.yaml` carrier hits are gone. (Nit: `*` is not depth-limited; no effect here.) |
| 8 | U0012 bare siblings by prefix | **PASS** | Prefix propagation at `:476-484`, recorded `prefix_propagation="FABRIC/fabric-desktop-automation/"`, `declared_paths` prefixed. Resolutions: `read_domain=EXTERNAL_CARRIER`, `resolved_relative_path` = carrier rel, shas `1936a465`/5,768 (TEAM), `b5257a3e`/3,651 (AGENTS), `aa3084ba`/4,410 (README) = allow-listed carrier bytes. The old repo-root files (`768411ac`/5,328, `988f9295`/6,086) appear only as basename candidates with `tracked:false`, no commit, no domain; `ls-tree HEAD` has 0 hits for AGENTS.md/README.md/TEAM.md (both `??`). |
| 9 | Per-artefact allow-list enforcement | **PASS** | Three-part gate `al_root` ∧ `al_art` ∧ `al_sha` (:753-757). Direction A — bound-but-listed BASE-017 `governance/FDA_INTEROP_DISPOSITION.yaml`: root = primary, rel = `governance/…`, root/path/sha all true, `allow_list_declared=true`. Direction B — 0 of 39 resolutions is a carrier path outside the 16, and such a path cannot become one (`carrier_hits ⊆ carrier_paths`); the only unlisted carrier contacts (BASE-018 `tests/test_fda_*.py`) never carry `allow_list_declared=true`. All 13 carrier-rooted resolutions listed with root/path/sha true. |
| 10 | Commit fabrication | **PASS** | 39 resolutions; 12 carry `commit`; **0** with `read_domain != REPO_ROOT` (round 3: 9). All 12 committed paths exist in the 295-path HEAD tree; the other 27 are `commit:null` with a reason. |
| 11 | BASE-009 adjudication gated | **PASS** | Gate `if res.get("carrier_hits") and not _repo_exact` (:626-629) plus finalisation precedence `repo_exact → REPO_ROOT` (:693-694). Across all 39 resolutions none is carrier-labelled while its declared target exists at HEAD, and no `EXTERNAL_CARRIER` source is a HEAD path. BASE-009: 3/3 `REPO_ROOT`, glob `TRACKED_GLOB` with two measured blobs; `NEG.BASE-009` PASS on arm (a) (`ABSENT_*`×3 → `BASE_ROW_MISSING`), arm (b) `applicable=true, upgraded=[]`. |

### Standing checks

| Check | Verdict | Measured basis |
|---|---|---|
| Pins (payload / spec / allow-list) | **PASS** | `payload_pin_failures=[]`; 30/30 units re-derived by me; spec `13294cad…`/185,197 exact; allow-list 16/16 sha+bytes exact. |
| No-write | **PASS** | HEAD `9a70501a…`, tree `688de895…`, 132 entries, status sha `59a313ed…` identical in receipt before/after and at my read; no `git` write command, no config written. |
| Case tally honesty | **PASS** (count corrected) | **60** cases, not 61: §06 has 30 POS + 30 NEG and the round-3 tqaep carries the identical 60 case_ids — no case dropped. Tally 53 PASS / 1 `HOLD_SCOPE_NOT_COVERED` / 1 `HOLD_BASELINE_NOT_VALID` / 5 `HOLD_ORACLE_UNBOUND`; 0 NEG with `first_fail=null`; 0 POS PASS on an invalid baseline; every NEG PASS's `first_fail` equals its §06 expectation. |
| BASE-018 new claim | **PARTIAL** | Verdict honest, evidence misattributed — below. |
| Freeze integrity | **PARTIAL** | 10/10 file pins exact, but `candidate_digest_rule` ("sorted 'sha  path' lines") does not reproduce its own digest. |
| Delivery manifest currency | **FAIL** | `DELIVERY_MANIFEST.json` (13:22) points `current_pointers` at the 13:04 receipts and pins pre-freeze code: b1_reader2.py 32,869/`4f2e4aaa` (frozen 41,031/`c8779e61`), b1_cases.py 18,438/`9456b61e` (frozen 22,959/`886bd8cb`), b1_fda_static.py 9,061/`a2dd7df8` (frozen 10,404/`c98cdb37`), run_b1.py 5,734/`71c237c2` (frozen 6,307/`ad64cb05`). |

### Attack on the new claim — BASE-018 `tests/test_fda_*`

The four files exist on disk in **both** carriers — primary 4,015 / 4,028 / 4,001 / 7,512 B; mirror 4,105 / 4,119 / 4,091 / 7,675 B — and none is among the 16 allow-listed paths, whose directive is "exactly the 16 artefact paths below; nothing else under FHS/ is in scope". So `TYPED_MISSING_OUT_OF_ALLOW_LIST_SCOPE` / `HOLD_SCOPE_NOT_COVERED` is the **honest** result: it is not hiding a missing artefact (existence is measured by stat/glob, the row is typed, the other three declared targets are EXACT).

Two evidence-side defects remain: (i) `carrier_present_out_of_scope` is overwritten inside the carrier loop (`b1_reader2.py:602-618`), so the receipt names only the **unratified mirror** and silently drops the **allow-listed primary** — the carrier whose scope decision actually matters; (ii) these are precisely the files round 3 found being read outside the allow-list, so this HOLD is the visible cost of closing that over-reach. The fix is an Owner act; the attribution is a Maker act.

## B1_ACCEPTED supported? **NO**

The 11 round-3 Maker items are closed except item 3's carrier wording, but acceptance is not supported: 1 POS is `HOLD_SCOPE_NOT_COVERED`, 5 NEG are `HOLD_ORACLE_UNBOUND`, four Owner decisions are outstanding, and the delivery manifest still points at the superseded candidate. Maker self-check is not R16.

**Maker-fixable (5)**
1. `carrier_present_out_of_scope` collapses multiple carriers (BASE-018 names only the mirror, drops the allow-listed primary) — `b1_reader2.py:602-618`.
2. `discrimination` record never reaches TQAEP `observed` for FDA slots, so POS/NEG remain indistinguishable from the receipt alone — `b1_cases.py:209-216`.
3. Carrier `commit_reason` wording is false: "no commit identity exists outside the brownfield repo" — FHS/Fabric@`765df628` tracks `…/governance/FDA_INTEROP_DISPOSITION.yaml` (blob `573b5acd`). Say "no brownfield commit identity".
4. `candidate_digest_rule` mislabel — digest is declaration-order, not sorted (`68550cdd…` vs `978add87…`).
5. `DELIVERY_MANIFEST.json` stale against the frozen candidate (4 code hashes, both current pointers).

**Owner-authority (4)**
1. **D-1** — three `CANDIDATE_NOT_RATIFIED` locator bindings (BASE-009 ×2 → `data_plane/src/`, BASE-017 bare → `governance/`) still carry the identity claim; ratify or amend the SPEC path (+new sha).
2. **D-2** — allow-list scope vs BASE-018: extend the 16 to cover `tests/test_fda_*.py` or record a waiver for `B1.POS.BASE-018`; also decide the mirror carrier's status (still feeding the EOL observation while outside the allow-list).
3. **D-3** — slot↔artefact mapping: `slot_reference_counts = 0` for 7/7 slots in both carriers; the 7 FDA POS remain `CARRIER_LEVEL_ONLY / slot_mapping=unproven`.
4. **SPEC/allow-list inconsistency** — §06 declares `tests/test_fda_*` while the owner allow-list caps the surface at 16 paths; root of the single `HOLD_SCOPE_NOT_COVERED`.

**Oracle-blocked (5)** — `B1.NEG.KERNEL_{fsdt,temporal,knowledge,harness,capability}` stay `HOLD_ORACLE_UNBOUND` (`declared_mutation_executed=false`, `semantic_acceptance=NOT_CLAIMED`); no ratified semantic oracle exists anywhere in the wave root. Not a Maker defect.

---

Two process notes: the `61` in the brief is not reproducible — the SPEC's §06 table and both rounds' TQAEP carry exactly **60** cases with an identical case_id set; and `40_OPS/b1_checker_round4_run.log` remained 0 bytes (untouched), since no writable target exists in this mount.