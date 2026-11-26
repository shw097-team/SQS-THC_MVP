# B1 separated checker — round 5 (read-only, narrow)

Round 4 closed 9/11 items and listed 5 Maker-fixable defects. A new candidate was frozen:
`40_OPS/b1_candidate_freeze_*.json` (highest timestamp). Re-hash it yourself.

Judge only these five, plus regression:

1. `carrier_present_out_of_scope` collapsed carriers → is it now a per-carrier list, primary first,
   with `allow_listed_root` true for the allow-listed primary (BASE-018 must name both carriers)?
2. `discrimination` record for FDA slots → does it now reach the TQAEP `observed` for both POS and
   NEG of `broker_live_submit` (so the receipt shows a discriminating measurement)?
3. Carrier `commit_reason` wording → is it now "no brownfield commit identity …" (true statement,
   not "no commit identity exists")?
4. `candidate_digest_rule` → does the declared rule now reproduce the digest? Recompute it.
5. `DELIVERY_MANIFEST.json` currency → the Maker rebuilds it at the end of the session; check whether
   `current_pointers` and the code hashes match the frozen candidate. If it is still stale, say so.

Regression: re-derive 30/30 payload pins, spec sha/size, allow-list 16/16, no-write equality, the
case tally (60 cases) and the 5 `HOLD_ORACLE_UNBOUND`. Confirm the 11 round-3 items have not
regressed. Do not re-litigate the Owner decisions (D-1…D-4).

Answer `B1_ACCEPTED supported? YES/NO` with the split into Maker-fixable / Owner-authority /
oracle-blocked. Write to the `-o` path.
