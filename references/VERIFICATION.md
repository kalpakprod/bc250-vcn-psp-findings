# Collection checks, 2026-10-09

These checks cover the archive and its publication, not firmware behavior.

- The catalog contains 59,113 distinct source records, with 3,552 included and 55,561 excluded, plus 45 source-subtree exclusions. Included paths exist. Binary ROM/EFI/UF2 artifacts are not bundled.
- Python 3 parsed 615 files. JSON parsing covered 779 files before this note was added. Four navigation errors were fixed, leaving no missing local Markdown file targets. Anchor semantics and every external URL were not exhaustively checked.
- The original project's `make test` passed 12 tests. That contract gate does not test VCN codecs or SPI timing.
- Gitleaks reported 11 generic-api-key candidates and kept its nonzero status. Review identified scientific digests/GUIDs, public kernel-certificate identifiers, source-path/import syntax, an integration identifier, a synthetic test token and board/equipment prose. No suppression, baseline or weakened scanner configuration was used. A scanner cannot prove that every possible secret is absent.
- The original publication-policy check counted the repository name 0 times in the baseline, 1 time after the change and 0 times after rollback. Each run used the same command and input and exited 0. The restored bytes matched the original, and the patch reconstructed the changed policy.

Publishing the collection did not rerun saved firmware tests or turn historical PASS claims into new results. Private execution and rollback records remain in the original workspace. Post-publication clean-clone readback is recorded there, rather than claimed in advance in this note.
