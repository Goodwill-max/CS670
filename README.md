# PIR-PSI private contact discovery

C++ research project implementing the **two-server, unbinned, single-entry-block**
construction in Sections 2.3 and 3.1-3.3 of *PIR-PSI: Scaling Private Contact
Discovery* (Demmler, Rindal, Rosulek, Trieu, PETS 2018).

The cryptographic backend is the authors' [libPSI](https://github.com/osu-crypto/libPSI),
vendored at commit `1159df1fecad06570ec384d64ab0724d05b6905b` with its license.
`src/main.cpp` is a new application driver. It does **not** call the upstream
`DrrnPsiClient`/`DrrnPsiServer` benchmarking path, which has hardcoded masks and
tests explicitly documenting incorrect intersections.

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

| Paper component | Implementation |
| --- | --- |
| 128-bit item encoding | domain-separated RandomOracle digest in `encode` |
| Three-choice cuckoo table, Sec. 3.2 | `cuckoo`: augmenting paths, public fresh salt, identical replicas |
| BGI distributed point function, Sec. 2.3 | upstream `BgiPirClient::keyGen`, `BgiPirServer::fullDomain` |
| Designated-output PIR, Sec. 3.1 | server1 sends its masked response directly to server0 |
| Hide cuckoo location, Sec. 3.3 | fresh three-mask vector per contact; server1 secretly shuffles it |
| Secure PSI, reference [30] | upstream `KkrtPsiSender` and `KkrtPsiReceiver`, real KKRT OT extension and base OTs |
| Client output | matched masked-input indices map to original contacts; deduplicate |

Each query produces shares `v0 XOR v1 = CT[h_j(x)]`. Server1 sends
`v1 XOR r_sigma(j)` to server0, which forms `CT[h_j(x)] XOR r_sigma(j)`.
The client inputs all three `x XOR r_j` values into KKRT PSI with server0.
The secret permutation prevents a successful match from identifying the occupied
cuckoo location. The client never receives an unmasked database value or the
servers' PIR shares. Masks, DPF seeds, OT seeds, and secret permutations use fresh
OS-seeded PRNGs on every invocation.

## Scope and security assumptions

This is a research implementation, **not an audited production system**. Its
intended model is semi-honest parties and two non-colluding servers. Running both
on one computer is a functional demo, not independent operation. Each server
holds the complete database. Contact and database sizes are public. Colluding
servers can reconstruct query locations. PSI does not stop clients from testing
guessed phone numbers; deployment needs a separate authorization policy.

This project implements the core construction rather than the paper's entire
optimized prototype. Query binning (Sec. 3.4), larger PIR blocks (Sec. 3.5),
Appendix A's optimized global permutation, AES batch tuning, persistent sessions,
associated-data retrieval, and 3/4-server variants are not implemented. The table
uses conservative power-of-two sizing of at least 2N rather than the paper's
experimental tight sizing formula. Construction failure aborts. Server work is
O(client-size * database-size); do not expect the published million-user timings.

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
`+919000000004`. These checks establish tested functionality, not a security audit
or the paper's published performance claims.

