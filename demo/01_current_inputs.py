"""Run only the initial contact-discovery scenario. Optional: --compare."""
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([
        sys.executable, str(Path(__file__).with_name("present_demo.py")),
        "--scenario", "current", *sys.argv[1:]
    ]))
