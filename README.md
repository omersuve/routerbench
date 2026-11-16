# RouterBench v0.1.0 Research Preview

[![Offline CI](https://github.com/omersuve/routerbench/actions/workflows/ci.yml/badge.svg)](https://github.com/omersuve/routerbench/actions/workflows/ci.yml)

**A small, provider-neutral benchmark for AI agent routing decisions.**

Routing a task requires more than estimating difficulty: operational risk,
capabilities, model profile, reasoning effort and relevant skills can disagree.
RouterBench compares deterministic rules, local classifiers and recorded provider
decisions against explicit reference labels, reporting each dimension separately.
It observes recommendations; every result has `execute=false`.

Python 3.11+ · standard library only · MIT · no API key or installation required.
The package contains no paid API transport.

## Quick start

Clone this repository or extract the release source archive, then run:

```sh
python3 -m unittest discover -s tests -v
python3 -m routerbench predict --inputs datasets/phase3/inputs.json --adapter rules --output runs/rules
python3 -m routerbench score --run runs/rules --labels datasets/phase3/labels.json --output runs/rules-score.json
```

Prediction reads tasks only; scoring opens labels after predictions are complete
and hash-sealed. Existing outputs are never overwritten: choose a new run name
when repeating a command. The score includes these fields (abridged):

```json
{
  "n": 32,
  "observed": 32,
  "coverage": 1.0,
  "metrics": {
    "route_exact": {"correct": 11, "total": 32, "accuracy": 0.34375}
  },
  "paid_calls_this_run": 0
}
```

## Benchmark results

Agreement with AI-authored reference labels on **32 new synthetic tasks**:

| Metric | Rules | Local: qwen3.5:9b | Jev |
|---|---:|---:|---:|
| Observed tasks | 32/32 | 32/32 | **0/32 — not measured** |
| Difficulty | 12/32 | 27/32 | — |
| Operational risk | 32/32 | 29/32 | — |
| Model profile + effort | 11/32 (34.4%) | 26/32 (81.3%) | — |
| All dimensions | 7/32 | 11/32 | — |

Historical replay on a separate 24-task set yielded model-profile + effort
agreement of 7/24 for rules, 19/24 for local and 23/24 for Jev. These are historical
observations, not new provider calls or a controlled ranking of providers.
The local serial timing repeat had a 546 ms median and 1,046 ms p95, with identical
assessments on 32/32 tasks. A separate six-file local repair probe passed 5/6
trusted validators; this is not a full coding-agent benchmark.

**All included task/label pairs were AI-authored and have no independent human
adjudication. Jev was not measured on the new 32 tasks. Production safety is
unproven.** Model profiles are hypothetical runtime assumptions, and effort is
derived from difficulty. One local prediction classified a reference high-risk
task as low risk. Public labels are exposed references, not a secret holdout.
These results do not establish optimal model selection, spend or safe automation.
See the [decision report](docs/decision-report.md), [methodology](docs/methodology.md)
and [aggregate results](results/summary.json) for denominators and limitations.

## Replay and optional local inference

Run the included hand-authored example (schema demonstration, not model evidence):

```sh
python3 -m routerbench predict --inputs examples/inputs.json --adapter replay --responses examples/responses.jsonl --output runs/example
python3 -m routerbench score --run runs/example --labels examples/labels.json --output runs/example-score.json
```

`--adapter jev --responses YOUR_RECORDING.jsonl` decodes a user-supplied,
permitted recording; it never calls Jev. Raw historical provider responses are
excluded. Missing task hashes remain missing observations. Optional
`--threshold 0.7` abstains on low or absent certainty; always report coverage.

Local inference requires an already installed Ollama model and explicit opt-in:

```sh
python3 -m routerbench predict --inputs datasets/phase3/inputs.json --adapter local --model YOUR_INSTALLED_MODEL --allow-local --output runs/local
python3 -m routerbench score --run runs/local --labels datasets/phase3/labels.json --output runs/local-score.json
python3 -m routerbench execute --model YOUR_INSTALLED_MODEL --allow-local --output runs/execution.json
```

Only literal loopback inference is supported. The harness refuses proxies,
redirects, remote model aliases and downloads; the model must report
`think=false` support. The repair probe writes bounded data files and runs trusted
validators, never generated code. See `python3 -m routerbench --help`.

## License and release checks

Original code, documentation and synthetic datasets use [MIT](LICENSE).
No third-party SDK, model weights or skill implementations are bundled;
provider recordings and optional models retain their own terms. See
[NOTICE](NOTICE.md) and the [release audit](docs/release-audit.md).

```sh
python3 -m routerbench audit
mkdir -p dist
python3 -m routerbench export --output dist/routerbench-0.1.0.zip
```

Export uses an explicit allowlist and contains no private experiment history.
GitHub Actions runs offline tests, CLI smoke checks and archive verification
without provider credentials. Project decisions and continuation notes live in
the decision report; [AGENTS.md](AGENTS.md) defines the source workflow.
