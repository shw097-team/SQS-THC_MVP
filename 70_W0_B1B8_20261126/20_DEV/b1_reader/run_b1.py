#!/usr/bin/env python3
"""B1 OPS runner: parse the B1 SPEC, run the four B1 ops against the authorized
RepoRoot, record argv/cwd/exit/no-write proof, write the receipt.

Effects: SOURCE_READ on the SPEC + repo; writes only this run's evidence files under
the wave root (engineering recorder, separately authorized from the product READ).
"""
from __future__ import annotations
import datetime, hashlib, json, os, re, subprocess, sys

WAVE = r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace\70_W0_B1B8_20261126"
DEV = os.path.join(WAVE, "20_DEV")
OPS = os.path.join(WAVE, "40_OPS")
sys.path.insert(0, os.path.join(DEV, "b1_reader"))
import b1_reader2 as b1_reader  # noqa: E402  (v2: disk-aware + FDA carrier inventory)

KBASE = r"C:\Projects\Agent_Workspace\知識庫\SQS\【1】SST_PLP_PH01-04\SST_PLP_PH01_W0_B0-B8"
REPO = r"C:\Projects\Agent_Workspace\SQS-THC"
FDA_CARRIERS = [os.path.join(r"C:\Projects\Agent_Workspace\FHS\Fabric",
                             "FABRIC", "fabric-desktop-automation"),
                os.path.join(r"C:\Projects\Agent_Workspace\FHS\Fabric",
                             "Fabric-rebind-publish", "FABRIC", "fabric-desktop-automation")]
FDA_SLOTS = ["watch_ui", "radar_signal", "xs_compile", "xs_backtest",
             "at_simulated_order", "broker_external_event_read", "broker_live_submit"]

# canonical 20 consumer edges (W0M §04 / B6 §04.EX — same EdgeID set)
EDGES = ["EXIT.startup.CORE", "EXIT.startup.POLICY", "EXIT.build.REPO", "EXIT.CI.TEST",
         "EXIT.profile.sqs-orchestrator", "EXIT.profile.sqs-data-analysis", "EXIT.profile.sqs-risk",
         "EXIT.runtime.DISPATCH", "EXIT.runtime.STOP"] + \
        [f"EXIT.GENIE.SW-{i:02d}" for i in range(1, 9)] + \
        ["EXIT.DEV-admission.POLICY", "EXIT.DEV-admission.REPO", "EXIT.DEV-admission.PIPD"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def find_spec() -> str:
    """Locate the B1 substantive SPEC by content identity, not by directory depth.

    The upstream library was reorganised (the batch SPECs now sit under
    SST_PLP_PH01_W0_B1-B8_執行控制小包/); the file identity is unchanged
    (sha256 13294cad…4a3753), so the search is recursive and must resolve to exactly one file.
    """
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


def parse_units(spec_path: str):
    t = open(spec_path, encoding="utf-8").read()

    def blk(pos):
        i = t.find("```json", pos)
        j = t.find("```", i + 7)
        return t[i + 7:j]

    common = json.loads(blk(t.find("COMMON_BY_KIND_BEGIN")))
    units, pins_bad = [], []
    for m in re.finditer(r"<!--\s*UNIT_BEGIN\s+(\S+)\s*-->", t):
        u = json.loads(blk(m.end()))
        calc = hashlib.sha256(json.dumps(u.get("source_payload"), ensure_ascii=False,
                                         separators=(",", ":")).encode()).hexdigest()
        if calc != u.get("payload_sha"):
            pins_bad.append(u["unit_id"])
        u["_common"] = common.get(u.get("kind"), {})
        units.append(u)
    return units, pins_bad


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, timeout=180)
    return p.returncode, p.stdout, p.stderr


def snapshot(repo):
    rc, out, _ = git(repo, "rev-parse", "--verify", "HEAD")
    head = out.decode().strip() if rc == 0 else None
    rc2, out2, _ = git(repo, "status", "--porcelain=v1")
    st = out2 if rc2 == 0 else b""
    return {"head": head, "status_sha256": sha(st), "status_entries": len(
        [l for l in st.decode("utf-8", "replace").splitlines() if l.strip()])}


def main() -> int:
    os.makedirs(OPS, exist_ok=True)
    spec = find_spec()
    spec_bytes = open(spec, "rb").read()
    units, pins_bad = parse_units(spec)
    print(f"SPEC {os.path.basename(spec)}  {len(spec_bytes)}B  sha256={sha(spec_bytes)}")
    print(f"units={len(units)}  payload_pin_failures={pins_bad or 'NONE'}")

    pre = snapshot(REPO)
    res = b1_reader.run(REPO, units, FDA_CARRIERS, EDGES, FDA_SLOTS)
    post = snapshot(REPO)

    no_write = {"before": pre, "after": post,
                "unchanged": pre == post,
                "verdict": "NO_PRODUCT_WRITE_OBSERVED" if pre == post else "WRITE_OBSERVED",
                "method": "git rev-parse HEAD + sha256(git status --porcelain=v1) before/after"}
    res["ops"]["no_write"] = no_write
    res["spec"] = {"path": spec, "bytes": len(spec_bytes), "sha256": sha(spec_bytes),
                   "units": len(units), "payload_pin_failures": pins_bad}

    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    out = os.path.join(OPS, f"b1_run_{stamp}.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1); f.write("\n")

    repo = res["repo"]
    print(f"\nrepo {repo['root']}")
    print(f"  HEAD {repo['commit']}  tree {repo['tree']}  branch {repo['branch']}")
    print(f"  dirty={repo['dirty']} entries={repo['status_entries']}  remotes={repo['remotes']}  "
          f"remote_head={repo['remote_head']} ({repo['remote_state']})")
    print(f"  tree entries tracked at HEAD: {res['tree_entries']}")
    print(f"  no-write: {no_write['verdict']} (before==after: {no_write['unchanged']})")

    for op, label in (("B1.BASE", "BASE+KERNEL"), ("B1.FDA", "FDA")):
        rows = res["ops"][op]["rows"]
        agg = {}
        for r in rows:
            agg[r["verdict"]] = agg.get(r["verdict"], 0) + 1
        print(f"\n{label}: {len(rows)} units  {agg}")
        for r in rows:
            print(f"  {r['unit_id']} {r['key']:30s} {r['verdict']}")
    print(f"\nB1.ROOTS: {len(res['ops']['B1.ROOTS']['rows'])} edges, all {res['ops']['B1.ROOTS']['rows'][0]['physical_status']}")
    print(f"\nreceipt: {out}  {os.path.getsize(out)}B  sha256={sha(open(out,'rb').read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
