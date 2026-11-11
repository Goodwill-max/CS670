"""Presentation wrapper around the existing secure binaries; never simulates results."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

DEMO = Path(__file__).resolve().parent
ROOT = DEMO.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_demo import run as run_pir_psi


def contacts(path):
    # Match the C++ input rules: ignore empty lines, preserve identifier bytes,
    # remove duplicates. No phone-number normalization happens automatically.
    values = [s for s in path.read_text(encoding="utf-8").splitlines() if s]
    if not values:
        raise ValueError(f"At least one identifier is required in {path}")
    return sorted(set(values))


def baseline(binary, server, client, port):
    process = subprocess.Popen([str(binary), "psi-server", str(server), str(port)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        result = subprocess.run([str(binary), "psi-client", str(client), str(port)],
                                capture_output=True, text=True, timeout=90)
        _, error = process.communicate(timeout=90)
        if result.returncode or process.returncode:
            raise RuntimeError(result.stderr + "\n" + error)
        return result.stdout.splitlines()
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--walkthrough", action="store_true", help="Run three registration scenarios using generated copies")
    selection.add_argument("--scenario", choices=["current", "client-only", "registered"], help="Run exactly one scenario independently")
    parser.add_argument("--compare", action="store_true", help="Also execute the separate direct KKRT PSI binary")
    parser.add_argument("--pause", action="store_true", help="Wait for Enter between walkthrough scenarios")
    parser.add_argument("--port", type=int, default=30080)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65510:
        parser.error("base port must be between 1024 and 65510")
    binary = ROOT / "build/linux/contact_discovery"
    psi_binary = ROOT / "comparison/build/kkrt_psi"
    for executable in [binary] + ([psi_binary] if args.compare else []):
        if not executable.is_file():
            parser.error(f"Executable missing: {executable}. See demo/README.md for build commands.")
    config = json.loads((DEMO / "config.json").read_text(encoding="utf-8"))
    users, address_book = contacts(DEMO / "server.txt"), contacts(DEMO / "client.txt")
    scenarios = [("01-current-inputs", "Current editable inputs", users, address_book)]
    if args.walkthrough or args.scenario in ("client-only", "registered"):
        added = config["new_contact"]
        if not isinstance(added, str) or not added or "\n" in added or "\r" in added:
            raise ValueError("config.json new_contact must be a nonempty single-line identifier")
        if added in users or added in address_book:
            raise ValueError("For the walkthrough, choose a new_contact absent from both editable input files")
        scenarios += [
            ("02-client-only", "New contact added only to the client", users, address_book + [added]),
            ("03-registered", "New contact also registered on the server", users + [added], address_book + [added]),
        ]
    if args.scenario:
        selected_key = {"current": "01-current-inputs", "client-only": "02-client-only", "registered": "03-registered"}[args.scenario]
        scenarios = [scenario for scenario in scenarios if scenario[0] == selected_key]
    now = datetime.now(timezone.utc)
    output = DEMO / "output" / now.strftime("%Y%m%dT%H%M%S_%fZ")
    output.mkdir(parents=True, exist_ok=False)
    transcript = []
    records = []

    def show(message=""):
        print(message, flush=True)
        transcript.append(message)

    try:
        for index, (key, label, server_set, client_set) in enumerate(scenarios):
            scenario_number = int(key[:2])
            if index and args.pause:
                input("Press Enter for the next scenario...")
            case_dir = output / key
            case_dir.mkdir()
            server_file, client_file = case_dir / "server.txt", case_dir / "client.txt"
            server_set, client_set = sorted(set(server_set)), sorted(set(client_set))
            server_file.write_text("\n".join(server_set) + "\n", encoding="utf-8")
            client_file.write_text("\n".join(client_set) + "\n", encoding="utf-8")
            expected = sorted(set(server_set) & set(client_set))
            show("=" * 64)
            show(config["title"])
            show(f"SCENARIO {scenario_number}: {label}")
            show("=" * 64)
            show(f"Server registered identifiers ({len(server_set)}):")
            for contact in server_set:
                show("  " + contact)
            show(f"Client contact identifiers ({len(client_set)}):")
            for contact in client_set:
                show("  " + contact)
            show("Expected intersection: " + (", ".join(expected) or "(empty)"))
            show("Executing original PIR-PSI binary: client + two server processes...")
            actual = run_pir_psi(binary, server_file, client_file, args.port + (scenario_number - 1) * 10)
            show("Actual PIR-PSI output:  " + (", ".join(actual) or "(empty)"))
            if actual != expected:
                raise RuntimeError(f"PIR-PSI result mismatch: expected {expected}, received {actual}")
            record = dict(scenario=key, server=server_set, client=client_set,
                          expected=expected, pir_psi_output=actual, passed=True)
            if args.compare:
                direct = baseline(psi_binary, server_file, client_file, args.port + (scenario_number - 1) * 10 + 3)
                show("Actual direct KKRT:    " + (", ".join(direct) or "(empty)"))
                if direct != expected:
                    raise RuntimeError(f"KKRT result mismatch: expected {expected}, received {direct}")
                record["kkrt_output"] = direct
            show("PASS: actual output equals the independently computed intersection.")
            show("This verifies this result, not a proof of privacy.")
            show()
            records.append(record)
        show("Demo complete. Exact inputs and results saved to:")
        show(str(output))
        show("Your editable demo inputs and original project data were not changed.")
    finally:
        (output / "transcript.txt").write_text("\n".join(transcript) + "\n", encoding="utf-8")
        (output / "results.json").write_text(json.dumps(dict(
            started_utc=now.isoformat(), mode=args.scenario or ("walkthrough" if args.walkthrough else "current"),
            compared_kkrt=args.compare, cases=records,
            scope="Functional demonstration only. Semi-honest, non-colluding-server model; no transport security or audit claim."
        ), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"DEMO FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
