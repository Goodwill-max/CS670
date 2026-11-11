"""Launch isolated loopback processes; stdout contains only the client's matches."""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(binary, server, client, port=18080, timeout=90):
    processes = []
    try:
        for role in ("server0", "server1"):
            processes.append(subprocess.Popen(
                [str(binary), role, str(server), str(port)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        result = subprocess.run([str(binary), "client", str(client), str(port)],
                                capture_output=True, text=True, timeout=timeout)
        outputs = [p.communicate(timeout=timeout) for p in processes]
        if result.returncode or any(p.returncode for p in processes):
            raise RuntimeError(result.stderr + "\n" + "\n".join(err for _, err in outputs))
        return result.stdout.splitlines()
    finally:
        for p in processes:
            if p.poll() is None:
                p.kill()
            p.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=pathlib.Path, default=ROOT / "build/linux/contact_discovery")
    parser.add_argument("--server", type=pathlib.Path, default=ROOT / "data/server.txt")
    parser.add_argument("--client", type=pathlib.Path, default=ROOT / "data/client.txt")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    if not args.binary.is_file():
        parser.error("Executable missing. Run the Configure and Build tasks first (see README.md).")
    for item in run(args.binary.resolve(), args.server, args.client, args.port):
        print(item)


if __name__ == "__main__":
    main()

