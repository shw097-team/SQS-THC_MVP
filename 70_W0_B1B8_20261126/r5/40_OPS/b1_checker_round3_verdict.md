## Read-only round 3 — measured

Baseline (my measurements today): spec `13294cad…4a3753`, 185,197 B; manifest 16/16 sha+bytes; HEAD `9a70501a…`, tree `688de895…`, 295 tracked, `status --porcelain` 132 entries → sha256 `59a313ed…ea2e3` (nl + trailing LF); receipts `9303ce87…` / `22613ebc…`; inputs `a8025e2f…` (bindings) / `de92bd2c…` (allow-list). Code mtimes precede both receipts (reader2 12:55:57 < 12:56:10; cases 12:56:39 < 12:56:45). `b1_cases.latest_receipt()` resolves to the cited run. Tally 54 PASS / 1 FAIL / 5 HOLD.

| # | Item | Verdict | Measured basis |
|---|---|---|---|
| 1 | NEG truthfulness | **PARTIAL** | 30 NEG: 24 PASS, 1 FAIL, 5 HOLD; **0** with `first_fail=null`. `narrowed_ok` no longer exists (0 occurrences, code+receipts); gate is now `baseline_valid = not row.missing` → `HOLD_BASELINE_NOT_VALID` (`b1_cases.py:202‑211`). Codes are real outputs: BASE from `delete_ff` of an in-memory re-resolve, FDA from `run_slot` detector arms, KERNEL `SEMANTIC_ORACLE_UNBOUND`. All 5 KERNEL NEG are `HOLD_ORACLE_UNBOUND` (not PASS) with `declared_mutation_executed=false`, `semantic_acceptance=NOT_CLAIMED`, note "second-writer scan … supplementary static evidence only; NOT the §06 case result" — present in 5/5. Residual defects: (i) `B1.NEG/POS.BASE-012` rest on a baseline that is nominally valid (`missing=[]`) but 2/3 targets are the wrong entity (below); (ii) `B1.NEG.FDA_broker_live_submit` executes only `token=SUBMIT_TOKEN_PRESENT` while the §06 mutation column reads `submit/replace/cancel`, and `d_broker_live_submit` is constant in `submit` → both POS and NEG are satisfied by one expression (non‑discriminating). |
| 2 | Locator bindings | **PARTIAL** | File: 3 unique `(unit,declared_path)` → one absolute path + one raw sha, no wildcard, `claim_ceiling=LOCATOR_ONLY_NOT_SPEC_AMENDMENT`, `ratification=CANDIDATE_NOT_RATIFIED`. **I re-hashed all three: `fc10f802…`/24,609 · `06b25b72…`/11,197 · `9fac4d25…`/3,487 — exact.** Runtime re-verify exists and gates the claim (`b1_reader2.py:584‑591` `sha_file(bind.path)==bind.sha` → `bind_ok`, else no binding + `missing`). `missing=[]` is legitimate for 8/9 formerly drifted targets (009 ×2 via binding, 012 `TEAM.md` via declared `FABRIC/…` prefix map to carrier root, 017 via binding, 018 via `tests/`-qualified carrier glob + 3 exact). **Not legitimate for 012 `AGENTS.md`/`README.md`**: still resolved to repo-root untracked `5,328 B 768411ac` / `6,086 B 988f929`, `locator_confidence=EXACT`, `commit=HEAD`, note "absent from the brownfield repo" — while the carrier copies are 3,651/4,410 B. Also `B1.U0009` verdict names a carrier surface **no resolution touches** (3/3 `read_domain=REPO_ROOT`). |
| 3 | Allow-list | **PARTIAL (declaration yes, enforcement no)** | Declaration: 16 explicit artefacts + 16 raw shas, fixed root `FHS\Fabric\FABRIC\fabric-desktop-automation`, `scope_ceiling="exactly the 16 … nothing else under FHS/"`, `effect=SOURCE_READ`, `write_set=[]` — **no wildcard**. **Primary 16/16 sha+bytes exact (my re-hash).** Enforcement is root-only: `b1_reader2.py:554‑559` loads only `_a["root"]`; `:635‑637` sets `allow_list_declared = root ∈ ALLOW_ROOTS`. Measured over-reach: 20 distinct carrier paths are sha-read, **7 are not in the allow-list** — `tests/test_fda_{lease,router,router_integration,security}.py`, `governance/FDA_ROUTE_CHECK.yaml`, `governance/FDA_XQ_PAPER_FIXTURE_MANIFEST.yaml`, `WO_FDA_XQ_002.yaml` — and the four test files carry `allow_list_declared=true`. Primary vs mirror: 11 carrier authority records, all rooted at primary, `al=true`; **0 mirror-rooted records**, yet the mirror is read (both carriers feed the EOL verdict; `matrix_vocabulary` reads the 11,439 B mirror matrix) → mirror usage has no structured entry. Opposite false-negative: bound BASE-017 target **is** listed but reports `root=null, al=false` (authority root taken from `car_exact`, empty for a binding). Coverage: allow-list 16 vs `FDA_ARTEFACTS` 15 — `README.md` excluded from the collision inventory, so `IDENTICAL_MODULO_EOL` covers 15/16 (I verified README is in fact LF-identical, `aa3084ba` both sides). |
| 4 | `B1.NEG.BASE-009` | adjudicated below | — |
| 5 | Standing checks | 3 PASS / 1 **FAIL** | Pins **30/30** recomputed exact (compact `source_payload`); spec sha+size exact; manifest **16/16** sha+bytes; no-write holds — HEAD/tree/132-entry status sha identical to receipt before/after. **Fabricated commits: FAIL — 9** untracked resolutions carry `commit=9a70501a…` with `commit_reason=null`: U0006 ×3, U0007, U0008 ×2, U0011, U0012 `AGENTS.md`/`README.md`. HEAD contains none of these paths (`ls-tree -r` = 0 hits for `backfill_daily|check_daily|AGENTS.md|README.md|TEAM.md`). Cause: `:620` `commit = HEAD if repo_exact`, and `repo_exact` is true for `DISK_FILE_UNTRACKED`/`DISK_DIR_UNTRACKED` because `matched == declared_path`. |
| 6 | B1_ACCEPTED | **NO** | split below |

---

## BASE-009 adjudication — artefact, not a reader/behaviour defect

Measured cause chain:
- `data_plane/config/*.yaml` is **genuinely HEAD-tracked**: `f077290d data_policy.yaml`, `6267f8d0 provider_profile.yaml` (`git ls-tree -r HEAD -- data_plane/config`). `src/backfill_daily.py` and `check_daily.py` are **absent everywhere in HEAD** (295-file tree, 0 hits).
- Mutation (b) resolves each declared path against the real tree with an **empty disk index** → glob = `TRACKED_GLOB` (correct). `upgraded=[TRACKED_GLOB]` appears only because the POS classification was overwritten `TRACKED_GLOB → FOUND_IN_FDA_CARRIER` by the carrier escalation at `b1_reader2.py:524‑526` (fires on *any* basename `carrier_hits`, even when `repo_exact`). Nothing about the HEAD surface differs between POS and mutation.
- Mutation (a) is constructible: withholding locators over 3/3 targets yields `DELETE_ff=BASE_ROW_MISSING`. So the unit is not untestable — only arm (b) is.

**Conclusion:** the FAIL is an artefact of (i) applying a unit-level "no target may become TRACKED" predicate to an intrinsically mixed-surface unit (one HEAD-tracked glob + two untracked files + carrier siblings), amplified by (ii) a real but *separate* labelling defect (a HEAD-tracked classification being overwritten). Per-target resolution behaviour is correct.

**Minimal correct fixture — no new fixture needed:**
1. Gate the escalation (`if res.get("carrier_hits") and not repo_exact`). Then R0 stays `TRACKED_GLOB`, `upgraded=[]`, `NEG.BASE-009` PASSes on the applicable arm (a), with arm (b) recorded `applicable=false`; `U0009` verdict also stops naming a carrier surface it never read.
2. If a *positive* upgrade test is wanted, make mutation (b) target-scoped (withhold only the targets whose baseline came from a non-`REPO_ROOT` surface, expect `BASE_ROW_MISSING` for that target) or split the unit into a tracked-glob unit and a carrier-only unit.

If neither is done, the honest verdict is `HOLD_SURFACE_NOT_CONSTRUCTIBLE` (the code path already exists at `b1_cases.py:231`), **not** FAIL — and explicitly not PASS. rev7's "必須用 purpose-built fixture" is right that PASS must not be forced, wrong that a new fixture is required: the "upgrade" is the mislabel, not the surface.

---

## B1_ACCEPTED supported? **NO** — 54/60 PASS (52 effective; 2 PASSes ride a wrong-entity locator), 1 FAIL, 5 HOLD.

**(a) Maker-fixable (code/evidence)**
1. Commit fabrication: 9 untracked resolutions still `commit=HEAD`, `reason=null` (`:619‑624`); must be `commit=null` + explicit reason.
2. Carrier escalation overwrites exact classifications (`:524‑526`) → `U0009` verdict contradicts its own 3/3 `REPO_ROOT` resolutions; root cause of the BASE-009 FAIL.
3. Glob carrier escalation ignores the directory prefix (`:502‑517`): `data_plane/config/*.yaml` produced 12 bogus carrier hits from bare `*.yaml` across the carrier tree.
4. `U0012` bare siblings: no `FABRIC/…` prefix propagation; `AGENTS.md`/`README.md` resolve to unrelated repo-root files as `EXACT` while the same record says "absent from the brownfield repo" (5,328/6,086 B vs carrier 3,651/4,410 B).
5. Allow-list is root-level only; per-artefact shas never consulted → `tests/test_fda_*` (unlisted) marked `al=true`; bound-but-listed BASE-017 target marked `al=false/root=null`.
6. `FDA_ARTEFACTS` 15 ≠ allow-list 16 (`README.md` outside the EOL verdict).
7. Receipt does not pin its two new inputs — no sha for `b1_locator_bindings.json`/`b1_source_allowlist.json`; binding trust is binding-vs-file only, so a checker must hash them out-of-band (I did).
8. `measured` empty for the bound BASE-017 target — bound sha is echoed, not measured; record the measured sha.
9. `SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` is vacuous — `resolve()` ignores the supplied disk index for exact paths (`os.path.isfile` on the real FS) → classes come back `DISK_*`; the assertion cannot fail.
10. `NEG.FDA_broker_live_submit` mutation ≠ §06 column; detector constant in `submit` → arm non-discriminating.
11. `commit_reason="no locator at the declared path"` used for targets that *do* have a verified binding.

**(b) SPEC / Owner-authority blocking**
1. Declared-path drift: BASE-009 `src/backfill_daily.py`,`check_daily.py` vs `data_plane/src/…`; BASE-017 bare `FDA_INTEROP_DISPOSITION.yaml` vs `governance/…` — bindings are `CANDIDATE_NOT_RATIFIED`; needs Owner ratification or spec revision (+new sha).
2. Mirror carrier: structured allow-list covers primary only (`source_id=SST.FDA.PRIMARY_CARRIER`); the second carrier still feeds the EOL verdict and matrix vocabulary → authorise it structurally or stop using it.
3. Slot→artefact mapping: `slot_reference_counts = 0` for all 7 slots in both carriers; the 7 FDA POS cases are explicitly `CARRIER_LEVEL_ONLY / slot_mapping=unproven`.
4. §06 KERNEL NEG mutation `改一個受保護欄位` needs the Domain Owner's semantic oracle.

**(c) Oracle-blocked**
- 5 × `B1.NEG.KERNEL_*` `HOLD_ORACLE_UNBOUND` — cannot become PASS without a ratified semantic oracle; the second-writer scan is correctly supplementary only.

Nothing was modified; git used as read-only plumbing (`git -c safe.directory=*`, no config written).