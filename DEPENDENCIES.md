# Cryptographic dependency provenance

The upstream source, copyright notices, and license are preserved under
`vendor/libPSI`. The project uses a new driver, not the upstream DRRN benchmark.

| Source | Revision |
| --- | --- |
| https://github.com/osu-crypto/libPSI | 1159df1fecad06570ec384d64ab0724d05b6905b |
| https://github.com/osu-crypto/libOTe | f47217d924ceef9b65e04a9ae680b65a79a4425a |
| https://github.com/sparsehash/sparsehash-c11 | edd6f1180156e76facc1c0449da245208ab39503 |

The latter two revisions are specified by upstream's `thirdparty/get*.cmake`.
Local build compatibility changes: `getLibOTe.cmake` enables only Naor-Pinkas
base OT, IKNP extension, and KKRT, and forwards a CMake project hook. The hook
in `cmake/DependencyCompatibility.cmake` replaces the retired Boost JFrog
download URL with `archives.boost.io`; the original SHA256 remains enforced.
The vendored CMake entry point also provides `LIBPSI_BUILD_FRONTEND` so this
application can exclude upstream's standalone benchmark and its test library.
The application's own CTest checks remain enabled.
Transitive dependency selection is delegated to that pinned libOTe build.
The base Ubuntu image and apt package versions are not reproducibly pinned.
This is a research dependency stack; a successful build does not constitute a
security audit or establish compatibility with every modern compiler.
