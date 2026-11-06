# Public examples

These files are completed, public development fixtures. They are not held-out tests and should not be given to a contestant during a restricted-information game.

| File | Contents |
| --- | --- |
| `scripted_v0_1.json` | Four scripted policies across 64 paired seeds, including decisions, full public histories, outcome vectors, and controlled diagnostics |
| `reachable_checkpoint_v0_1.json` | One selected legal history showing excess precaution from misreading a blended warning |
| `kernel_validation_v0_1.json` | Historical validation record for the frozen kernel |

The scripted controls are not proxies for named LLMs. The ordinary default trajectories give identical results for the exact and ignore-blending policies, so those trajectories do not establish discrimination of that error. The separate diagnostics isolate it.

The belief-0.4 diagnostic is a supplied hypothetical checkpoint. The additional reachable checkpoint was selected by a small diagnostic search and has a small expected decision effect. Neither selection supports a population performance estimate.

Realised charter loss, same-information excess expected loss, and Brier scores measure different things. Policies also buy different amounts of evidence, so their aggregate forecast scores do not by themselves compare reasoning from identical information.
