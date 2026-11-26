# B2 separated checker — round 1 (read-only)

You are the independent checker for batch B2 (1,465 units / 2,930 cases) of SST/SQS-THC PH01 W0.

Frozen candidate: `40_OPS/b2_candidate_freeze_*.json` (highest timestamp). Re-hash every pinned
file yourself; do not trust its self-report.

## What changed since the previous session (and what to attack)

The previous B2 receipt claimed `2,930 PASS` under `claim_ceiling = PAYLOAD_INTEGRITY_ONLY`. Every
NEG mutated `__b2_neg_probe__` and observed the payload hash change — a tautology. The new receipts
(`b2_toolreadset_*` @2 and `b2_tqaep_*` @2) claim `claim_ceiling = ROW_SEMANTICS_AND_CLASS_MUTATION`.

Attack each claim:

1. **Quadrant census** — 440/513/378/54 with `all_three_signals_agree`. Re-derive it independently
   from the SPEC (namespace prefix and `q_row.full_key`); the header says three signals but the SPEC
   has no per-quadrant section. Check the non-Q count (80) actually equals HARD 18 + E00_TECH 8 +
   TECH_ROUTE 54.
2. **Requiredness** — 18 HARD preserved, 0 downgraded, `disagreement_count = 0`. Check whether the
   independence claim is real or whether `requiredness_row` is being compared to itself for Q rows
   (the SPEC's Q row column 2 is often prose, not a token). If the check is vacuous for some kinds,
   say which and how many.
3. **Pin reconciliation** — the receipt now says the historical 72 is *not reproducible* and that
   the old TQAEP's 54 equals the TECH_ROUTE count. Verify both numbers against the bytes.
4. **NEG class mutations** — 1,465 NEG, expected distribution 1,385 / 72 / 8 (SPEC §06). For each
   class, is the mutation discriminating? Specifically:
   - `NAMESPACE_JOIN_DENY`: is the *baseline* join clean (exactly one row) and is the refusal
     non-vacuous (the naive suffix lookup would have matched)?
   - `TOOL_REQUIREDNESS_HOLD`: HARD row losing HARD → hold; route row claiming HARD + enablement →
     hold; baseline clean in both directions?
   - `STATE_CONFLICT`: does the baseline pass and the two-state mutation fail?
   Report any class where the oracle would return the expected code for *any* input.
5. **Clause identity** — the receipt declares the generator's clause-sha rule UNBOUND and claims no
   clause identity. Is that honest, or is clause identity silently assumed elsewhere? Try to
   reproduce one `direct_clause_sha` yourself.
6. **Parent source** — `PARENT_SOURCE_REBOUND_BY_SHA` (declared path has a stale `W0_B0-m` segment).
   Verify the rebound file's sha really equals `d95c8ac6…` and that the rebind is labelled
   `CANDIDATE_NOT_RATIFIED`.

Standing: spec sha `140de5bc…` / 8,016,371 B; no-write; 2,930 case ids with no orphan and none
missing; `first_fail` never null on a NEG that claims PASS.

Answer: is the new `claim_ceiling` supported? What may B2 claim, and what must it not claim? Split
defects into Maker-fixable / Owner-authority / Original-Domain-Owner. Write to the `-o` path.
