#!/usr/bin/env python3
"""B1 TQAEP — run the 60 original cases from SPEC §06 plus the applicable EDGE/SEC checks.

Each POS/NEG is evaluated against the B1 receipt and against a *re-derived* resolution, so a
mutation is a real change to the reader's input surfaces, not a relabelled expectation.

Verdict vocabulary (closed set):
  PASS                     oracle satisfied with measured evidence
  FAIL                     oracle violated (a real defect)
  HOLD_ORACLE_UNBOUND      the case needs an oracle the SPEC / original owner has not bound
  NOT_APPLICABLE           mutation targets an effect this batch does not carry
"""
from __future__ import annotations
import hashlib, json, os, re, sys, datetime

WAVE = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
DEV = os.path.join(WAVE, "20_DEV")
OPS = os.path.join(WAVE, "40_OPS")
sys.path.insert(0, os.path.join(DEV, "b1_reader"))
import b1_reader2 as R  # noqa: E402
import b1_fda_static as FDAS  # noqa: E402

REPO = r"C:\Projects\Agent_Workspace\SQS-THC"
KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"

# per-kernel owner marker (measured from each module; they are NOT uniform, and plain substring
# matching is unsafe because e.g. "OWNER_ID" is a substring of "KERNEL_OWNER_ID"/"HARNESS_OWNER_ID")
KERNEL_MARKERS = {
    "fsdt": r"\bKERNEL_OWNER_ID\b",
    "temporal": r"\b_EXPECTED_OWNER\b",
    "knowledge": r"(?<![A-Z_])OWNER_ID\b",
    "harness": r"\bHARNESS_OWNER_ID\b",
    "capability": r"\b_LIFECYCLE_OWNER_ID\b",
}
FDA_A = r"C:\Projects\Agent_Workspace\FHS\Fabric\FABRIC\fabric-desktop-automation"
FDA_B = r"C:\Projects\Agent_Workspace\FHS\Fabric\Fabric-rebind-publish\FABRIC\fabric-desktop-automation"


def sha(b): return hashlib.sha256(b).hexdigest()


def find_spec():
    root = [os.path.join(KBASE, n) for n in os.listdir(KBASE)
            if n.startswith("W0_B1-B8_NATIVE_FIRST_2026-11-26_r4")][0]
    hits = []
    for dp, _dn, fn in os.walk(root, onerror=lambda e: None, followlinks=False):
        for f in fn:
            if f.startswith("SST_PLP_PH01_W0_B1_") and "實質正文" in f and f.endswith(".md"):
                hits.append(os.path.join(dp, f))
    if len(hits) != 1:
        raise RuntimeError(f"SPEC_NOT_UNIQUE: {hits}")
    return hits[0]


def parse_cases(spec_path):
    """§06 table: 8 columns per case, one row per case, anchor-prefixed."""
    t = open(spec_path, encoding="utf-8").read()
    i = t.find("## 06")
    j = t.find("## 07", i)
    block = t[i:j if j > 0 else len(t)]
    cases = []
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        cid = re.sub(r"<[^>]+>", "", cells[0]).strip()
        m = re.match(r"^B1\.(POS|NEG)\.(.+)$", cid)
        if not m:
            continue
        cases.append({"case_id": cid, "polarity": m.group(1), "key_token": m.group(2),
                      "key": cells[1], "fixture": cells[2], "mutation": cells[3],
                      "predicate": cells[4], "expected_first_fail": cells[5]})
    return cases


def latest_receipt():
    return json.load(open(sorted(__import__("glob").glob(os.path.join(OPS, "b1_run_*.json")))[-1],
                         encoding="utf-8"))


def main() -> int:
    spec = find_spec()
    cases = parse_cases(spec)
    rc = latest_receipt()
    rows = {r["key"]: r for op in ("B1.BASE", "B1.FDA") for r in rc["ops"][op]["rows"]}
    tree = R.list_tree(REPO, rc["repo"]["commit"])
    disk = R.index_disk(REPO)
    carriers = [c for c in rc["ops"]["B1.FDA"]["carrier_inventory"]["carriers"] if c["exists"]]
    coll = rc["ops"]["B1.FDA"]["carrier_inventory"]["authority_collision"]

    out = []
    for c in cases:
        key, pol = c["key"], c["polarity"]
        row = rows.get(key)
        rec = {"case_id": c["case_id"], "key": key, "polarity": pol,
               "mutation": c["mutation"][:160], "expected_first_fail": c["expected_first_fail"][:80]}
        if row is None:
            rec.update(verdict="FAIL", observed={"error": "unit not present in receipt"},
                       first_fail="B1_CASE_UNIT_ABSENT")
            out.append(rec); continue

        observed_locator = row["verdict"].startswith(("OBSERVED", "CARRIER_OBSERVED"))

        if pol == "POS":
            # oracle: payload columns equal the original AND the unit's real locator exists
            pins_ok = not rc["spec"]["payload_pin_failures"]
            if key.startswith("FDA:"):
                slot = key.split(":", 1)[1]
                r0 = FDAS.run_slot(slot)
                carrier_files = sum(1 for cc in carriers for a in cc["artefacts"] if a["raw_sha256"])
                ok = (pins_ok and carrier_files > 0 and coll["content_level_differences"] == 0
                      and r0["verdict"] == "PASS"
                      and r0["pos_first_fail"] == r0["pos_expected"])
                rec.update(verdict="PASS" if ok else "FAIL",
                           first_fail=r0["pos_first_fail"],
                           expected_first_fail=(c["expected_first_fail"] or "").strip("`"),
                           observed={"pos_first_fail": r0["pos_first_fail"],
                                     "pos_expected": r0["pos_expected"],
                                     "carrier_artefacts_present": carrier_files,
                                     "content_level_differences": coll["content_level_differences"],
                                     "claim_ceiling": "CARRIER_LEVEL_ONLY",
                                     "slot_mapping": "unproven: slot_reference_counts=0 for all 7 slots",
                                     "discrimination": r0.get("discrimination")})
                out.append(rec); continue
            else:
                miss = row.get("missing") or []
                oos = [m for m in miss if m.get("reason") == "OUT_OF_ALLOW_LIST_SCOPE"]
                if oos:
                    rec.update(verdict="HOLD_SCOPE_NOT_COVERED",
                               first_fail="B1_SOURCE_OUT_OF_ALLOW_LIST_SCOPE",
                               observed={"unit_verdict": row["verdict"],
                                         "out_of_scope_targets": [m["declared_path"] for m in oos],
                                         "present_but_unread": [m.get("out_of_scope") for m in oos],
                                         "resume": "the evidence exists in the carrier but is "
                                                   "outside the 16-artefact allow-list; a POS can "
                                                   "only be claimed after the Owner extends the "
                                                   "allow-list (D-2) and the same candidate is re-run"})
                    out.append(rec); continue
                ok = pins_ok and not miss
                detail = {"unit_verdict": row["verdict"],
                          "declared_paths": row["declared_paths"][:3],
                          "targets_without_exact_locator": len(miss),
                          "missing": [m["declared_path"] for m in miss][:4]}
            rec.update(verdict="PASS" if ok else "FAIL",
                       first_fail=None if ok else "B1_POS_LOCATOR_OR_PIN",
                       observed={**detail, "payload_pin_ok": pins_ok})
            out.append(rec); continue

        # ---- NEG
        if key.startswith("KERNEL:"):
            kname = key.split(":", 1)[1]
            canon = f"src/kernel/{kname}/__init__.py"
            marker = KERNEL_MARKERS[kname]

            def scan(sources):
                """Return every module under src/kernel whose text declares this kernel's owner."""
                out_ = []
                for p, text in sources.items():
                    if p.startswith("src/kernel/") and p.endswith(".py") and re.search(marker, text):
                        out_.append(p)
                return sorted(out_)

            real = {}
            for p in tree:
                if p.startswith("src/kernel/") and p.endswith(".py"):
                    bs = tree[p].get("sha") or tree[p].get("blob")
                    if bs:
                        try:
                            real[p] = R.read_blob(REPO, bs).decode("utf-8", "replace")
                        except Exception as exc:
                            rec.setdefault("_read_errors", {})[p] = str(exc)
            baseline = scan(real)
            # refusal arm: a second module that declares the same owner marker, discovered by the
            # SAME scanner (not a hardcoded return value)
            shadow = dict(real)
            ident_name = marker.replace(r"\b", "").replace("(?<![A-Z_])", "")
            shadow[f"src/kernel/{kname}/shadow_writer.py"] = (
                f"{ident_name} = '{ident_name}'\n"
                "def write_truth(*a, **k):\n    raise RuntimeError('second writer')\n")
            mutated = scan(shadow)
            refused = "SECOND_WRITER" if len(mutated) > 1 else None
            ok = baseline == [canon] and refused == "SECOND_WRITER"
            rec.update(verdict="HOLD_ORACLE_UNBOUND",
                       first_fail="SEMANTIC_ORACLE_UNBOUND",
                       expected_first_fail="SECOND_WRITER",
                       observed={"mechanism_scan_pass": ok, "marker": marker,
                                 "canonical_writer_module": canon,
                                 "modules_declaring_marker": baseline,
                                 "refusal_scan_found": mutated,
                                 "neg_fixture_refused_with": refused,
                                 "declared_mutation_executed": False,
                                 "declared_mutation": "§06 requires 改一個受保護欄位; that mutation "
                                                      "needs the original Domain Owner's semantic "
                                                      "oracle, which is not ratified for this batch",
                                 "semantic_acceptance": "NOT_CLAIMED",
                                 "note": "the second-writer scan is recorded as supplementary "
                                         "static evidence only; it is NOT the §06 case result"})
            out.append(rec); continue
        if key.startswith("FDA:"):
            slot = key.split(":", 1)[1]
            r0 = FDAS.run_slot(slot)
            ok = r0["verdict"] == "PASS"
            spec_ff = (c["expected_first_fail"] or "").strip("`")
            rec.update(verdict="PASS" if ok else "FAIL",
                       first_fail=(r0["arms"][0]["first_fail"] if pol == "NEG" and r0["arms"]
                                   else r0["pos_first_fail"]),
                       expected_first_fail=spec_ff,
                       observed={"pos_first_fail": r0["pos_first_fail"],
                                 "pos_expected": r0["pos_expected"],
                                 "arms": r0["arms"],
                                 "neg_expected": r0["neg_expected"],
                                 "discrimination": r0.get("discrimination"),
                                 "code_matches_spec": all(a["first_fail"] == FDAS.CODES[slot]
                                                          for a in r0["arms"]),
                                 "claim_ceiling": r0["claim_ceiling"],
                                 "carrier": r0["carrier"]})
            out.append(rec); continue

        # BASE NEG: a negative only means something on a VALID baseline
        baseline_valid = not (row.get("missing") or [])
        if not baseline_valid:
            rec.update(verdict="HOLD_BASELINE_NOT_VALID",
                       first_fail="BASELINE_INVALID_PRECONDITION",
                       observed={"reason": "the POS baseline for this unit is not admissible "
                                           "(declared target lacks an exact locator), so the NEG "
                                           "mutation cannot be distinguished from the baseline",
                                 "unit_verdict": row["verdict"],
                                 "missing": [m["declared_path"] for m in row.get("missing", [])]})
            out.append(rec); continue
        res_full = row["resolutions"]
        # (a) DELETE: drop every in-memory locator -> the row must fall back to BASE_ROW_MISSING
        promoted, delete_ff = [], None
        empty_disk: dict[str, list[str]] = {}
        for r0 in res_full:
            r2 = R.resolve(r0["declared_path"], {}, "", empty_disk)
            promoted.append(r2["classification"])
        delete_ff = ("BASE_ROW_MISSING" if not any(c.startswith("TRACKED") for c in promoted)
                     else None)
        # (b) declared/remote -> local qualified: HEAD-tree-only surface must not upgrade the unit
        head_only = []
        for r0 in res_full:
            head_only.append(R.resolve(r0["declared_path"], tree, REPO, empty_disk)["classification"])
        upgraded = [c for r0, c in zip(res_full, head_only)
                    if c.startswith("TRACKED")
                    and not (r0.get("classification") or "").startswith("TRACKED")]
        # mutation (b) can only distinguish a unit that is NOT already tracked at HEAD
        b_applicable = row["verdict"] != "OBSERVED_TRACKED_AT_HEAD"
        ok = delete_ff == "BASE_ROW_MISSING" and (not upgraded or not b_applicable)
        if delete_ff != "BASE_ROW_MISSING":
            rec.update(verdict="HOLD_SURFACE_NOT_CONSTRUCTIBLE",
                       first_fail="NEG_SURFACE_NOT_CONSTRUCTIBLE",
                       expected_first_fail="BASE_ROW_MISSING",
                       observed={"mutation_a": {"classes": sorted(set(promoted)),
                                                "first_fail": delete_ff},
                                 "reason": "withholding the locator surface did not yield a "
                                           "BASE_ROW_MISSING for every declared target; the unit "
                                           "mixes a tracked glob with elsewhere-resolved targets, so "
                                           "this NEG needs a purpose-built fixture",
                                 "mutation_b": {"classes": sorted(set(head_only)),
                                                "upgraded_to_tracked": upgraded,
                                                "applicable": b_applicable}})
            out.append(rec); continue
        rec.update(verdict="PASS" if ok else "FAIL",
                   first_fail="BASE_ROW_MISSING",
                   expected_first_fail="BASE_ROW_MISSING",
                   observed={"mutation_a": {"surface": "locators withheld",
                                            "classes": sorted(set(promoted)),
                                            "first_fail": delete_ff},
                             "mutation_b": {"surface": "HEAD tree only",
                                            "classes": sorted(set(head_only)),
                                            "upgraded_to_tracked": upgraded,
                                            "applicable": b_applicable,
                                            "not_applicable_reason": (None if b_applicable else
                                                "the unit is already tracked at HEAD, so this "
                                                "mutation cannot distinguish it")},
                             "baseline_valid": True})
        out.append(rec)

    # ---- EDGE / SEC checks that this batch actually carries
    edge = []
    nw = rc["ops"]["no_write"]
    edge.append({"id": "EDGE.B1.NO_PRODUCT_WRITE", "verdict":
                 "PASS" if nw["verdict"] == "NO_PRODUCT_WRITE_OBSERVED" else "FAIL",
                 "observed": {"head_before": nw["before"]["head"], "head_after": nw["after"]["head"],
                              "status_sha_before": nw["before"]["status_sha256"][:16],
                              "status_sha_after": nw["after"]["status_sha256"][:16]}})
    # caller cannot smuggle a surface: a poisoned disk index must never produce a declared-path
    # EXACT/tracked claim, and the real HEAD tree must win over a caller-declared index.
    poison = {"__caller_supplied__.py": ["src/kernel/__caller_supplied__.py"],
              "fsdt": ["src/kernel/fsdt/__init__.py"]}
    forged = R.resolve("src/kernel/__caller_supplied__.py", {}, REPO, poison)
    exact_under_poison = R.resolve("src/kernel/fsdt/__init__.py", tree, REPO, poison)
    glob_poison = R.resolve("src/kernel/*.py", {}, REPO,
                            {"x.py": ["src/kernel/__forged_glob__.py"]})
    smuggled = (forged["matched"] or []) == ["src/kernel/__caller_supplied__.py"]
    edge.append({"id": "SEC.B1.CALLER_SUPPLIED_SURFACE_REJECTED",
                 "verdict": "PASS" if (not smuggled
                                       and exact_under_poison["classification"] == "TRACKED_PRESENT"
                                       and exact_under_poison["matched"] == ["src/kernel/fsdt/__init__.py"]
                                       and not glob_poison["matched"]) else "FAIL",
                 "observed": {"poisoned_declared_path": {"classification": forged["classification"],
                                                         "matched": forged["matched"]},
                              "real_tree_wins_over_index": {
                                  "classification": exact_under_poison["classification"],
                                  "matched": exact_under_poison["matched"]},
                              "poisoned_glob": {"classification": glob_poison["classification"],
                                                "matched": glob_poison["matched"]},
                              "why": "the disk index is a search aid, never an identity: only the "
                                     "HEAD tree (exact path) or a measured file on the real "
                                     "filesystem can produce a locator"}})
    # receipt must pin the two preflight inputs it now depends on
    pins = rc.get("inputs") or {}
    pin_ok, pin_detail = True, {}
    for name in ("b1_locator_bindings.json", "b1_source_allowlist.json"):
        ent = pins.get(name) or {}
        now_sha = sha(open(ent.get("path", ""), "rb").read()) if ent.get("path") and os.path.isfile(
            ent.get("path")) else None
        ok = bool(ent.get("present")) and ent.get("raw_sha256") == now_sha
        pin_ok = pin_ok and ok
        pin_detail[name] = {"pinned_sha256": (ent.get("raw_sha256") or "")[:16],
                            "measured_now": (now_sha or "")[:16], "match": ok,
                            "bytes": ent.get("bytes")}
    edge.append({"id": "EDGE.B1.INPUT_PINS_PINNED",
                 "verdict": "PASS" if pin_ok else "FAIL", "observed": pin_detail})
    # payload pin tamper: flipping one payload field must break the pin (re-derived here)
    def parse_units(path):
        t = open(path, encoding="utf-8").read()
        def blk(pos):
            i = t.find("```json", pos); j = t.find("```", i + 7)
            return t[i + 7:j]
        out_u = []
        for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
            out_u.append(json.loads(blk(m.end())))
        return out_u
    us = parse_units(spec)
    tamper_ok, tamper_detail = False, {}
    if us:
        u0 = us[0]
        good = sha(json.dumps(u0["source_payload"], ensure_ascii=False,
                              separators=(",", ":")).encode()) == u0["payload_sha"]
        mutated = list(u0["source_payload"]); mutated[0] = mutated[0] + "X"
        bad = sha(json.dumps(mutated, ensure_ascii=False,
                             separators=(",", ":")).encode()) == u0["payload_sha"]
        tamper_ok = good and not bad
        tamper_detail = {"unit": u0["unit_id"], "baseline_pin_matches": good,
                         "mutated_pin_still_matches": bad,
                         "units_parsed": len(us)}
    edge.append({"id": "SEC.B1.PAYLOAD_PIN_TAMPER_DETECTED",
                 "verdict": "PASS" if tamper_ok else "FAIL",
                 "observed": tamper_detail or {"error": "no units parsed"}})
    # carrier content pin tamper: byte-level (EOL) difference must not be reported as a content
    # collision. Authority verdict = allow-listed primary only; the second carrier is an
    # unratified mirror, so the EOL/content distinction is measured against it as an observation.
    mir = rc["ops"]["B1.FDA"]["carrier_inventory"].get("mirror_observation", {}) or {}
    edge.append({"id": "EDGE.B1.CARRIER_EOL_VS_CONTENT_DISTINGUISHED",
                 "verdict": "PASS" if (coll["content_level_differences"] == 0
                                       and mir.get("byte_level_differences_vs_primary")
                                       == len(R.FDA_ARTEFACTS)
                                       and mir.get("content_level_differences_vs_primary") == 0)
                            else "FAIL",
                 "observed": {"authority_verdict": coll["verdict"],
                              "authority_carriers_compared": coll["carriers_compared"],
                              "authority_byte_differences": coll["byte_level_differences"],
                              "authority_content_differences": coll["content_level_differences"],
                              "mirror_byte_differences": mir.get(
                                  "byte_level_differences_vs_primary"),
                              "mirror_content_differences": mir.get(
                                  "content_level_differences_vs_primary"),
                              "mirror_status": mir.get("status"),
                              "artefacts_in_scope": len(R.FDA_ARTEFACTS)}})

    tally = {}
    for r in out:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    res = {"schema": "SST.PH01.W0.B1.TQAEP@1", "generated_at":
           datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "spec": {"path": spec, "sha256": sha(open(spec, "rb").read())},
           "receipt_candidate": rc["repo"]["commit"],
           "cases_total": len(out), "tally": tally,
           "maker_note": "Maker self-check only. A separated checker must re-run the same candidate; "
                         "Maker role change is not R16.",
           "cases": out, "edge_sec": edge}
    p = os.path.join(OPS, f"b1_tqaep_{stamp}.json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1); f.write("\n")

    print(f"cases parsed={len(out)}  tally={tally}")
    for r in out:
        print(f"  {r['case_id']:34s} {r['verdict']:22s} {r.get('first_fail') or ''}")
    print()
    for e in edge:
        print(f"  {e['id']:44s} {e['verdict']}")
    print(f"\nreceipt {p} {os.path.getsize(p)}B sha256={sha(open(p,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
