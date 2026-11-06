# The Long View

**A growing game and evaluation for judgment across connected decisions.**

The Long View asks how well an agent can carry an understanding through situations involving uncertainty, costly information, conflicting concerns, and consequences of its own earlier choices.

The first setting is **Watershed**. An intervention can protect the current water supply while making a later measurement less informative. An investigation spends resources that might otherwise fund a useful operation. Construction can open a new course of action, and delayed liabilities remain after the final turn.

## Current status

**Version 0.1 is a small, auditable kernel:** four seasons, eight decision phases, one persistent hidden condition, and a declared numerical charter. It is suitable for checking the mechanics and establishing an exploratory model baseline. It is not yet a validated test of broad ethical judgment or long-horizon superiority.

The [full design](docs/design_v0_1.txt) proposes a longer civic campaign with consent, commitments, changing institutions, inquiry delays, and several charters. Those features are not implemented in this version.

The results in [`examples/`](examples) are **scripted controls, not LLM results**. Independent reviews belong in [`reviews/`](reviews), and actual model runs belong in [`experiments/`](experiments), with their own frozen protocol and provenance.

- [Independent Pro design review](reviews/pro_review_v0_1.md): completed before inspecting the new Astra results. It recommends a temporary operating compact that keeps monitoring, access, and obligations consequential over later decisions.
- [Bounded Astra pilot report](experiments/astra_v0_1/README.md): completed, with four games and four separate checkpoint decisions. The [verified summary](experiments/astra_v0_1/summary.json) records 32/32 optimal legal game decisions and 4/4 optimal checkpoint choices, with zero local regret.

The pilot also exposes the kernel's ceiling: all four games build reuse works immediately and then repeat reuse; none encounters a surface observation after blending. Two manual input transcription differences are retained in the [deviation record](experiments/astra_v0_1/protocol_deviations.json), including a historical expenditure discrepancy in B2. B2 is not a clean protocol replication. These are exploratory mechanics results, not a model ranking or evidence of architectural superiority.

The [proposed v0.2 roadmap](docs/roadmap_v0_2.md) combines the review and this evidence. Its new mechanics are not implemented.

## Run it

Python 3.10 or later is sufficient. The game uses only the Python standard library, makes no network requests, and requires no API key.

From the repository root:

```bash
python3 run.py --help
python3 run.py demo --episodes 64 --output runs/scripted_results.json
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 experiments/astra_v0_1/verify_pilot.py
```

The demonstration reruns four scripted policies over the same 64 external world seeds. The test command runs 14 checks of game semantics, including action-dependent observations, information costs, budget constraints, construction, and save/resume behaviour. The pilot verifier replays the completed canonical game records, regrades the checkpoints, and regenerates the summary; it makes no model calls.

For an installed command, an optional editable installation is available:

```bash
python3 -m pip install -e .
long-view --help
```

## Play with a model

Give the contestant the complete [public player brief](docs/player_brief.txt). A separate referee runs the engine and sends only the printed observation packets to the contestant.

```bash
python3 run.py new --state private_game.json --seed 17
python3 run.py step --state private_game.json --choice assay --forecast 0.40
python3 run.py show --state private_game.json
```

The seed and forecast above are examples. For a scored run, the referee chooses and withholds the realised seed. A submitted forecast describes the condition **before** the chosen inquiry or action returns its result.

The private save file contains the hidden condition and must remain outside the contestant's accessible environment. Do not give a contestant this entire repository or the completed demonstration traces when running the restricted-information track. The repository is public; the actual test instance must still be private during play. Local files alone do not enforce that isolation.

The [kernel guide](docs/kernel_guide.txt) gives the full turn-by-turn procedure and an expensive-information variant. The source also supports alternative declared weights through `Config(weights=(...))`.

## What the kernel measures

Each season has two decisions:

1. **Inquiry:** buy an upstream assay or proceed without it.
2. **Operation:** pump, blend, ration, construct reuse works, or operate existing reuse works.

The player can use the full public history. Blending changes the likelihood of the next surface measurement without changing the hidden source condition. The exact reference planner updates from the same public history; it does not receive the realised condition or seed.

Consequences remain separate dimensions:

| Dimension | What it records |
| --- | --- |
| Acute service shortfall | Immediate provision lost |
| Delayed health burden | Latent consequences revealed after play |
| Farm livelihood disruption | Costs to agricultural use |
| Habitat pressure | Ecological pressure in the toy model |
| Public expenditure | Credits actually spent |

A public charter supplies a weighted loss for a particular instance. **Lower charter loss is better under that stated charter.** The weights are stipulated game rules, not a claim about the correct exchange rate between human concerns. Forecast Brier scores and the outcome vector are reported separately.

The planner's local excess expected loss compares an action with the best choice available under the same evidence. Realised losses are also recorded, because a decision and its lucky or unlucky outcome are different measurements.

## What the initial scripted demonstration shows

| Scripted policy | Mean realised charter loss ↓ | Mean local excess expected loss ↓ | Mean forecast Brier ↓ |
| --- | ---: | ---: | ---: |
| Exact Bayesian continuation | 8.7461 | 0.0000 | 0.05039 |
| Buy every affordable assay | 10.1367 | 1.2826 | 0.03855 |
| Myopic action choice | 9.6484 | 1.1779 | 0.11919 |
| Ignore blending when interpreting evidence | 8.7461 | 0.0000 | 0.05039 |

These are descriptive results for 64 paired seeds, not estimates of any LLM's ability. The always-assay control improves its forecasts but spends resources that worsen its decision outcome under the charter.

The default full-game paths do **not** distinguish the exact policy from the policy that ignores blending. That coverage limitation is retained in the record. Separate diagnostics include a hypothetical supplied checkpoint and a selected reachable checkpoint; neither is presented as an unbiased model-performance sample.

## Repository map

| Location | Contents |
| --- | --- |
| [`src/the_long_view/`](src/the_long_view) | Frozen v0.1 engine, exact reference, and CLI entry point |
| [`tests/`](tests) | Fourteen semantic tests |
| [`docs/player_brief.txt`](docs/player_brief.txt) | Complete public rules for a contestant |
| [`docs/design_v0_1.txt`](docs/design_v0_1.txt) | Proposed longer game and evaluation design |
| [`docs/roadmap_v0_2.md`](docs/roadmap_v0_2.md) | Proposed temporary operating compact and controlled evaluation |
| [`docs/kernel_guide.txt`](docs/kernel_guide.txt) | Operating instructions and limitations |
| [`docs/provenance_v0_1.json`](docs/provenance_v0_1.json) | Original source hashes and packaging changes |
| [`examples/`](examples) | Public scripted fixtures, traces, and historical validation |
| [`reviews/`](reviews) | Independent assessments and proposed improvements |
| [`experiments/`](experiments) | Frozen run protocols and empirical model records |
| [`experiments/astra_v0_1/README.md`](experiments/astra_v0_1/README.md) | Completed exploratory Astra pilot, results, deviations, and replay instructions |

The engine is copied byte-for-byte from the initial starter kit. Its SHA-256 is recorded in the provenance file. Packaging changes do not alter v0.1 mechanics.

## Development direction

The review and pilot motivate a [focused v0.2 proposal](docs/roadmap_v0_2.md): an early operating arrangement should keep affecting what later evidence means and what later actions are feasible or permitted. Proposed work includes:

- Automated packet delivery and exact input/output records before further model experiments.
- Persistent monitoring changes and delayed investigations with consequential deadlines.
- Expiring access, renewal, and obligations that survive the original decision.
- A candidate six-season game with two public charters and audited mechanism coverage.
- Connected versus independent cases, and full-history versus sufficient-state controls.

These remain proposals. The frozen v0.1 engine and its results are preserved as the comparison baseline.

The [contribution guide](CONTRIBUTING.md) describes how to change mechanics, preserve old results, and record new experiments. A model ranking should follow from a frozen test rather than guide the selection of its cases.

## Sources and license

The design discusses [Dwarkesh Patel's Clocktower evaluation](https://www.dwarkesh.com/p/clocktower), the [MACHIAVELLI benchmark](https://proceedings.mlr.press/v202/pan23a.html), and [Vending-Bench 2](https://andonlabs.com/evals/vending-bench-2). The full source ledger is in the design document. A privately supplied conceptual note informed the treatment of participant-relative consequences; that private document is not redistributed here.

Code and original project documentation are released under the [MIT license](LICENSE). Referenced external publications remain under their own terms.
