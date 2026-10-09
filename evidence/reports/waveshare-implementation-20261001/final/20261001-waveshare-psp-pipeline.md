# Offline Waveshare PSP pipeline

`scripts/waveshare_psp_pipeline.py` is a host-side, read-only preparation tool.
It locates the literal `BL_PUBLIC_KEY`, `TRUSTED_OS`, and `DRIVER_ENTRIES`
labels in a donor image and records offsets, sizes and SHA-256 hashes.  The
`patch` operation compares two separate files and emits a JSON manifest with
clean, patched and changed-range records; it never overwrites the donor.
`keygen` creates a local RSA-2048 PEM with mode 0600 and prints only its path.
`verify` checks a container hash and, when supplied, RSA-PSS/SHA-256 using a
public key and detached signature.  All operations are offline and deterministic
for a fixed fixture.  No signing key or signature bytes are printed.

## Provenance and assumptions

The marker names and RSA-PSS/SHA-256 requirement are taken from the supplied
Waveshare/Habr migration brief.  Exact PSP table serialization, signature
placement, and board-specific offsets remain hardware assumptions; this tool
does not claim that a manifest is bootable and performs no flash or board I/O.


## Hardened parser
The pipeline now parses a proven `$PSP` directory (header signature, count, 16-byte entries) when present and reports unsupported values as `UNKNOWN`. Candidate writes are bounded to a new output path; manifests include rollback metadata. RSA-PSS verification uses SHA-256 with explicit salt length 32.
