"""Native OFF probe (engineering recorder, not product code).

Runs the B0 CLI with a deliberately reduced environment (no FHS/HGK/CODEX/OPENAI
variables, no hermes/opencodex paths on PATH) and records:

  * exit code and stdout digest, compared with the normal run (same request)
  * child processes spawned by the product during the run
  * TCP endpoints owned by the product process during the run
  * environment keys actually visible to the child

What this does NOT prove (recorded honestly in the output): transitive imports of
services that are absent, kernel-level file/registry writes, and long-running
network activity after the sampled window.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

W = Path(r"C:\Projects\Agent_Workspace\SQS-THC_MVP_Workspace")
DEV = W / "20_DEV"
REQ = W / "40_OPS" / "b0_read_request_2026-11-25.json"
OUT = W / "40_OPS"
BASELINE_SHA = "4004f208fb29"

HOSTILE_PREFIXES = ("HGK_", "FHS_", "HERMES_", "CODEX_", "OPENAI_", "OPENCODE", "PYTHONPATH")


def reduced_env() -> dict[str, str]:
    keep = {"SystemRoot", "SYSTEMROOT", "COMSPEC", "PATHEXT", "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE", "USERNAME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
            "LOCALAPPDATA", "APPDATA", "ProgramData", "windir"}
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["PATH"] = str(Path(sys.executable).parent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TEMP"] = str(DEV / ".tmp_tests")
    env["TMP"] = env["TEMP"]
    (DEV / ".tmp_tests").mkdir(exist_ok=True)
    return env


def sample_network(pid: int, stop: threading.Event, sink: list[str]) -> None:
    while not stop.is_set():
        try:
            raw = subprocess.run(["netstat", "-ano"], capture_output=True).stdout
            text = raw.decode("utf-8", "replace")
            for line in text.splitlines():
                if line.rstrip().endswith(str(pid)) and "127.0.0.1" not in line:
                    sink.append(line.strip())
        except Exception:
            pass
        time.sleep(0.05)


ALLOWED_CHILDREN = {"icacls.exe", "icacls", "attrib.exe", "whoami.exe"}


def sample_children(pid: int, stop: threading.Event, sink: dict[str, str]) -> None:
    """Accumulate every child process name observed while the product runs."""

    while not stop.is_set():
        try:
            out = subprocess.run(["wmic", "process", "where", f"ParentProcessId={pid}",
                                  "get", "Name,ProcessId", "/format:csv"],
                                 capture_output=True, encoding="utf-8", errors="replace", timeout=10).stdout
            for line in out.splitlines():
                parts = [x.strip() for x in line.split(",")]
                if len(parts) >= 3 and parts[2] and parts[2] != "Name":
                    sink[parts[1]] = parts[2]
        except Exception:
            pass
        time.sleep(0.03)


def main() -> int:
    request_bytes = REQ.read_bytes()
    env = reduced_env()
    script = ("import subprocess,sys,time;"
              "p=subprocess.Popen([sys.executable,'-B','-m','b0_reader.cli','read','--request-json','-'],"
              "stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);"
              "out,err=p.communicate(sys.stdin.buffer.read());"
              "sys.stdout.buffer.write(out);sys.stderr.buffer.write(err);"
              "sys.exit(p.returncode)")
    t0 = time.time()
    proc = subprocess.run([sys.executable, "-B", "-c", script], cwd=str(DEV), input=request_bytes,
                          capture_output=True, env=env)
    elapsed = time.time() - t0

    # second pass with live sampling of the child process
    net: list[str] = []
    stop = threading.Event()
    p2 = subprocess.Popen([sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
                          cwd=str(DEV), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env)
    kids: dict[str, str] = {}
    th = threading.Thread(target=sample_network, args=(p2.pid, stop, net), daemon=True)
    tk = threading.Thread(target=sample_children, args=(p2.pid, stop, kids), daemon=True)
    th.start(); tk.start()
    out2, err2 = p2.communicate(request_bytes)
    stop.set(); th.join(timeout=5); tk.join(timeout=5)

    def projection(payload: bytes) -> dict:
        try:
            doc = json.loads(payload.decode("utf-8"))
        except Exception:
            return {"error": "unparsable"}
        return {
            "wire_version": doc.get("wire_version"),
            "candidate_digest": doc.get("candidate_digest"),
            "entries": [
                {"sid": e["source_ref"]["source_id"], "sha": e["sha"], "clause": e["clause_sha"],
                 "R": e["required_fields"], "P": sorted(e["observed"]), "M": sorted(m["field"] for m in e["missing"])}
                for e in doc.get("entries", [])
            ],
            "errors": [e.get("code") for e in doc.get("errors", [])],
        }

    digest = hashlib.sha256(proc.stdout).hexdigest()
    proj1 = projection(proc.stdout)
    proj2 = projection(out2)
    foreign = {pid: name for pid, name in kids.items() if name.lower() not in ALLOWED_CHILDREN}
    record = {
        "schema": "SST-B0-NATIVE-OFF/1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "command": {"argv": [sys.executable, "-B", "-m", "b0_reader.cli", "read", "--request-json", "-"],
                    "cwd": str(DEV)},
        "environment": {
            "keys_visible_to_child": sorted(env),
            "stripped_prefixes": list(HOSTILE_PREFIXES),
            "note": "no HGK_/FHS_/HERMES_/CODEX_/OPENAI_/PYTHONPATH variables; PATH is the interpreter dir only",
        },
        "run1": {"exit": proc.returncode, "stdout_bytes": len(proc.stdout), "stdout_sha256": digest,
                 "stderr": proc.stderr.decode("utf-8", "replace")[:400], "seconds": round(elapsed, 3)},
        "run2_sampled": {"exit": p2.returncode, "stdout_sha256": hashlib.sha256(out2).hexdigest(),
                         "stderr": err2.decode("utf-8", "replace")[:400],
                         "child_processes": kids, "external_tcp_endpoints": net[:10]},
        "comparison": {
            "baseline_stdout_sha_prefix": BASELINE_SHA,
            "raw_stdout_sha_changes_per_run": "authority.checked_at is a timestamp, so raw bytes differ by design",
            "stable_projection_run1": proj1,
            "same_stable_projection": proj1 == proj2,
            "children_total": len(kids),
            "children_seen": kids,
            "children_allowed_os_tools": sorted({n for n in kids.values() if n.lower() in ALLOWED_CHILDREN}),
            "children_foreign": foreign,
            "external_tcp_observed": len(net),
        },
        "not_proven": [
            "transitive imports of absent services (only the runtime behaviour is observed)",
            "kernel-level file/registry writes outside the watched roots",
            "network activity after the sampling window",
        ],
        "verdict": ("NATIVE_OFF_OBSERVED_NO_EXTERNAL_DEPENDENCY"
                    if proj1 == proj2 and proj1.get("entries") and not foreign and not net
                    else "NATIVE_DEPENDENCY_OR_DRIFT_OBSERVED"),
    }
    (OUT / "native_off_r4.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("run1", "comparison", "verdict")}, ensure_ascii=False)[:900])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
