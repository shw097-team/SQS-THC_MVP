#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 META — official metadata retrieval for the 18 HARD keys, without installing anything.

Rules applied:
  * a licence may only be attributed to a *version*; if the pin is UNBOUND the metadata stays
    HOLD, because "the tool's name" is not a licence and the latest release is not the pin;
  * only official registries are read (PyPI JSON API for Python distributions);
  * every fetched document is pinned by URL + retrieval time + response SHA256, and the
    parsed fields are quoted, not paraphrased;
  * nothing is installed, selected or enabled here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import w0_spec

OPS = os.path.join(r"<LOCAL_ROOT>",
                   "71_W0_B0-B3_R7_20261127", "40_OPS")

# tool key -> (kind, package/distribution, pin source)
PACKAGES = {
    "TECH-02": ("package", "pydantic"),
    "TECH-03": ("package", "jsonschema"),
    "TECH-04": ("package", "pytest"),
    "TECH-05": ("package", "hypothesis"),
    "TECH-08": ("package-or-format", "pyarrow"),
    "TECH-09": ("package", "duckdb"),
    "TECH-14": ("package", "mlflow"),
    "TECH-15": ("package", "pyqlib"),
    "TECH-19": ("package", "opentelemetry-sdk"),
}
NOT_PACKAGES = {
    "TECH-01": "programming language runtime (Python); its licence is the PSF licence, not a "
               "distribution licence, and the admissible version is set by the product pin",
    "TECH-24": "hosted service (GitHub Actions)",
    "TECH-25": "repository feature (CODEOWNERS), not a distribution",
    "TECH-26": "artefact class (SBOM), not a distribution",
    "TECH-27": "hosted feature (Artifact Attestations)",
    "TECH-28": "framework (SLSA), not a distribution",
    "TECH-29": "project (Sigstore); the installable parts are separate distributions",
    "TECH-30": "organisation (OpenSSF), not a distribution",
    "TECH-42": "vendor product (XQ/XS); no official public metadata right in this run",
}


def fetch_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sst-w0-b2-meta/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return {"url": url, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "json": json.loads(raw.decode("utf-8"))}


def main() -> int:
    spec = w0_spec.load("B2")
    hard = [u for u in w0_spec.units(spec["text"]) if u.get("kind") == "HARD"]
    out = []
    for u in hard:
        tid = re.findall(r"(TECH-\d+)", u["key"])[-1]   # the key may also carry an ECP_TECH<n> prefix
        pin = None
        m = re.search(r"pin=([^；]+)", u["input_rule"])
        if m:
            pin = m.group(1).strip()
        rec = {"unit_id": u["unit_id"], "key": u["key"], "tool_id": tid,
               "pin_text": pin, "metadata": None, "decision": None, "missing": []}
        out.append(rec)
        kind_pkg = PACKAGES.get(tid)
        if tid in NOT_PACKAGES:
            rec["decision"] = "NOT_A_DISTRIBUTION"
            rec["missing"] = [{"field": "metadata", "reason": "FORMAT_UNSUPPORTED",
                               "detail": NOT_PACKAGES[tid]}]
            continue
        if not kind_pkg:
            rec["decision"] = "UNCLASSIFIED_TOOL"
            rec["missing"] = [{"field": "metadata", "reason": "UNVERIFIED",
                               "detail": "no official registry mapping known for this key"}]
            continue
        _kind, dist = kind_pkg
        ver = None
        if pin:
            mv = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", pin)
            if mv and "UNBOUND" not in pin.upper():
                ver = mv.group(1)
        if not ver:
            rec["decision"] = "VERSION_UNBOUND"
            rec["missing"] = [{"field": "metadata", "reason": "UNVERIFIED",
                               "detail": f"the pin for {dist!r} is not a version ({pin!r}); a "
                                         f"licence may not be attributed to an unpinned tool, and "
                                         f"the latest release is not the pin"}]
            continue
        url = f"https://pypi.org/pypi/{dist}/{ver}/json"
        try:
            doc = fetch_json(url)
        except Exception as ex:                                   # noqa: BLE001
            rec["decision"] = "FETCH_FAILED"
            rec["missing"] = [{"field": "metadata", "reason": "UNVERIFIED",
                               "detail": f"{url} -> {type(ex).__name__}: {ex}"}]
            continue
        info = doc["json"]["info"]
        rec["metadata"] = {
            "distribution": dist, "version": info.get("version"),
            "license": info.get("license") or None,
            "license_expression": info.get("license_expression") or None,
            "requires_python": info.get("requires_python"),
            "summary": (info.get("summary") or "")[:120],
            "provenance": {"url": doc["url"], "retrieved_at": doc["retrieved_at"],
                           "response_sha256": doc["sha256"], "response_bytes": doc["bytes"]},
        }
        lic = rec["metadata"]["license_expression"] or rec["metadata"]["license"]
        if lic:
            rec["decision"] = "COLLECTED"
        else:
            rec["decision"] = "LICENCE_FIELD_EMPTY"
            rec["missing"] = [{"field": "license", "reason": "ABSENT",
                               "detail": "the official metadata carries no licence field for this "
                                         "release"}]
    counts = {}
    for r in out:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1
    result = {"schema": "SST.PH01.W0.B2.META@2",
              "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "registry": "pypi.org JSON API (official)",
              "installed_anything": False, "selected_anything": False,
              "counts": counts, "entries": out,
              "claim_ceiling": "metadata collected for real bytes only where a version pin "
                               "exists; nothing installed, nothing selected"}
    p = os.path.join(OPS, "b2_r7_meta.json")
    json.dump(result, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps({"written": p, "counts": counts}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
