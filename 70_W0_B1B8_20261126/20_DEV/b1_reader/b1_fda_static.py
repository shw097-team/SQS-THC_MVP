#!/usr/bin/env python3
"""B1 — static typed-fixture detectors for the six FDA NEG cases.

Each case is a *typed contract* test that B1 can legitimately run statically: a POS fixture must
be admitted (detector returns None) and one single-field mutation must be refused with exactly the
first-fail the original SPEC names for that slot. This does NOT claim seven-slot runtime
qualification; it claims the typed refusal rule holds at the record level.

Slot -> code (SPEC §06, verbatim):
  watch_ui                  -> FDA_WINDOW_HOLD         (mutation 錯窗/過期)
  radar_signal              -> SIGNAL_TIME_HOLD        (mutation 假即時)
  xs_compile                -> COMPILE_RAW_MISSING     (mutation 缺 compiler raw)
  xs_backtest               -> BACKTEST_SCOPE_HOLD     (mutation lookahead/無權)
  at_simulated_order        -> SIM_BROKER_TYPE_DENY    (mutation 模擬升真成交)
  broker_external_event_read-> BROKER_FACT_MISSING     (mutation GUI ACK 冒 Fill)
  broker_live_submit        -> FIN_ORDER_DENY_ALWAYS   (DENY invariant, no allowed POS)
"""
from __future__ import annotations
import copy, datetime

ISO = "%Y-%m-%dT%H:%M:%S%z"


def _t(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, ISO)


def _need(d: dict, *keys) -> list[str]:
    return [k for k in keys if d.get(k) in (None, "", [], {})]


# ---------------------------------------------------------------- slot detectors
def d_watch_ui(p: dict) -> str | None:
    """Only-read observation must sit inside the lease window and on the bound build/SKU."""
    miss = _need(p, "window_id", "lease_ref", "build_ref", "sku", "observed_at", "valid_until",
                 "capture_sha")
    if miss:
        return "FDA_WINDOW_HOLD"
    if p["window_id"] != p["lease_ref"]:
        return "FDA_WINDOW_HOLD"                      # observation from another window
    if _t(p["observed_at"]) > _t(p["valid_until"]):
        return "FDA_WINDOW_HOLD"                      # expired window
    return None


def d_radar_signal(p: dict) -> str | None:
    """A signal may not be known after the decision instant it is claimed to inform."""
    miss = _need(p, "signal_id", "signal_known_at", "decision_asof", "source_sha")
    if miss:
        return "SIGNAL_TIME_HOLD"
    if _t(p["signal_known_at"]) > _t(p["decision_asof"]):
        return "SIGNAL_TIME_HOLD"                     # 假即時
    return None


def d_xs_compile(p: dict) -> str | None:
    """A compile verdict without the compiled script raw is not a verdict."""
    miss = [k for k in ("script_sha", "compiler_build") if p.get(k) in (None, "")]
    if "diagnostics" not in p:
        miss.append("diagnostics")
    if miss:
        return "COMPILE_RAW_MISSING"
    if not (len(p["script_sha"]) == 64 and all(c in "0123456789abcdef" for c in p["script_sha"])):
        return "COMPILE_RAW_MISSING"
    return None


def d_xs_backtest(p: dict) -> str | None:
    """Backtest needs PIT status, a pinned rule snapshot and a rights epoch covering the period."""
    miss = _need(p, "pit_status", "rule_snapshot_ref", "rights_epoch", "period_start", "period_end")
    if miss:
        return "BACKTEST_SCOPE_HOLD"
    if p["pit_status"] != "PIT_OK":
        return "BACKTEST_SCOPE_HOLD"                  # lookahead
    if _t(p["period_start"]) >= _t(p["period_end"]):
        return "BACKTEST_SCOPE_HOLD"
    return None


def d_at_simulated_order(p: dict) -> str | None:
    """A simulator fill stays a SimFill; it may never be typed as a broker fact."""
    miss = _need(p, "sim_receipt_ref", "fill_type", "qty", "simulator_build")
    if miss:
        return "SIM_BROKER_TYPE_DENY"
    if p["fill_type"] not in ("SIM_FILL",):
        return "SIM_BROKER_TYPE_DENY"                 # 模擬升真成交
    for k in ("broker_fact_ref", "broker_seq", "broker_receipt_ref"):
        if p.get(k):
            return "SIM_BROKER_TYPE_DENY"             # a sim object carrying broker provenance
    return None


def d_broker_external_event_read(p: dict) -> str | None:
    """An external fact needs the broker's own sequence/receipt and a book-of-record version."""
    miss = _need(p, "broker_seq", "broker_receipt_ref", "book_of_record_version", "provenance_sha")
    if miss:
        return "BROKER_FACT_MISSING"                  # GUI ACK is not a fill
    if p.get("origin") == "GUI_ACK":
        return "BROKER_FACT_MISSING"
    return None


def d_broker_live_submit(p: dict) -> str | None:
    """Deny invariant: every write-class action is refused; a read-only record is admitted.

    The detector must read the action token — a constant in `submit` would satisfy both the POS
    and the NEG arm with one expression (round-3 checker item 6/10).
    """
    if "action" not in p:
        return "FIN_ORDER_DENY_ALWAYS"                 # untyped record: never admissible
    if p.get("action") in ("submit", "replace", "cancel"):
        return "FIN_ORDER_DENY_ALWAYS"                 # no token, no connector, no allowed effect
    if p.get("action") == "read":
        return None                                    # read-only observation is admissible
    return "FIN_ORDER_DENY_ALWAYS"                     # unknown action is not a read


CODES = {
    "watch_ui": "FDA_WINDOW_HOLD",
    "radar_signal": "SIGNAL_TIME_HOLD",
    "xs_compile": "COMPILE_RAW_MISSING",
    "xs_backtest": "BACKTEST_SCOPE_HOLD",
    "at_simulated_order": "SIM_BROKER_TYPE_DENY",
    "broker_external_event_read": "BROKER_FACT_MISSING",
    "broker_live_submit": "FIN_ORDER_DENY_ALWAYS",
}

DETECTORS = {
    "watch_ui": d_watch_ui,
    "radar_signal": d_radar_signal,
    "xs_compile": d_xs_compile,
    "xs_backtest": d_xs_backtest,
    "at_simulated_order": d_at_simulated_order,
    "broker_external_event_read": d_broker_external_event_read,
    "broker_live_submit": d_broker_live_submit,
}

# ---------------------------------------------------------------- fixtures
_FDA = "/Fabric/FABRIC/fabric-desktop-automation"
_BLD = "9f1c2d0e"          # carrier build_ref placeholder: static fixture, not a runtime claim
_SHA = "a" * 64

POS = {
    "watch_ui": {"window_id": "WIN-1", "lease_ref": "WIN-1", "build_ref": _BLD, "sku": "XQ-8.0",
                 "observed_at": "2026-11-26T10:00:00+0800",
                 "valid_until": "2026-11-26T18:00:00+0800", "capture_sha": _SHA},
    "radar_signal": {"signal_id": "SIG-1", "signal_known_at": "2026-11-26T09:00:00+0800",
                     "decision_asof": "2026-11-26T10:00:00+0800", "source_sha": _SHA},
    "xs_compile": {"script_sha": _SHA, "diagnostics": [], "compiler_build": _BLD},
    "xs_backtest": {"pit_status": "PIT_OK", "rule_snapshot_ref": "RS-1", "rights_epoch": "R-1",
                    "period_start": "2026-01-01T00:00:00+0800",
                    "period_end": "2026-06-01T00:00:00+0800"},
    "at_simulated_order": {"sim_receipt_ref": "SIM-1", "fill_type": "SIM_FILL", "qty": 1,
                           "simulator_build": _BLD},
    "broker_external_event_read": {"broker_seq": 4231, "broker_receipt_ref": "BR-1",
                                   "book_of_record_version": "BoR-7", "provenance_sha": _SHA,
                                   "origin": "BROKER"},
    # POS for live_submit expresses an actual submit request: the invariant must deny it
    "broker_live_submit": {"action": "submit", "side": "BUY", "qty": 1, "connector": None,
                           "token": None},
}

MUTATION = {   # one field only, per the SPEC's mutation column
    "watch_ui": ("valid_until", "2026-11-26T09:00:00+0800"),          # 錯窗/過期
    "radar_signal": ("signal_known_at", "2026-11-26T11:00:00+0800"),  # 假即時
    "xs_compile": ("script_sha", ""),                                # 缺 compiler raw
    "xs_backtest": ("pit_status", "LOOKAHEAD"),                      # lookahead/無權
    "at_simulated_order": ("fill_type", "BROKER_FILL"),              # 模擬升真成交
    "broker_external_event_read": ("origin", "GUI_ACK"),             # GUI ACK 冒 Fill
    "broker_live_submit": ("action", "replace"),                     # §06 column: submit/replace/cancel
}


# a slot may have more than one arm named in the spec mutation column
EXTRA_MUTATIONS = {
    "xs_backtest": [("rights_epoch", "")],            # 無權 arm (lookahead is the other arm)
    "broker_external_event_read": [("broker_seq", None), ("broker_receipt_ref", None),
                                   ("book_of_record_version", None)],   # GUI ACK 冒 Fill
    "broker_live_submit": [("action", "cancel")],      # third arm of the same mutation column
}

# discrimination records: a detector that is constant on one field passes its POS and its NEG
# with the same expression. Each entry must be ADMITTED (None) where the slot has any read side.
DISCRIMINATION = {
    "broker_live_submit": {"action": "read", "window_id": "WIN-1", "observed_at":
                           "2026-11-26T10:00:00+0800"},
}

# POS expectation: every slot admits a clean record EXCEPT broker_live_submit, whose spec POS row
# demands the deny invariant itself.
POS_EXPECT = {s: None for s in DETECTORS}
POS_EXPECT["broker_live_submit"] = "FIN_ORDER_DENY_ALWAYS"


def run_slot(slot: str) -> dict:
    det = DETECTORS[slot]
    pos = copy.deepcopy(POS[slot])
    pos_res = det(pos)
    arms = []
    k, v = MUTATION[slot]
    for kk, vv in [(k, v)] + EXTRA_MUTATIONS.get(slot, []):
        neg = copy.deepcopy(POS[slot])
        neg[kk] = vv
        arms.append({"mutation": {kk: vv}, "first_fail": det(neg)})
    want = CODES[slot]
    disc = DISCRIMINATION.get(slot)
    disc_res = det(copy.deepcopy(disc)) if disc else None
    ok = (pos_res == POS_EXPECT[slot]) and all(a["first_fail"] == want for a in arms)
    if disc:
        ok = ok and disc_res is None
    return {"slot": slot, "pos_first_fail": pos_res, "pos_expected": POS_EXPECT[slot],
            "arms": arms, "neg_expected": want, "verdict": "PASS" if ok else "FAIL",
            "discrimination": ({"record": disc, "admitted_first_fail": disc_res}
                               if disc else None),
            "carrier": _FDA, "claim_ceiling": "STATIC_TYPED_CONTRACT_ONLY"}


if __name__ == "__main__":
    for s in DETECTORS:
        r = run_slot(s)
        arms = " ".join(f"{list(a['mutation'])[0]}={a['first_fail']}" for a in r["arms"])
        print(f"  {s:30s} pos={str(r['pos_first_fail']):22s} {arms:60s} {r['verdict']}")
