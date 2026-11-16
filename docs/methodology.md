# Method and schema

RouterBench measures agreement with explicit reference preference labels and the
behavior of a declared hypothetical model/runtime catalog. It does not find the
universally best commercial model, authorize effects, load skills or modify an
agent. The baseline rules and routing core are preserved from phase 1. The shared
semantic rubric is preserved from phase 2; the local output wrapper is versioned.
All recommendations remain observe-only with execute=false.

## Label separation and preregistration

`predict` accepts only a JSON array of `{id, task}`. It rejects extra expected or
label fields; it has no --labels flag. The classifier sees only the task and
fixed rubric. Each task contains text and complete host facts: environment,
action, data_class, external_effect, context_tokens. Facts are supplied by a
trusted operator, not inferred permission. Missing facts fail closed. Labels
contain their input-file SHA-256 and each task's canonical SHA-256.

Predictions are written to a new directory as JSONL, then sealed by a manifest
containing input, rubric, routing, task-index and output hashes. Incomplete runs
have no manifest and cannot be scored. Existing directories/results are never
overwritten. `score` alone opens labels and verifies every task, ID and hash.
A hash receipt detects accidental edits; it is not cryptographic authentication
against an adversary who rewrites both predictions and receipts.

For an independent blind evaluation, an organizer prepares and seals labels,
distributes only inputs to classifier runners, receives sealed predictions, and
then scores. The included phase 3 run follows the input/scoring separation but
its AI author knew the labels and the included labels were not independently
reviewed by humans. **It is not independently adjudicated or
truly author-blind.** Once shipped publicly, labels and tasks are exposed and
must not be presented as a future secret holdout. New classifiers/thresholds
should use new externally annotated tasks for confirmatory claims.

The 28 phase 1 and 24 phase 2 tasks are historical references. Phase 3's 32 new
shuffled tasks were committed by hash before inference. No task, label, rubric,
rule or threshold was revised after seeing results. A post-run scorer display
fix represents wholly unobserved accuracy as null instead of zero (yield remains
zero); it changes no predictions or observed counts. A serialized local timing
repeat addresses overlapping local inference during the original execution
probe; primary accuracy remains from the first pass.

## Common classifier interface

An adapter implements `predict(task) -> Observation` with status, assessment,
optional certainty, latency_ms, source, usage and reason. Assessments contain
separate difficulty, risk, capabilities and skills. The common router derives
model profile and effort. Default profiles are local/general/visual/deep, with
explicit context/capability/privacy filters. These model+runtime tiers are
experimental assumptions, not measured performance rankings. Effort and
difficulty are mathematically linked in this catalog, not independent findings.

Rules call a pure heuristic. Local requires --allow-local, an explicit already
installed model, verified think=false support and a literal loopback endpoint.
No proxy, redirect, pull, remote-model alias or tools are accepted. A caller may
add a provider adapter via this same small Python interface, or import explicit
JSONL recordings through replay. There is **no paid inference transport** in v0.1.
The Jev adapter decodes a provided recorded response; it never searches for a
key, reads environment credentials or calls the provider. Missing task hashes
are missing observations, never substituted predictions.

A replay line binds task_sha256 to either an assessment or a recorded Jev
response. It may include certainty, latency_ms and usage. Recorded latency is
historical, not the duration of an offline replay. Replay files have a receipt
hash, but their claimed provenance is the supplier's responsibility. No raw
provider responses ship in the public archive; a hand-authored schema example
is clearly marked as synthetic and is not empirical model evidence.

## Metrics, abstention and risk

Difficulty, operational risk, model, effort and skill exact agreement are
reported separately; capability exact agreement and micro set F1 are additional
checks. Confusion matrices, sample denominators and Wilson 95% intervals are
included. Intervals describe sampling uncertainty under a binomial convention;
they do not correct single-author label bias, correlated families or selective
acceptance. No statistical provider-superiority claim follows from these data.

Every task stays in the denominator. `yield` is correct/total. `accuracy` equals
that value when observations exist, and is null when none exist.
`observed_accuracy` uses accepted observations only. Coverage is accepted/total;
missing, invalid, error and abstain counts remain explicit. A task whose valid
assessment legitimately yields model=none is different from an absent or
uncertain assessment. The host policy is reported independently in all cases.

With a threshold, min certainty across all required answers must pass. Jev
Choice certainty uses the selected probability; Noul uses max(p,1-p). These
values are not correctness probabilities. Local/rules have no calibrated
confidence; thresholding an absent certainty abstains, rather than inventing
1.0. Uncertain tasks receive no guessed route and no automatic strong-model
fallback. This differs from phase 2's historical fallback-inflated score.

Audit events include hard-to-local, hard-under-high-effort, high-risk-as-low,
high-risk-below-high, capability misses, uncertain tasks and unobserved high-risk
tasks. No missing prediction counts as a safe risk classification. A low risk
estimate never grants permission; deterministic host facts drive the policy.
The benchmark does not discover hidden command effects or independently verify
the supplied facts. Many risk labels directly reflect those facts.

## Bounded task execution

The optional execution probe repairs six actual synthetic data files in fresh
temporary directories. The model receives content and a requested change and
returns only a bounded content string. The trusted host writes one fixed target
file and validates it using JSON/CSV/INI parsers, exact preservation or a checked
relative Markdown link. There is no model-supplied path, shell, tool executor,
remote operation or execution of generated Python/source code. This tests file
repair outcomes, not full repository feature completion or autonomous coding.
The existing local daemon itself is not placed inside an OS sandbox.
