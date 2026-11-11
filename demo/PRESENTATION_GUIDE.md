# Demo presentation notes and screenshots

Allocate about three minutes. Prepare the binaries before presenting. Keep Docker
Desktop running and use the VS Code container terminal. Enlarge the terminal font
with Ctrl+plus if needed. Use the default short inputs so the output fits on screen.

## Screenshot 1: inputs (30 seconds)

Open `demo/server.txt` and `demo/client.txt` side by side. Say:

"The client has three contacts. Two are registered with the service. The third,
ending 099, is not registered. The desired output contains only 002 and 004."

"I control all roles for this local demonstration, so I can show both inputs.
In deployment, these inputs belong to different parties."

## Screenshot 2: secure execution (40 seconds)

Run from `/workspaces/CS670`:

```bash
python3 demo/present_demo.py
```

Capture the visible inputs, actual output, and PASS line. Say:

"This executes the existing C++ PIR-PSI program as a client and two server
processes. DPF query shares hide lookup positions from either non-colluding
server. Masked responses and KKRT PSI limit what the client learns."

"The harness computes the expected answer separately for verification. That
ordinary intersection is not used to produce the secure program's output."

## Screenshot 3: contact addition and registration (60 seconds)

Run:

```bash
python3 demo/present_demo.py --walkthrough --pause
```

After each screen, explain the result before pressing Enter:

1. Base inputs: 002 and 004 match.
2. Add 088 only to the client's generated copy: output stays 002 and 004.
3. Add 088 to the server's generated copy as well: output adds 088.

Capture the third scenario. Say:

"The newly added contact appears only once it is registered. Each stage performs
a fresh protocol execution. This is not an incremental-update implementation."

The walkthrough leaves `demo/client.txt`, `demo/server.txt`, and `data/` unchanged.

## Screenshot 4: same result with direct KKRT (optional, 20 seconds)

Run:

```bash
python3 demo/present_demo.py --compare
```

Capture the two actual-output lines and PASS. Say:

"Both protocols compute the same intersection. They differ in communication,
computation and trust assumptions. This screen compares correctness only."

## Screenshot 5: measured performance (30 seconds)

Open `comparison/results/COMPARISON.md`. Highlight the 10,000 / 32 rows. Say:

"The saved experiment uses five measured runs per method after one warmup.
Our PIR-PSI used 75.9% less client traffic but took 54.7% longer in this case.
This demonstrates a communication-runtime tradeoff, not a security ranking."

Use the existing benchmark results instead of launching a full benchmark on stage.
The demo script does not overwrite the comparative measurements.

## Closing statement (20 seconds)

"Our intended privacy model is semi-honest parties with non-colluding PIR servers.
All processes run on one computer for this demonstration. The successful output
demonstrates tested correctness. It is not a proof of privacy or production security."

## Optional backup evidence

```bash
ctest --test-dir build/linux --output-on-failure
```

Capture successful primitive and protocol tests before the presentation if desired.
Every demo run also saves a transcript and JSON results under `demo/output/`.
Keep the timestamp visible if you present a saved transcript as recorded evidence.
