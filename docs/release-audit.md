# v0.1.0 public snapshot audit

This repository starts from the audited source distribution, extracted into a
clean directory with no inherited Git metadata. Source archive SHA-256:
`61c11143b09e9e99fb8cd8b1ca425293c5ea71a43ad14b9b74e08412b8225e90`.
The original experiment and old archives remain untouched.

## Included surface and changes

The explicit allowlist contains original package code, tests, synthetic datasets,
a hand-authored replay example, aggregate results, documentation and the pinned
GitHub Actions workflow. It excludes old experiment sources, raw provider/model
outputs, private path inventories, run directories, environments, weights and
caches. No secret/configuration files or personal home paths are intended for
publication. Hypothetical private/production tasks contain no such source data.

Preparation rewrote the English README and decision report, added offline CI,
added two integration checks, included CI in export and corrected human-label
metadata in two historical manifests. Original task/label files, rubric, core
routing semantics and recorded benchmark results are unchanged.

## Security and licensing

Runtime imports use Python standard library only. No SDK, third-party source,
model weights or skill implementation is redistributed. Original source, docs and
synthetic datasets use MIT; the text was compared with the SPDX reference.
Optional packaging uses setuptools; source execution requires no installation.
Provider recordings and optional runtimes/models retain their separate terms;
see [NOTICE](../NOTICE.md), including the TypeSafe output-use restrictions.
No raw provider response is offered as MIT training data.

Runtime has no credential discovery, environment-key reads, paid transport,
model downloads, remote inference option or agent-config writes. Explicitly
opted-in local inference uses literal loopback with proxies and redirects refused.
Execution probes run trusted validators on bounded data files, not generated code.
Offline tests mock local network boundaries and require no daemon or credentials.

Audit checks cover personal paths, common credential shapes, symlinks, imports,
relative documentation links and runtime dependencies. Additional prepublication
inspection covers all source files, dataset schemas/hashes, metadata and the
staged Git surface. Pattern scans cannot prove absence of every possible secret;
license review is limited to the included materials and linked public terms.

## Verification

- 44 offline tests pass locally on Python 3.15.2.
- Rules metrics reproduce the shipped summary on all 28 + 24 + 32 tasks.
- The hand-authored replay example scores 1/1 with full coverage.
- Dataset/task hashes and original historical bytes are checked.
- CLI prediction, scoring, audit and export work from source.
- Two exports from identical source bytes have matching SHA-256 hashes on the
  same Python/zlib tooling; extracted archives include the CI workflow and tests.
- GitHub Actions tests Python 3.11–3.14, the documented offline commands and a
  fresh extraction. No provider key, paid call or live local model is required.

The CLI audit/export commands themselves do not create repos, push or publish.
The GitHub release is a research prerelease: AI labels lack independent review,
Jev has no observations on the new 32 tasks and production safety is unproven.
