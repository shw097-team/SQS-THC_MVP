# B1 separated checker — round 4 (read-only)

You are the independent checker for batch B1 of SST/SQS-THC PH01 W0 (wave P1-W00M). You did rounds 1–3. Round 3 measured candidate `9303ce87…`/`22613ebc…` and returned `B1_ACCEPTED = NO` with 11 maker-fixable items, 4 SPEC/Owner items and 5 oracle-blocked cases.

A new candidate was frozen after round 3. Read `40_OPS/b1_candidate_freeze_*.json` (highest timestamp) — it pins every input byte you are judging. Re-hash it yourself; do not trust its self-report.

## What to judge (narrow, per round-3 item number)

Measure, don't infer. For each item give verdict PASS / PARTIAL / FAIL plus the measured basis (file:line, command, hash).

1. **Receipt does not pin its inputs** → is `inputs.{b1_locator_bindings.json,b1_source_allowlist.json}` present in the run receipt with bytes + raw sha256, and does re-hashing the files now match?
2. **BASE-017 bound target `measured` empty** → does the bound target now carry a *measured* record (raw sha recomputed from the file), not an echo?
3. **`commit_reason` "no locator at the declared path" on bound targets** → is the reason now specific (binding / carrier / disk-untracked / none) and true?
4. **`SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED` vacuous** → is the assertion now falsifiable? Try to break it: can a caller-supplied disk index produce a declared-path EXACT/tracked claim?
5. **`FDA_ARTEFACTS` 15 vs allow-list 16 (`README.md`)** → is the collision inventory now over all 16 allow-listed artefacts?
6. **`NEG.FDA_broker_live_submit` detector constant** → does the detector read the action token (submit/replace/cancel vs read) so POS and NEG are not satisfied by one expression?
7. **Glob carrier escalation ignored the directory prefix** → can a declared glob such as `data_plane/config/*.yaml` now only match path-parity carrier paths?
8. **`U0012` bare siblings (`AGENTS.md`/`README.md`) resolved to unrelated repo-root files** → are they now resolved to the carrier entity by prefix propagation, and is the old repo-root file no longer used?
9. **Allow-list is root-only** → is per-artefact enforcement now in force (root + relative path + measured sha)? Check both directions: an unlisted carrier path must NOT be `allow_list_declared=true`; a bound-but-listed path must be `true`.
10. **Commit fabrication** → count resolutions with `commit=HEAD` whose `read_domain != REPO_ROOT`. Round 3 measured 9.
11. **BASE-009 adjudication** → is the carrier escalation now gated so a HEAD-tracked classification is never relabelled (the round-3 root cause of the FAIL)?

Also judge, as standing checks:

- Pins: `spec.payload_pin_failures` empty; spec sha/size; allow-list 16/16 sha+bytes against the files on disk.
- No-write: HEAD/tree/`git status --porcelain` unchanged before/after (the receipt records both).
- Case tally honesty: `61` cases must not show PASS where the baseline is invalid, and no `first_fail=null` on a NEG.
- **New claim to attack:** the candidate now restricts the carrier read surface to the 16 allow-listed artefacts. Consequence: `BASE-018` target `tests/test_fda_*` is reported `TYPED_MISSING_OUT_OF_ALLOW_LIST_SCOPE` and its POS is `HOLD_SCOPE_NOT_COVERED`. Is that the correct honest verdict, or is it being used to hide a missing artefact?
- Is `B1_ACCEPTED` supported *now*? If not, list exactly what remains and who owns it (Maker / Owner / Original Domain Owner).

## Rules

- Read-only. Do not modify, create or delete anything in the wave root; do not run `git` write commands; do not checkpoint/fetch/import/execute repo code.
- Do not accept the Maker's self-assessment. Re-derive every number.
- `HOLD` is a legitimate result; do not convert a HOLD into PASS or FAIL to make the batch look better or worse.
- 5 × `B1.NEG.KERNEL_*` require a ratified semantic oracle from the original Domain Owner; if still absent they stay `HOLD_ORACLE_UNBOUND`, and that is not a Maker defect.

Write the verdict to the `-o` path in this form: a `## Read-only round 4 — measured` header, a baseline paragraph with your re-measured hashes, a table of the 11 items, a standing-checks table, then `B1_ACCEPTED supported? YES/NO` with the split into Maker-fixable / Owner-authority / oracle-blocked.
