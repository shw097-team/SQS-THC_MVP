## Verdict table

| # | Task | Verdict | Basis (measured) |
|---|---|---|---|
| 1 | 30× `payload_sha` | **PASS** | Recomputed compact `source_payload` (ensure_ascii=False, `,`/`:`) → 30/30 exact; cross-checked U0030 with an independent SHA-256 path. |
| 2 | spec raw sha + 16-file manifest | **PASS** | Spec = `13294ca…4a3753` (expected); manifest `candidate_manifest_…tsv` 16/16 rows match raw sha256 **and** byte size. |
| 3 | 23 BASE/KERNEL resolution | **FAIL** | Localisation is factually right for 22/23, but `B1.U0012` is reported `OBSERVED_IN_WORKING_TREE_UNTRACKED` while its declared target `FABRIC/fabric-desktop-automation/TEAM.md` has **no locator** (only basename hits). |
| 4 | 7 FDA static detectors | **FAIL** | 6/7 code-correct; `broker_live_submit` POS oracle is inverted (spec POS expects `FIN_ORDER_DENY_ALWAYS`, harness asserts `None`). |
| 5 | 5 KERNEL NEG | **FAIL** | "one writer per kernel" invariant is not implemented: literal grep on `KERNEL_OWNER_ID` only, and refusal is a hand-built constant. SEMANTIC_ORACLE_UNBOUND handling is correct. |
| 6 | no-product-write | **PASS** | HEAD and `git status` stdout sha reproduced byte-exactly today; caveats below. |
| 7 | B1_ACCEPTED | **NO** | Blockers listed. |

---

## Facts I measured (not asserted)

- Spec sha256 `13294cada156a2c0beb485bb940a316dd540173273c90dc721570604ca4a3753`, 185 197 B — matches expected.
- Manifest: 16/16 sha+size OK (appendices live in `證據型附錄/`, all resolve).
- Repo HEAD `9a70501ad4bbf315c675894a7a58c0f98bf18f47`, tree `688de895b003c35da1b85c0c7926089a44e78855`, 295 tracked files, `git status --porcelain=v1` stdout sha256 = `59a313ed990e43a7b470df83a2ddf390b3b931be81ce56d0583e3f986d0ea2e3` — identical to the receipt's before/after; 132 entries (2 `M`, 130 `??`).
- 5 kernel blobs at HEAD (`cat-file`) = spec §04.K2 raws exactly (`90a5f4d4`, `21e0150f`, `ea1e13cd`, `288a2a0e`, `d2a143c5`).
- Resolution census (my oracle): 11 HEAD-tracked (U0001-05, U0010, U0019-23), 1 partial (U0009), 5 disk-untracked only (U0006/07/08/11/12), 6 carrier-only (U0013-18). Every locator the receipt cites does exist; **no** false-"missing".
- Carriers `FHS/Fabric/FABRIC/...` vs `FHS/Fabric/Fabric-rebind-publish/...`: 15/15 artefacts differ at raw sha, **0/15** differ after CRLF→LF. `IDENTICAL_MODULO_EOL` is true; the two "carriers" are one source in two EOL flavours.
- Literal slot-name hits in both carriers = 0 for all 7 slots (matches receipt).
- 60 §06 case IDs ↔ receipt case IDs: exact bijection; all 30 unit `case_ids` join.
- 20 B1.ROOTS edges, all `physical_status=UNKNOWN`.

---

## FAIL / HOLD detail + smallest closing evidence

**T3 · `B1.U0012` mis-located, verdict over-claims**
- Declared cell (source `05.12`, verified in the r2 parent): ``FABRIC/fabric-desktop-automation/TEAM.md、AGENTS.md、README.md``. At HEAD and repo root all three are absent (root has *unrelated* untracked `TEAM.md` 741 B `2b4226f4…`, `AGENTS.md` 5 328 B `768411ac…`, `README.md` 6 086 B `988f9295…`). The real files exist only in the carriers (`TEAM.md` 5 768 B `1936a465…`, `AGENTS.md` 3 651 B, `README.md` 4 410 B).
- Receipt says `FOUND_ELSEWHERE_ON_DISK` for the first target and `DISK_FILE_UNTRACKED` for the other two, then upgrades the unit to `OBSERVED…`. `b1_reader2.py` skips carrier escalation because the class isn't `ABSENT_IN_TREE_AND_DISK`.
- This is verbatim the unit's own NEG mutation ("把 declared/remote 當 local qualified" → `BASE_ROW_MISSING`).
- Close with: rows showing declared-path-exact locator + raw sha for all three, or `first_fail=BASE_ROW_MISSING`.
- Secondary, same family: `B1.U0017` `FDA_INTEROP_DISPOSITION.yaml` was silently relocated to `governance/…`; `B1.U0018` `docs/FDA_USER_GUIDE.md` "matched" points at repo `evidence/review/…` (20 138 B) while `carrier_hits` point at a 22 327 B file — two different contents under one declared path.

**T4 · `broker_live_submit` POS inverted**
- §06 row `B1.POS.FDA_broker_live_submit` = "DENY invariant檢查；無允許效果POS", Expected FirstFail **`FIN_ORDER_DENY_ALWAYS`**. `b1_fda_static.run_slot` asserts `pos_res == None` for *every* slot; `d_broker_live_submit` returns `None` when `submit` is falsy, and the POS fixture `{"submit": False}` contains no live-submit intent at all.
- `b1_cases.py` POS branch never compares `expected_first_fail`, so this row is vacuously PASS while the spec demands a denial.
- Close with: `pos_first_fail == "FIN_ORDER_DENY_ALWAYS" == neg_first_fail` on a POS fixture that actually expresses a live submit request.
- Minor: `xs_backtest` exercises only the "lookahead" arm (the "無權" arm is untested); `broker_external_event_read` mutation keeps `broker_seq/receipt/BoR` while relabelling `origin=GUI_ACK` — not a genuine "GUI ACK 冒 Fill" record.

**T5 · KERNEL "no shadow writer" not actually checked**
- The scan is `p.startswith("src/kernel/") and p.endswith(".py") and "KERNEL_OWNER_ID" in blob`. I measured the owner constant per kernel: fsdt `KERNEL_OWNER_ID`, temporal `_EXPECTED_OWNER`, knowledge `OWNER_ID`, harness `HARNESS_OWNER_ID`, capability `_LIFECYCLE_OWNER_ID`. So `holders` = `[src/kernel/fsdt/__init__.py]` only; for 4/5 kernels `second == []` is vacuous.
- The refusal side is a literal: `fixture={"module": ".../shadow_writer.py","declares_owner":True}` → `"SECOND_WRITER"` by construction. No code path, no scanner is exercised.
- Mutation also does not match the spec column: §06 KERNEL NEG mutation is **"改一個受保護欄位"**, not "add a shadow writer".
- SEMANTIC_ORACLE_UNBOUND *is* recorded separately (`separate_limitation`, "NOT the result of this case") — that sub-requirement is met.
- Close with: per-kernel marker table driving the scan, and a refusal fixture fed through the same scanner (mutated module discovered by the scan), producing `SECOND_WRITER`.

**T6 caveats (verdict still PASS)**
- The measurement is true and independently reproducible, but it is blind to `.gitignore`d paths and mtime-only writes, and the tree is already dirty (2 `M`: `data_plane/config/provider_profile.yaml`, one `docs/…使用說明文檔.md`).
- Provenance gap: cited receipt `b1_run_20261126T120202.json` (12:02:02) **predates** `b1_reader2.py` (12:17:24). Its `B1.U0009.first_fail` is `B1_SOURCE_DECLARED_PATH_MISSING`, which the shipped reader cannot emit (it can only emit `BASE_ROW_MISSING` for `kind=BASE`). The receipt is therefore not reproducible from the shipped code.

**T4/T3 provenance note** — for `B1.U0009` the receipt reports HEAD-blob bytes (`provider_profile.yaml` `0e3108…`, 1 549 B) while the working copy is `b68d39…`, 2 079 B. HEAD values are legitimate, but no `local`/disk column exists, contrary to the "declared/remote/local/observed 分欄" rule.

---

## 7 · Is B1_ACCEPTED supported? No.

Blocking items:
1. `B1.POS.FDA_broker_live_submit` reported PASS with `first_fail=null`; spec requires `FIN_ORDER_DENY_ALWAYS`. (1 of 60 cases false.)
2. 5 × `B1.NEG.KERNEL_*` PASS rest on a vacuous invariant and a hardcoded refusal; the spec mutation was replaced.
3. `B1.U0012` claims OBSERVED with no locator for its declared target (and U0017/U0018 carry silently relocated paths).
4. Untracked-only units (U0006/07/08/11/12) cannot produce the declared typed output `CommitPathSpan` (commit+path+blob); no row emits a `missing` set either — `RepoReadSet.commit/path/blob/missing` is not fully materialised.
5. Six units' locators are read from `C:\Projects\Agent_Workspace\FHS\…`, i.e. outside the authorised RepoRoot, with no `authority`/allow-list evidence in the receipt (§02 requires an authorised allow-list per source).
6. No separated checker; the tqaep receipt itself states "Maker self-check only", and it consumes a receipt that the shipped reader cannot regenerate (T6).

Everything else I could test holds: pins, spec digest, manifest, HEAD/status stability, kernel blob identity, carrier EOL identity, slot-name absence, case coverage, and the other six FDA NEG codes.