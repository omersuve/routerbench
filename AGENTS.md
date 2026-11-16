# RouterBench

Read README.md, docs/decision-report.md and docs/methodology.md at start/resume.
They own shared state and methodology. Preserve historical datasets and raw
phase 1/2 evidence. archive/ is local historical material, excluded from release.
Never run archived credential discovery or paid transports.

Observe-only harness: no agent integration, global/skill/model config edits,
other project writes or deployments. Repository delivery follows the user's
explicit authorization; this file grants no standing remote-write authority. Paid API
transport is absent from the public package. Jev runs use explicit replay files.
Local inference requires explicit --allow-local and an installed model. No pulls,
credentials, proxies, redirects or remote inference endpoints. Generated source
code is never executed; the execution benchmark writes bounded data files and
runs trusted validators only. No prompts/labels in source control may contain
private project inputs. Prediction must never load labels; scoring is separate.

Python standard library only. Run python3 -m unittest discover -s tests -v.
Use python3 -m routerbench --help for current commands. Do not overwrite run
artifacts, revise frozen labels after seeing predictions or reset old ledgers.
Release archives are generated from an audited explicit allowlist, never the
whole working directory. Preserve frozen inputs, labels and historical results.
