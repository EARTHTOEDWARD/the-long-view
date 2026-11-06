# Astra v0.1: exploratory mechanics pilot

**Completed 6 November 2026.** Astra selected an optimal legal choice on every recorded decision: **32/32 decisions across four complete games**, and **4/4 separate checkpoint decisions**. Local excess expected loss was zero throughout. These results establish successful play on this small sample; the narrow trajectories and documented input discrepancies limit what they demonstrate. The numerical source is the replay-verified [summary](summary.json).

## Design and budget

The [frozen protocol](protocol.json) specified two exogenous world seeds, each played with assay prices of one and two credits: A1/A2 share one world, B1/B2 another. Each four-season game contains eight responses, alternating inquiry and operation. Four separately specified, single-decision checkpoints bring the total to **32 game responses plus 4 diagnostic responses = 36**. There were no extra repair responses or replacement runs.

The requested contestant was **`gpt-6-astra` with high reasoning effort**. Each game and checkpoint used a fresh task instance without parent history. The [shared prompt](contestant_prompt.txt) required JSON, a public reason of at most 120 words, and no tools. Isolation was prompt-based; the shared runtime did not provide a hardened boundary. Independent model-ID and reasoning-mode attestation were unavailable. No external API requests were used, and inference dollars, reasoning tokens, and per-decision inference time were unavailable. This was a decision-count budget, not a measured dollar cap. [Protocol and telemetry limits](protocol_deviations.json).

## Complete-game results

Lower charter loss is better under the game's stipulated weights. Local regret compares each applied choice with the minimum expected remaining loss under the same public information and optimal continuation; the reference does not know the realised source condition during grading.

| Game | Assay price | Revealed source | Charter loss | Forecast Brier | Local regret |
| --- | ---: | --- | ---: | ---: | ---: |
| [A1](A1.json) | 1 | Benign | 11.25 | 0.05696478 | 0 |
| [A2](A2.json) | 2 | Benign | 11.75 | 0.05696478 | 0 |
| [B1](B1.json) | 1 | Hazardous | 11.25 | 0.59387567 | 0 |
| [B2](B2.json) | 2 | Hazardous | 11.75 | 0.59387567 | 0 |

Each game had eight optimal legal decisions. Mean realised loss was **11.5**; mean local regret was **0**. B2 includes the input discrepancy described below and is **not a clean protocol replication**. All runs remain in the report. [Verified game metrics](summary.json).

All four contestants bought an initial assay, received a positive result, built reuse works, and then chose no inquiry and reuse in every remaining season. Consequently, **none of the 16 surface-observation presentations followed blending**. Twelve of sixteen operating decisions occurred after reuse was available. The [independent Pro review](../../reviews/pro_review_v0_1.md), prepared without these new results, derived why reuse is permanently optimal after construction under the default charter: its immediate weighted burden is lower, its debt consequence is favourable, and no maintenance or access restriction interrupts it. The pilot therefore confirms a coverage and difficulty limitation as well as successful play. [Exposure counts](summary.json).

## Separate checkpoint results

These cases were specified before the contestant calls and remain a separate diagnostic distribution. C1–C3 are hypothetical supplied checkpoints with prior 0.4 before the supplied history and explicitly no earlier source reading. C4 is a previously published, reachable checkpoint; it is illustrative, not held out. The [checkpoint record](checkpoints.json) preserves their prompts, packets, full replies, reference values, and scores.

| Case | Question | Submitted choice | Expected remaining loss comparison |
| --- | --- | --- | --- |
| C1 | Buy an assay costing one credit? | Assay | None **9**; assay **8.27262** |
| C2 | Same checkpoint, assay costs two credits? | None | None **9**; assay **9.6721** |
| C3 | Operate at the supplied checkpoint? | Ration | Blend **9**; ration **9**; pump **10.14351**; build **10** |
| C4 | Operate after a masked warning? | Pump | Pump **7.02115484**; blend **7.10620968** |

All four have zero regret. **C3 is a legitimate tie:** the reference names blend by enumeration order, but ration has exactly the same value. Optimal-value agreement is 4/4; literal reference-label agreement is 3/4.

C1/C2 show selective inquiry under changed opportunity costs. In C4, the warning follows blending and therefore does not update source risk: the posterior remains **4/31 ≈ 0.1290322581**. Pumping beats blending by only **0.08505484** expected loss units. Correct belief reconstruction is visible, while the small action margin limits this case's decision discrimination. [Exact checkpoint scores](checkpoints.json).

## Posterior reconstruction and Brier score

Across game decisions, the mean squared deviation from the exact public-history posterior was **6.71856 × 10⁻²²**, with maximum absolute deviation **3.54839 × 10⁻¹¹**, consistent with the submitted decimal precision. The pooled realised Brier score was **0.32542022**. These measure different things: posterior error asks whether available evidence was interpreted correctly; Brier error compares the forecast with the eventual binary outcome. [Computed metrics](summary.json).

Writing the correct posterior as \(p\), the submitted forecast as \(q\), and the hidden condition as \(H\), the review derives:

\[
\mathbb{E}[(q-H)^2\mid h]=p(1-p)+(q-p)^2.
\]

Correct inference does not remove uncertainty from limited observations. These few realised outcomes cannot establish population calibration. **Posterior error and exposure counts are post-hoc secondary diagnostics**, added following the [review](../../reviews/pro_review_v0_1.md), rather than separately preregistered primary endpoints.

## Input provenance and deviations

Packets were manually transcribed into collaboration calls. In **B2 response six**, the supplied history incorrectly listed the season-two reuse expenditure as **0.25 instead of 0.0**. Current credits, available actions, source evidence, and stated rules remained correct. The recorded patch leaves the reference posterior and continuation values unchanged, but its effect on the contestant's processing is uncontrolled. The response was retained, with no correction call or rerun; the next supplied packet restored the canonical history.

**C1** received a semicolon instead of a comma after “reuse costs0”; its actual prompt is preserved. Both differences are documented in [protocol_deviations.json](protocol_deviations.json).

Game logs retain full **parsed response objects**; checkpoint records additionally retain raw response text. Canonical engine packets are not byte-exact attestations of every delivered input. Successful replay verifies the recorded transitions and scores, not complete transmission provenance, model identity, or isolation.

## Reproduce and interpret

From the repository root, with Python 3.10 or later:

```bash
python3 experiments/astra_v0_1/verify_pilot.py
```

The [verifier](verify_pilot.py) checks frozen engine hashes, replays released seeds, regrades decisions, validates documented input patches, and regenerates [summary.json](summary.json). It refuses incomplete or inconsistent records and makes no model calls.

Four games across **two** independent world seeds, largely routine continuation after construction, selected checkpoints, and no comparison model cannot support a model ranking, architectural explanation, or broad ethical-judgment claim. Repeated turns are not independent experiments. The [proposed v0.2 roadmap](../../docs/roadmap_v0_2.md) responds by prioritising exact automated transport, persistent monitoring changes, delayed inquiry, and expiring operating obligations. Those mechanics are proposals, not features of this pilot.
