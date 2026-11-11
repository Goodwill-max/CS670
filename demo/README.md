# Editable presentation demo

This folder is separate from the PIR-PSI implementation and comparison project.
The runner calls the existing compiled programs. It never replaces the secure
protocol with a plain set intersection: plain intersection is only the independent
oracle used to check the actual program's output.

## Files you can change

- `server.txt`: synthetic registered users, one identifier per line.
- `client.txt`: synthetic client contacts, one identifier per line.
- `config.json`: presentation title and the new contact used in the walkthrough.
- `PRESENTATION_GUIDE.md`: what to say and which screens to capture.

Use synthetic numbers for screenshots. Identifiers must match exactly. The
program does not normalize phone numbers. Empty sets are not supported. Duplicate
lines are removed. The default walkthrough contact must be absent from both
files. The walkthrough creates copies and does not edit these files.

## Run inside the VS Code development container

### Run one scenario at a time

From `/workspaces/CS670`, run any of these independently, in any order:

```bash
python3 demo/01_current_inputs.py
python3 demo/02_client_only.py
python3 demo/03_registered.py
```

With the supplied inputs, the first two return 002 and 004. The third returns
002, 004 and 088. Scenario 3 does not require first running scenarios 1 or 2.
Each constructs its own input copies from the editable demo files and config,
executes the real PIR-PSI binary, and saves its own transcript and results.
Add `--compare` to any command to also run direct KKRT PSI. No compilation is needed.

### Run the complete walkthrough

```bash
cd /workspaces/CS670
python3 demo/present_demo.py
```

This executes your edited inputs and displays expected versus actual matches.

For the three-step walkthrough (base inputs, client-only addition, registration):

```bash
python3 demo/present_demo.py --walkthrough --pause
```

For screenshots or rehearsal without pauses, including the independent KKRT baseline:

```bash
python3 demo/present_demo.py --walkthrough --compare
```

You can combine `--walkthrough --compare --pause` for a live presentation.
`--compare` uses the separate direct KKRT binary. It compares output correctness,
not performance. Use the saved five-run benchmark table for performance claims.

Every run creates a unique `demo/output/<UTC timestamp>/` directory containing
`transcript.txt`, `results.json`, and exact input copies for each scenario.
If a result does not match the oracle, the runner exits with an error. Incomplete
scenarios never receive a PASS record.

## If a binary is missing

From `/workspaces/CS670` in the container:

```bash
cmake --build build/linux --target contact_discovery --parallel 2
```

For optional `--compare` support:

```bash
cmake -S comparison -B comparison/build -DCMAKE_BUILD_TYPE=Release
cmake --build comparison/build --target kkrt_psi --parallel 2
```

If another demo is running, close it or choose another port:

```bash
python3 demo/present_demo.py --walkthrough --port 31080
```

The presentation harness knows both synthetic inputs so it can show and check
them. This is not a view available to an individual protocol party in deployment.
Output correctness does not establish transcript privacy, non-collusion, resistance
to malicious messages, or production deployment security.
