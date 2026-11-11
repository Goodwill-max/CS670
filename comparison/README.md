# Separate PSI comparison project

This directory contains its own sources, build, runner, and results. The original
`../src/main.cpp`, executable and demo runner contain no comparison additions.

- `src/psi_main.cpp`: standalone direct two-party KKRT PSI baseline.
- `src/pir_psi_measured.cpp`: separate snapshot of the original PIR-PSI driver,
  with optional channel counters. Protocol operations are unchanged.
- `scripts/benchmark.py`: same-data comparison with independent correctness checks.

Both programs share only the existing vendored cryptographic backend. Run from
the existing VS Code development container; finish the original backend setup
first. No additional Docker rebuild is needed.

```sh
cd /workspaces/CS670/comparison
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target kkrt_psi pir_psi_measured --parallel 2
python3 scripts/benchmark.py
```

Open `results/COMPARISON.md`. Raw measurements and machine metadata are saved
alongside it. Five measured runs follow one excluded warmup per case/protocol;
order alternates. Inputs range from the original sample to 10,000 server records
and 128 client contacts. Each intersection must match a plain-set oracle.

Wall time includes startup, preprocessing, fresh base OTs and shutdown. Client
communication counts both directions; total includes the interserver link once.
Counters do not measure IP/Ethernet or connection-handshake overhead. All parties
run on the same machine over loopback. This compares direct KKRT with our
unoptimized PIR-PSI, not every PSI scheme or the paper's optimized implementation.

The comparison builds in its own directory. The original project's CTest
checks can be run independently from the repository root.
