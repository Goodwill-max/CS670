"""Run only the scenario with a new unregistered client contact. Optional: --compare."""
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([
        sys.executable, str(Path(__file__).with_name("present_demo.py")),
        "--scenario", "client-only", *sys.argv[1:]
    ]))
