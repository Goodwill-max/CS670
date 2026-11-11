"""Measured direct KKRT PSI versus the unoptimized two-server PIR-PSI driver."""
import argparse
import csv
import json
import os
import pathlib
import platform
import statistics
import subprocess
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def trial(binary, protocol, server, client, port):
    env = dict(os.environ, PIR_PSI_METRICS="1")
    processes = []
    started = time.perf_counter()
    try:
        roles = ["server0", "server1"] if protocol == "pir-psi" else ["psi-server"]
        for role in roles:
            processes.append(subprocess.Popen([str(binary), role, str(server), str(port)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env))
        role = "client" if protocol == "pir-psi" else "psi-client"
        result = subprocess.run([str(binary), role, str(client), str(port)],
                                capture_output=True, text=True, env=env, timeout=120)
        logs = [result.stderr]
        for p in processes:
            _, err = p.communicate(timeout=120)
            logs.append(err)
        elapsed = (time.perf_counter() - started) * 1000
        if result.returncode or any(p.returncode for p in processes):
            raise RuntimeError("\n".join(logs))
        metrics = [json.loads(line[len("METRICS "):]) for log in logs
                   for line in log.splitlines() if line.startswith("METRICS ")]
        by_role = {m["role"]: m for m in metrics}
        if set(by_role) != set(roles + [role]):
            raise RuntimeError("Missing role metrics; rebuild the executable before benchmarking")
        c = by_role[role]
        client_bytes = c["sent"] + c["received"] + c["extra_sent"] + c["extra_received"]
        if client_bytes <= 0:
            raise RuntimeError("Invalid client communication counters")
        interserver_bytes = 0
        if protocol == "pir-psi":
            s = by_role["server0"]
            interserver_bytes = s["extra_sent"] + s["extra_received"]
            peer = by_role["server1"]
            if s["extra_sent"] != peer["extra_received"] or s["extra_received"] != peer["extra_sent"]:
                raise RuntimeError("Interserver communication counters disagree")
        return result.stdout.splitlines(), elapsed, client_bytes, interserver_bytes
    finally:
        for p in processes:
            if p.poll() is None:
                p.kill()
            p.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=pathlib.Path, default=ROOT / "build/pir_psi_measured")
    parser.add_argument("--psi-binary", type=pathlib.Path, default=ROOT / "build/kkrt_psi")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "results")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    cases = [("uploaded-demo", None, None), ("balanced", 128, 128),
             ("small", 100, 32), ("unequal-1k", 1000, 32),
             ("unequal-10k", 10000, 32), ("more-contacts", 10000, 128)]
    with tempfile.TemporaryDirectory() as temp:
        for case_idx, (label, size, contacts) in enumerate(cases):
            if size is None:
                a = (ROOT.parent / "data/server.txt").read_text().splitlines()
                b = (ROOT.parent / "data/client.txt").read_text().splitlines()
            else:
                a = [f"registered-{i:08d}" for i in range(size)]
                matches = min(size, max(1, contacts // 4))
                b = a[:matches] + [f"absent-{i:08d}" for i in range(contacts - matches)]
            expected = sorted(set(a) & set(b))
            server, client = pathlib.Path(temp)/"server.txt", pathlib.Path(temp)/"client.txt"
            server.write_text("\n".join(a)+"\n")
            client.write_text("\n".join(b)+"\n")
            # One excluded warmup per protocol, then alternating trial order.
            for repeat in range(-1, args.repeats):
                order = ["kkrt-psi", "pir-psi"] if repeat % 2 == 0 else ["pir-psi", "kkrt-psi"]
                for protocol in order:
                    actual, ms, client_bytes, interserver = trial(
                        (args.binary if protocol == "pir-psi" else args.psi_binary).resolve(), protocol, server, client, 26000 + case_idx*12 + order.index(protocol)*3)
                    assert actual == expected, (label, protocol, actual, expected)
                    if repeat >= 0:
                        rows.append(dict(case=label, server_size=len(set(a)), client_size=len(set(b)),
                                         matches=len(expected), protocol=protocol, repeat=repeat,
                                         wall_ms=ms, client_bytes=client_bytes,
                                         interserver_bytes=interserver, total_bytes=client_bytes+interserver))
            print(f"PASS {label}: N={len(set(a))}, n={len(set(b))}", flush=True)
    with (args.output/"benchmark_raw.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary = []
    for label, _, _ in cases:
        for protocol in ["kkrt-psi", "pir-psi"]:
            group = [r for r in rows if r["case"] == label and r["protocol"] == protocol]
            r = dict(group[0]);r.pop("repeat")
            for key in ["wall_ms", "client_bytes", "interserver_bytes", "total_bytes"]:
                r[key] = statistics.median(x[key] for x in group)
            r.update(min_ms=min(x["wall_ms"] for x in group),max_ms=max(x["wall_ms"] for x in group))
            summary.append(r)
    with (args.output/"benchmark_summary.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    metadata = dict(platform=platform.platform(), python=platform.python_version(),
                    cpu_count=os.cpu_count(), repeats=args.repeats, warmups=1,
                    cpu=pathlib.Path("/proc/cpuinfo").read_text().split("model name",1)[-1].splitlines()[0],
                    utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()))
    (args.output/"environment.json").write_text(json.dumps(metadata,indent=2))
    report = ["# Measured KKRT PSI versus PIR-PSI", "",
              "Median of five measured fresh-process runs after one excluded warmup per case/protocol.",
              "All outputs checked against an independent set-intersection oracle. Same input files, encoder,",
              "128-bit cryptographic backend and statistical security parameter 40. Loopback networking;",
              "all parties share one Docker host. Alternate protocol order between repetitions.", "",
              "Wall time includes process startup, input loading/hashing, table construction, fresh base OTs,",
              "protocol execution and process shutdown. It is not an online-only or CPU-time measurement.",
              "Client bytes count both directions on all client links; total adds the interserver link once.",
              "Bytes use cryptoTools channel counters, excluding TCP/IP/Ethernet and connection-handshake overhead.", "",
              "| Case | Server N | Client n | Method | Median ms | Min–max ms | Client KiB | All-links KiB |",
              "|---|---:|---:|---|---:|---:|---:|---:|"]
    report[2] = f"Median of {args.repeats} measured fresh-process runs after one excluded warmup per case/protocol."
    for r in summary:
        report.append(f'| {r["case"]} | {r["server_size"]} | {r["client_size"]} | {r["protocol"]} | {r["wall_ms"]:.2f} | {r["min_ms"]:.2f}–{r["max_ms"]:.2f} | {r["client_bytes"]/1024:.2f} | {r["total_bytes"]/1024:.2f} |')
    report += ["", "The direct baseline is specifically KKRT PSI, not all PSI schemes.",
               "PIR-PSI is the current unbinned implementation; these results do not evaluate the paper's optimized prototype.",
               "The baseline has one server; PIR-PSI has two non-colluding servers. This is a different trust/deployment model.",
               "No database preprocessing or base OTs are amortized. Small-case wall times can be dominated by startup and scheduling.",
               "No memory usage, WAN latency, multi-client throughput, or security-audit conclusion is claimed.",
               "See benchmark_raw.csv, benchmark_summary.csv and environment.json for measurements and environment."]
    (args.output/"COMPARISON.md").write_text("\n".join(report)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
