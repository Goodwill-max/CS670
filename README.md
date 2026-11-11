# PIR-PSI private contact discovery

This CS670 project implements private contact discovery in C++. A client
finds which of its contact identifiers appear in a registered-user set held
by two servers. The application builds a cuckoo table, queries candidate
locations using private information retrieval (PIR), and compares masked
values using private set intersection (PSI).

`src/main.cpp` implements the client and both server roles. The demo scripts
launch those roles on synthetic inputs and check the returned matches. The
separate `comparison/` project measures runtime and communication against
direct KKRT PSI.

The cryptographic backend uses [libPSI](https://github.com/osu-crypto/libPSI)
and libOTe. See [DEPENDENCIES.md](DEPENDENCIES.md) for versions and build details.

## Open and run in VS Code on Windows

Prerequisites: Docker Desktop with Linux containers, VS Code, and its Dev
Containers extension. This is a Linux x86-64 C++ build; installing VS Code alone
does not install the compiler or the cryptographic dependencies. AES/SSE CPU
instructions must be available to the container.

1. Open this **CS670** folder in VS Code.
2. Run **Dev Containers: Reopen in Container** from the command palette.
3. Open a terminal in that container and run:

```sh
cmake -S . -B build/linux -DCMAKE_BUILD_TYPE=Release
cmake --build build/linux --target contact_discovery --parallel 2
python3 scripts/run_demo.py
ctest --test-dir build/linux --output-on-failure
```

The first configure downloads/builds libOTe, cryptoTools, RELIC, and sparsehash
through upstream's dependency scripts; internet access is required. Allow several
minutes. The included VS Code tasks run the same commands.
Generated dependencies and Linux build files use Docker named volumes to avoid
slow extraction of Boost's many small files through the Windows shared folder.
Source files remain in the Windows workspace. After changing container settings,
run **Dev Containers: Rebuild Container** once to apply the volume mounts.

Expected demo output (synthetic contacts):

```text
+919000000002
+919000000004
```

Replace `data/server.txt` and `data/client.txt`, or run:

```sh
python3 scripts/run_demo.py --server path/to/users.txt --client path/to/contacts.txt
```

Inputs are UTF-8, one identifier per line. Empty lines are ignored and duplicates
are removed. Matching uses exact bytes; normalize phone numbers to the same format
before running. Empty sets are rejected. Only the client prints matches.

To launch the three roles manually, use three container terminals:

```sh
./build/linux/contact_discovery server0 data/server.txt
./build/linux/contact_discovery server1 data/server.txt
./build/linux/contact_discovery client data/client.txt
```

Ports 18080-18082 are loopback-only. A fourth argument overrides the base port;
all three roles must use the same value. The Python launcher kills child servers
on timeout or error. Do not run two instances on the same ports simultaneously.

## Demo scenarios and comparison

After building the original application, run these commands from the CS670
root inside the development container:

```bash
python3 demo/01_current_inputs.py
python3 demo/02_client_only.py
python3 demo/03_registered.py
```

The supplied inputs yield matches ending in 002 and 004 in the first two
scenarios. The third adds 088 to the matching set. Each scenario executes
PIR-PSI independently and checks the result against the expected intersection.
See [demo instructions](demo/README.md) for editable inputs and
[comparison instructions](comparison/README.md) for building the direct KKRT
baseline, using `--compare`, and running the benchmark.

## Protocol and source map

| Component | Implementation |
| --- | --- |
| 128-bit item encoding | domain-separated RandomOracle digest in `encode` |
| Three-choice cuckoo table | `cuckoo` uses augmenting paths and a fresh public salt to build identical replicas |
| BGI distributed point function | `BgiPirClient::keyGen` and `BgiPirServer::fullDomain` generate and evaluate query shares |
| Designated-output PIR | Server 1 sends its masked response directly to Server 0 |
| Hide cuckoo location | Server 1 shuffles three fresh masks per contact |
| Secure PSI | `KkrtPsiSender` and `KkrtPsiReceiver` run KKRT with OT extension and base OTs |
| Client output | matched masked-input indices map to original contacts; deduplicate |

Each query produces shares `v0 XOR v1 = CT[h_j(x)]`. Server1 sends
`v1 XOR r_sigma(j)` to server0, which forms `CT[h_j(x)] XOR r_sigma(j)`.
The client inputs all three `x XOR r_j` values into KKRT PSI with server0.
The secret permutation prevents a successful match from identifying the occupied
cuckoo location. The client never receives an unmasked database value or the
servers' PIR shares. Masks, DPF seeds, OT seeds, and secret permutations use fresh
OS-seeded PRNGs on every invocation.

## Scope and security assumptions

The intended model assumes semi-honest parties and two non-colluding servers.
Each server holds the complete database, and contact and database sizes are
public. Colluding servers can reconstruct query locations. A deployment would
need an authorization policy to limit repeated queries for guessed numbers.

The application uses an unbinned lookup for each candidate location. The
cuckoo table has a power-of-two size with at least twice as many slots as
registered identifiers. Construction aborts if an item cannot be placed.
Each server scans its table for every PIR query, so query work grows with
the product of client and database sizes.

The driver binds to localhost and supplies no transport authentication/TLS or
malicious-message hardening. It must not be exposed to the internet. No claim of
malicious security is made. Output correctness tests cannot prove privacy.

## Validation status

The repository includes 24 end-to-end runs covering disjoint sets, one match,
full overlap, duplicates, and random partial overlaps, each checked against an
independent set intersection. These must pass before treating a build as working.
The `primitives` CTest also checks BGI point-function outputs at every position,
PIR reconstruction at boundary indices across three table sizes, and cuckoo
placement. No correctness failures are suppressed.
Validated on 2026-11-06 in the Ubuntu 22.04 VS Code development container:
CMake configuration and the C++ application build succeeded; both CTest suites
passed (24 end-to-end protocol runs plus the primitive checks). The sample
`python3 scripts/run_demo.py` command returned exactly `+919000000002` and
`+919000000004`. These checks verify functional correctness for the tested inputs.

