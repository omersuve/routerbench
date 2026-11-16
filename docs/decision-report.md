# Research preview decision and continuation record

17 November 2026. **Suitable for a public v0.1.0 research preview of an evaluation
harness.** The evidence does not validate a best-model router, safe production
routing or end-to-end coding quality. No real agent integration was performed.

This report, [README](../README.md) and [methodology](methodology.md) own shared
project state. Read them at task start/resume. This repository is a fresh source
snapshot extracted from the audited distribution, with no private Git history.
The original experiment and its historical archive remain separate and unchanged.

## Protocol and evidence

The package uses Python standard library only, one CLI and a shared
`predict(task) -> Observation` interface for rules, local inference and explicit
provider recordings. Prediction accepts tasks only and rejects labels. Scoring
opens separate labels after receipt hashes seal predictions. Missing, invalid or
uncertain assessments receive no guessed provider prediction or strong-model
fallback. Coverage and unobserved high-risk counts stay explicit.

The 28 phase 1 and 24 phase 2 synthetic originals remain byte-for-byte intact.
Phase 3 adds 32 shuffled tasks whose inputs and labels were hash-frozen before
inference. **All included task/label pairs were AI-authored, with no independent
human adjudication.** The author knew the labels; protocol separation is not
independent scientific blinding. Public tasks are exposed references and cannot
serve as future secret tests. No labels, rubric or rules were tuned after these
observations. A later scorer display fix represents wholly unobserved accuracy
as null rather than zero; it changed no predictions or observed counts.

## New 32-task set: first pass

| Metric | Rules | Local classifier | Jev |
|---|---:|---:|---:|
| Observed predictions | 32/32 | 32/32 | **0/32 — not measured** |
| Difficulty agreement | 12/32 | 27/32 | — |
| Operational risk | 32/32 | 29/32 | — |
| Model profile | 16/32 | 26/32 | — |
| Reasoning effort | 12/32 | 27/32 | — |
| Skill set | 29/32 | 28/32 | — |
| Capability set | 18/32 | 17/32 | — |
| Model + effort | 11/32 (34.4%) | 26/32 (81.3%) | — |
| All dimensions | 7/32 | 11/32 | — |
| Selected profile misses required capabilities | 2 | 1 | unobserved |
| High risk classified as low | 0 | 1 | 4 high-risk tasks unobserved |

Descriptive Wilson 95% intervals for model + effort agreement are approximately
20.4–51.7% for rules and 64.7–91.1% for local. These intervals do not validate
AI labels, independence across task families or commercial model superiority.
Effort is derived from difficulty, so they are not independent successes.

**Jev was not measured on these 32 tasks.** No new paid call was made: the prior
phase budget was exhausted and no paid transport ships. Old recordings did not
match new task hashes and remain missing observations. Zero observed predictions
does not mean zero provider accuracy. This phase establishes no three-provider
ranking on the new set.

## Historical 24-task replay

| Metric | Rules | Local replay | Jev replay |
|---|---:|---:|---:|
| Difficulty | 6/24 | 20/24 | 24/24 |
| Risk | 24/24 | 23/24 | 24/24 |
| Model | 12/24 | 21/24 | 23/24 |
| Effort | 7/24 | 20/24 | 24/24 |
| Skills | 21/24 | 20/24 | 21/24 |
| Model + effort | 7/24 | 19/24 | 23/24 |

The shared scorer reproduces earlier results. Replay is not fresh inference;
Jev's 296 ms and local's 543 ms medians belong to historical observations.
Raw responses are excluded rather than relicensed as MIT training data, so
public aggregates alone cannot independently reproduce every provider decision.
The replay interface requires a user-supplied recording with permitted provenance.

A fixed Jev certainty threshold of 0.70 accepts 15 and abstains on 9 tasks:
coverage 62.5%, accepted model + effort accuracy 100%, correct-route yield 15/24.
Earlier fallback-based accounting counted 17/24; the shared method assigns no
route to uncertain tasks. Three high-risk tasks remain unobserved after this
threshold and cannot be counted as safe classifications. The threshold was not
adjusted against these results.

## Misrouting, execution and timing

None of nine new hard tasks was assigned to local. Rules proposed insufficient
effort on six, local on three. These are disagreements with predefined profiles,
not proof of actual commercial-model failures.

Local classified H021, a hypothetical read from a production admin tool, as low
risk without tools and proposed local. The rubric marks production work high
risk, making this a classification/capability error. Whether a read-only task
should be high risk also needs independent adjudication. Host facts are supplied
by a trusted operator; the benchmark does not discover hidden effects. Policy
always has `execute=false`; no production action was attempted.

The existing qwen3.5:9b local installation passed **5/6** small data-file repair
validators: JSON config, CSV header, INI flag, JSONL deduplication and version
sorting passed; strict Markdown link preservation failed. The validator was not
relaxed after failure. Each task used a fresh temporary directory, a fixed target
and trusted validators; generated code, shell and model-selected paths were never
executed. Raw failed content was not retained, so whitespace versus substantive
link failure cannot be separated. This is not a repository coding-agent test.

The original routing run partly overlapped the execution probe. Primary accuracy
was preserved. A subsequent serial local repeat produced identical assessments
on **32/32 tasks**, with **546 ms median and 1,046 ms p95**. First-pass timing was
718 ms median and 2,417 ms p95; rules had about 0.012 ms median. Energy, controlled
cold starts and service load were not measured. One repeat proves no general
determinism or stability claim.

## Public snapshot preparation

The source distribution was extracted into a clean directory. The English README
now shows the problem, quick start, sample output and benchmark limitations.
Two historical manifest descriptions incorrectly said human preference labels;
only that metadata was corrected to AI-authored reference preference labels.
Frozen task, label, rubric and benchmark result bytes were preserved.

The public allowlist now includes offline GitHub Actions and an additional test
module that reproduces all three rules baselines and the synthetic replay.
The 44 offline tests pass locally on Python 3.15.2. CI is configured for Python
3.11, 3.12, 3.13 and 3.14, including CLI smoke checks and a fresh exported archive.
See [release audit](release-audit.md) for verification scope and
[NOTICE](../NOTICE.md) for license boundaries. No paid inference is used by CI or
publication preparation. Repository delivery requires explicit user authority;
this record grants no standing permission for future writes.

## Remaining scientific work

Use an independent annotator who retains labels, freeze a new three-provider
experiment in advance and measure actual model execution quality. Other open
issues are tier/effort assumptions, threshold calibration, independent repeats,
trusted-host fact accuracy and the narrow repair scope. Production safety remains
unproven. No global settings, installed skills or other projects need changes.

Machine-readable evidence: [summary](../results/summary.json) and
[execution](../results/execution.json). Future work must preserve original
observations and record new experiments separately.
