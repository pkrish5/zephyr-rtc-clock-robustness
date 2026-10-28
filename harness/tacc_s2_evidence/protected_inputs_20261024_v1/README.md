# Original audit dependencies

This cache repairs missing paths for the read-only archive audit. It does
not add experimental subjects, rebuild firmware, or change the collector.

`baseline.json` is an exact copy of the original 30,067-file Phase 2
protected baseline, SHA-256
`b0078f949d83672aadf1a5e385caebcb61842435b92cf41e1e30507e41102aef`.
The original stays in the Mac's ignored artifacts directory.

`protected_files.tar.gz` contains 508 original protected files absent from
the Git index at c258b108: existing ignored ELFs, build products, and build
metadata. Every byte was checked against that original baseline before
packaging. Uncompressed size: 86,313,046 bytes. Archive size: 25,480,881
bytes; SHA-256 `5ade857dfde2eaeaac225f5538bc55c76f4f0bd91112a1f1a5b4f7e6d19ec971`.
`cache_manifest.json` lists their original paths, sizes, and hashes.

The development-only `stage_audit_paths.py` checks all pre-existing
protected bytes before creating anything. It fills only missing paths,
uses exclusive creation, refuses to overwrite any existing file, installs
the identical baseline at the collector's original expected path, and
runs the unchanged full protected-file audit. Archive contents and
selection code remain unchanged. The retry uses a fresh output directory;
the failed job's logs and empty destination are retained.
