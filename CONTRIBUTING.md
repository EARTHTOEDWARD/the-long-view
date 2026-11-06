# Contributing

The Long View is a research game with a small working kernel and a larger proposed campaign. Contributions should make the relationship between a mechanism and the capability it tests easier to inspect.

## Start from the current version

Read the [public rules](docs/player_brief.txt), [design](docs/design_v0_1.txt), and any completed independent review before changing mechanics. Keep proposed, implemented, and empirically observed behaviour distinct.

Run the existing checks from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The no-install CLI is `python3 run.py`. The runtime has no third-party dependencies.

## Change mechanics with a versioned explanation

A change to transitions, likelihoods, action prerequisites, charters, or terminal liabilities changes the game. Give it a new version and explain:

- The capability or failure mode the change is intended to test.
- The exact mechanism and any new assumption.
- What the player knows and what remains hidden.
- Which historical results remain comparable.
- The smallest meaningful check that verifies the intended effect.

Preserve the v0.1 scripted results and their source hashes. Add a new result directory instead of silently regenerating them under changed rules. Resolve a concrete measurement risk when adding tests; avoid tests that merely repeat the implementation.

## Record an experiment before interpreting it

Each empirical study should retain a protocol, immutable engine and prompt hashes, model configuration, world selection, resource limits, public observations, submitted actions, and scoring results. State whether the study is exploratory or confirmatory.

Record exclusions, invalid outputs, retries, tool access, context handling, and stopping rules. Do not select a headline result by changing the rules until a preferred model wins. Treat turns within a campaign as dependent observations.

Actual model runs belong in `experiments/`. Keep scripted policies in `examples/` clearly labelled. No private chain-of-thought should be requested or included; concise public decision explanations are sufficient.

## Protect the test instance

Contestants may receive the public rule family without receiving the realised hidden state. Give them only permitted observation packets and tools. A local filename or `.gitignore` rule does not create an access boundary.

Keep API keys, private referee saves, unrevealed test seeds, credentials, and unrelated personal material out of the repository. Completed public fixtures may include their seeds for reproducibility; future held-out worlds require separate handling. Make that distinction explicit in each protocol.

## Review and attribution

An independent assessment belongs in `reviews/`, with its reviewer configuration and limitations. Preserve a clear distinction between the review's proposals and changes that have been implemented.

Cite public sources for external claims. Do not redistribute a private source note merely because its concepts informed the design. Contributions of original code and documentation are accepted under the repository's MIT license.
