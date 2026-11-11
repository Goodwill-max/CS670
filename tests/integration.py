"""End-to-end tests against an independent plain-set oracle, never used by the protocol."""
import pathlib
import random
import sys
import tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from run_demo import run

binary = pathlib.Path(sys.argv[1]).resolve()
rng = random.Random(670)
cases = [(["a", "b"], ["c"]), (["a", "b"], ["a"]),
         (["a", "b"], ["b", "a"]), (["a", "a", "b"], ["a", "a"])]
for _ in range(8):
    cases.append(([f"contact-{i}" for i in rng.sample(range(500), 100)],
                  [f"contact-{i}" for i in rng.sample(range(500), 32)]))
with tempfile.TemporaryDirectory() as temp:
    server, client = pathlib.Path(temp)/"server.txt", pathlib.Path(temp)/"client.txt"
    for i, (a, b) in enumerate(cases):
        server.write_text("\n".join(a)+"\n", encoding="utf-8")
        client.write_text("\n".join(b)+"\n", encoding="utf-8")
        # Repeat identical inputs to exercise fresh masks and shuffled positions.
        for repeat in range(2):
            actual = run(binary, server, client, 22000 + 6*i + 3*repeat)
            expected = sorted(set(a) & set(b))
            assert actual == expected, (i, actual, expected)
        print(f"PASS case {i}: {len(set(a)&set(b))} matches", flush=True)
