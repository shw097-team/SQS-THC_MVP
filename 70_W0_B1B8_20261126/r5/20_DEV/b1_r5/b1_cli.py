#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B1 product entry point.

One strict UTF-8 JSON object on stdout, no BOM, no surrounding prose.
exit 0  : all requested keys resolved, no missing, no errors
exit 2  : legitimate entries but some missing / source-level refusals (per-key split)
exit 64 : invocation / trusted-context problem, refused before reading content
exit 70 : unclassified internal state

--out is accepted only as an engineering recorder path under the W tree; it never
turns a READ into a product write (product write_set stays []).
"""
from __future__ import annotations

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1_engine as E
import b1_spec

W_ROOT = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace"


def parse_args(argv):
    opts = {"op": None, "repo": None, "commit": None, "out": None, "units": "spec", "keys": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--op", "--repo", "--commit", "--out", "--keys", "--context", "--trusted-context"):
            if i + 1 >= len(argv):
                raise E.EngineFault("BAD_INVOCATION", a, "missing value", exit_code=64)
            opts[a[2:]] = argv[i + 1]
            i += 2
        elif a == "--units":
            opts["units"] = argv[i + 1] if i + 1 < len(argv) else "spec"
            i += 2
        else:
            raise E.EngineFault("BAD_INVOCATION", a, "unknown argument", exit_code=64)
    if not opts["op"]:
        raise E.EngineFault("BAD_INVOCATION", "--op", "op is required", exit_code=64)
    if not opts["repo"]:
        opts["repo"] = E.REPO_ROOT_ALLOWED[0]
    return opts


def main() -> int:
    argv = sys.argv[1:]
    try:
        opts = parse_args(argv)
        op = opts["op"].upper()
        spec = b1_spec.load_b1()
        units = list(spec["units"].values())
        if opts["keys"]:
            want = {k.strip() for k in opts["keys"].split(",") if k.strip()}
            units = [u for u in units if u["key"] in want]
            if not units:
                raise E.EngineFault("EMPTY_REQUEST", "EMPTY_UNIT_SELECTION",
                                    "a requested key set that matches nothing is refused, "
                                    "not reported as a vacuous success", exit_code=64)
        body = E.run(op, opts["repo"], units=units, commit=opts["commit"], argv=argv)
        body["spec_inputs"] = {"b1_spec_sha256": spec["sha256"],
                               "b1_unit_count": len(units),
                               "b1_unit_id_set_sha": spec["unit_id_set_sha"]}
        missing = 0
        errors = 0
        if "base" in body:
            missing = sum(len(e["missing"]) for e in body["base"]["entries"])
            errors = len(body["base"]["errors"])
        if "fda" in body:
            # a slot-level D-3 gap is a real missing obligation; the by-design absence of an
            # allowed-effect POS for live submit is not counted as a defect
            fda_missing = [m for slot in body["fda"]["slots"] for m in slot["missing"]
                           if not (m.get("field") == "allowed_effect_pos" and m.get("reason") == "ABSENT")]
            missing += len(fda_missing)
        body["invocation"] = {"op": op, "repo": opts["repo"], "commit": opts["commit"],
                              "units_source": "pinned_r5_spec", "out": opts["out"]}
        body["disposition"] = ("COMPLETE_NO_MISSING" if missing == 0 and errors == 0
                               else "PARTIAL_SPLIT_PER_KEY")
        payload = json.dumps(body, ensure_ascii=False, sort_keys=False, indent=1)
        if opts["out"]:
            out = os.path.abspath(opts["out"])
            if not os.path.normcase(out).startswith(os.path.normcase(W_ROOT) + os.sep):
                raise E.EngineFault("OUT_PATH_NOT_UNDER_W", out,
                                    "engineering recorder may only write inside W", exit_code=64)
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(payload)
            sys.stderr.write(f"recorder_out={out}\n")
        sys.stdout.write(payload)
        sys.stdout.flush()
        return 0 if missing == 0 and errors == 0 else 2
    except E.EngineFault as f:
        sys.stdout.write("{}")
        sys.stdout.flush()
        sys.stderr.write(json.dumps({"code": f.code, "first_fail": f.first_fail,
                                     "detail": f.detail}, ensure_ascii=False) + "\n")
        return f.exit_code
    except Exception:
        sys.stdout.write("{}")
        sys.stdout.flush()
        sys.stderr.write("UNCLASSIFIED_INTERNAL_STATE\n" + traceback.format_exc(limit=3))
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
