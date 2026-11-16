# Provenance and third-party boundaries

Original harness code, documentation, synthetic task inputs and single-author
preference labels are offered under the MIT license in LICENSE. No external
project code, skill implementation, SDK, tokenizer, model weights or credentials
are bundled. Runtime dependencies: Python standard library only. Optional pip
build/install uses setuptools as a build dependency; running from source needs
no installation. Skill IDs and provider/model names are descriptive identifiers,
not endorsements or licenses to their implementations.

Historical phase 1 (28) and phase 2 (24) synthetic task originals are preserved
byte-for-byte in datasets/*/original.json; their manifest hashes record that
provenance. Phase 3 adds 32 new single-author synthetic tasks. Task/label pairs were AI-authored and not independently human-adjudicated.
No real customer,
employer or private project data is included. Some tasks describe hypothetical
private/production work; they contain no such source data.

Raw provider responses and model outputs remain outside the public release
allowlist. They are not relicensed as MIT training data. The exported result
summaries contain factual aggregate benchmark measurements, not a distillation
dataset or a competing decision service. Users importing their own response
recordings remain responsible for their source terms and permitted uses.

TypeSafe's public Master Customer Agreement section 4.2 assigns its interests in
Output to the customer, but section 2.3 separately restricts uses including model
distillation and competing products. Output ownership is not a waiver of those
restrictions. This project neither trains models nor ships the historical raw
responses. Account-specific agreements may differ. Source checked 17 November
2026: [TypeSafe MCA](https://typesafe.ai/legal/mca).

The MIT text was checked against the [SPDX MIT reference](https://spdx.org/licenses/MIT.html).
Optional Ollama is a separately installed service; its runtime and any selected
model have their own licenses. This archive contains neither. The model used for
local observations was an existing qwen3.5:9b installation; no weights were
installed, downloaded, modified or distributed.
