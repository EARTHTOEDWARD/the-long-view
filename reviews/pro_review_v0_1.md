# Independent review of The Long View v0.1

**Date:** 6 November 2026  
**Reviewer configuration:** independent task instance inheriting the parent session's GPT-6 Astra Pro configuration. The delegation contract inherits its model and reasoning settings; no separate API model-ID attestation or per-inference dollar telemetry was provided. This is an assessment of the design, not a comparison of model performance.  
**Review boundary:** the supplied design, public player rules, engine, tests, and existing scripted demonstrations. Newly commissioned Astra play results were not inspected in preparing this review. The engine and baseline were not modified.

## Assessment

**The programme is worth developing. The present executable game is a sound, small calibration environment, but it does not yet test the most ambitious capability described in the design.** It evaluates planning and Bayesian updating in a fully specified, four-season decision problem. The larger proposal concerns sustained inquiry through changing evidence, obligations, and institutions. Those are related targets, but their relationship needs to be demonstrated by the next version.

The best feature is action-dependent evidence: an intervention changes the observation channel, so a reassuring or alarming reading can become uninformative. The best evaluation choice is the same-information reference planner: its decisions are evaluated under the uncertainty available to the contestant, rather than against knowledge of the realised hidden world.

The most consequential weaknesses are concrete:

1. **The default campaign rarely exposes the headline mechanism.** In the saved exact-policy sample, there is no surface observation after blending. The sole blend operation occurs in the final season.
2. **Building reuse works ends the substantive decision problem under the default charter.** Reuse then outperforms all other available operations, and further information about the hazard cannot improve the chosen policy.
3. **The implemented ethical problem has already been resolved into a public weighted objective.** That is appropriate for a competence test under a mandate, but it does not yet test deliberation over incompatible goods, consent, institutional revision, or an unresolved moral remainder.

A small Astra run is therefore useful now as a **mechanics and interface baseline**. It can reveal mistakes, near-optimal play, and saturation. It cannot establish a long-horizon reasoning advantage or rank models in ethical judgment. Preserve its results even if performance is perfect: saturation would be evidence about this version's difficulty.

## 1. What is already good

### The causal structure is inspectable

The game has a persistent hazardous or benign source condition, an explicit prior, a noisy surface observation, a paid assay, and a finite set of operations. In `engine.py`, `surface_likelihoods()` correctly gives the same probability of a clear reading in both hidden conditions after blending. Both a clear and a warning reading are therefore uninformative in that circumstance.

The possibility of an uninformative warning is especially valuable. The benchmark can reward accurate causal interpretation without encoding a universal preference for reassurance or precaution.

### Inquiry has a real opportunity cost

An assay both contributes to declared expenditure and reduces the credits available for later operations. Those are distinct, legitimate roles for the same resource. The code and player brief disclose both. A test that reduces uncertainty can still be a poor decision.

The saved demonstration supplies an instructive example: always buying an affordable assay improves the average forecast score while increasing average charter loss. This is a result from the scripted sample, not a theorem that inquiry generally reduces welfare and not an observation about any LLM.

### The reference does not cheat

`Planner` takes public state and a posterior reconstructed from public observations. Its recursion averages over future signals; it does not receive the actual condition or world seed. This is the right reference for the known-generator track.

The public likelihood family is part of the rules. A contestant can in principle reproduce the planner. That is useful for calibration. A tools-allowed model that writes an equivalent solver has performed the permitted task successfully; it should not be penalised for doing so. A separate tools-restricted condition can study direct reasoning, with the distinction made explicit.

### The implementation anticipates several common evaluation failures

The private state and public packet are separate; histories returned to players are copied; invalid unaffordable actions do not partially mutate the game; saved games resume faithfully; terminal liabilities do not disappear at the cutoff; and random draws are keyed to event channels rather than shifted by extra queries.

I reran the existing fourteen semantic tests. All passed. I found no critical transition or default-scoring defect in the reviewed path. This statement concerns the implemented finite model, not a certification of every future configuration or deployment.

## 2. What the existing evidence actually shows

The following counts were recomputed from the saved `demo_scripted_results.json`. They concern 64 worlds played by the exact scripted policy.

| Observation | Count | Implication |
|---|---:|---|
| Games that build reuse works in season 1 | 31 of 64 | Nearly half enter a simple continuation immediately |
| Later reuse operations | 93 | Exactly three for each of those 31 games |
| Blending operations | 1 | Blending is rare under the tested charter |
| Blending before the final season | 0 | No later observation tests its masking effect in these optimal runs |
| Pumping operations | 130 | Much of the remaining policy is repeated source use |
| Rationing operations | 1 | Another meaningful alternative is almost absent from this sample |

The sole blend occurs in season 4 of the saved seed 61 run. There is no next surface observation. Consequently, the identical scores of the exact and `ignore_blending` controls are an exposure limitation: that sample gives the introduced error no occasion to affect later belief.

The separately supplied belief-0.4 checkpoint and the later reachable checkpoint do test the mechanism. Their status is already disclosed appropriately. They should remain separate from full-campaign statistics. A selected demonstration is evidence that the mechanism exists, not evidence that an ordinary campaign reliably measures it.

### Why the post-construction simplification is structural

Under the default weights, reuse costs 0.75 loss units per season: 0.5 from farm disruption and 0.25 from habitat pressure. It costs no credits and reduces extraction debt by one.

Once the works exist:

| Alternative | Immediate default-charter loss | Debt consequence relative to reuse |
|---|---:|---|
| Reuse | 0.75 | Reduces debt by one |
| Ration | 5 | Same debt reduction |
| Blend | 2 | Leaves debt unchanged and spends two credits |
| Pump | At least 1 | Increases debt and can add delayed health burden |

Reuse therefore improves the immediate scalar objective and leaves a continuation at least as favourable as every alternative. It can be repeated without maintenance, resource, permission, or capacity limits. By backward induction, reuse is optimal for every remaining season under the default charter. Further hazard information cannot change that choice.

This is **charter-dependent scalar dominance**, not a claim that reuse dominates every outcome dimension or every possible charter. For example, pumping has less farm disruption. It is nevertheless sufficient to collapse this default continuation.

## 3. What the game currently measures

The implemented problem has a small sufficient description:

\[
(t,\;\text{credits},\;\text{works built},\;\text{debt},\;P(H\mid h_t)).
\]

Once that description is correct, the full earlier history has no further effect on the optimal decision. Most state variables are already supplied in each packet; only the posterior needs reconstruction from the short history. The observation packet also explicitly names the action responsible for each surface reading.

That is a legitimate task. Compressing history into a useful sufficient state is itself a capability. But a four-season, binary-hidden-state problem with all mechanisms and numerical tradeoffs supplied gives limited room to distinguish sophisticated sustained reasoning from careful calculation.

Several ambitions belong to the design rather than the current implementation:

| Intended capability | Current support |
|---|---|
| Correctly interpret intervention-dependent evidence | Implemented, but poorly exposed in ordinary optimal play |
| Buy information selectively | Implemented |
| Invest for a later operation | Implemented, with a strong absorbing continuation |
| Maintain a consequential commitment | Not implemented |
| Revise through a legitimate consent procedure | Not implemented |
| Preserve a service while changing its institution | Not implemented |
| Discover or revise an unknown causal mechanism | Not implemented; the finite generator is supplied |
| Retain a distinction across a long, changing inquiry | Proposed; the current history is short and highly scaffolded |
| Deliberate where a moral ordering remains unresolved | Proposed; the prototype supplies a scalar ordering |

The public description should retain this distinction. Avoid calling a high score on the kernel a demonstration of broad ethical intelligence, long-horizon research competence, or Pro superiority.

## 4. Ethics: a good foundation that still needs a real mechanism

A public charter is preferable to hidden moral weights. It makes the competence question reproducible: did the model understand the mandate and choose well under it? Multiple charters can legitimately prefer different actions in the same physical world.

However, the existing dimensions are broad burden categories, and the scalar ordering resolves all their tradeoffs in advance. There is no implemented participant who can withhold consent, retain a right after an emergency, be owed a remedy, or reject compensation. Public decision prose cannot add those features to the engine.

The next ethical addition should therefore be an actual rule governing a relationship. A land-access agreement is a suitable first choice: it enables a later operation, has a finite permission or duration, creates an obligation, and can require renewal or a defined emergency exception. This would make an earlier decision consequential in a later dilemma without requiring a simulated society of many autonomous characters.

The game can still have exact scoring under a stated charter. A separate deliberation track should preserve disagreements that the charter leaves open. Do not turn reviewer preferences about graceful prose into a substitute moral answer key.

## 5. A useful improvement to the forecast metrics

Raw Brier scores mix two effects: how much information a policy acquired, and how well it interpreted the information it had. The current demonstration already shows why that distinction matters.

For a binary hidden condition, let \(p=P(H=1\mid h)\) be the correct public-history posterior and \(q\) the model's forecast. Then:

\[
\mathbb E[(q-H)^2\mid h]
=p(1-p)+(q-p)^2.
\]

The first term is uncertainty remaining in the evidence. The second is avoidable forecast error relative to that evidence.

**Report \((q-p)^2\) alongside realised Brier score in the known-generator track.** It separates belief reconstruction from information acquisition. A model may rationally stop buying tests when no action can benefit, retain high uncertainty, and still interpret its evidence perfectly.

This measure is available exactly in the present kernel. It does not carry over unchanged to an open-world task with unknown laws and no justified reference posterior. There, reference-model uncertainty must also be reported.

Action regret needs similar care. Near-tied legal actions should receive their small actual regret, not a binary failure for disagreeing with the oracle's tie-breaking. Public explanations can help diagnose a mistake, but they should not overwrite the choice's measured consequences.

## 6. A focused v0.2: a temporary operating compact

I recommend one joined extension before a large civic simulation: **an emergency operating arrangement that changes monitoring, grants temporary access, and later needs renewal**.

The aim is to make the game's central relation recur: an early intervention changes what later evidence means and what later actions are legitimate or feasible. These proposed mechanics are not yet validated or implemented.

### A. Make the monitoring change persist

Replace the one-step dependence on the previous operation with a public monitoring configuration \(m_t\). An emergency buffer installation moves a named sensor to a treated-water store. Its measurements then remain weakly informative or uninformative about the upstream source until a crew restores source sampling.

The public observation model specifies the likelihoods conditional on the monitoring configuration. The history records the installation and any restoration. Ordinary sensor packets contain the sensor identity and reading. An additional diagnostic arm can supply the current monitoring configuration explicitly.

This permits a clean comparison between reconstructing the configuration from earlier events and planning after a sufficient state is supplied. The model receives complete accessible evidence in both arms; the difference is whether that evidence has already been compiled into the current causal state.

### B. Give the delayed inquiry a deadline that matters

A source assay consumes money and one work slot, and returns after a declared number of operational decisions. Store its target, sample time, and due time in a pending-investigation ledger. An investment or renewal decision has a fixed deadline.

The model must sometimes order the assay before the importance of its result becomes immediate. Other worlds should make the assay unnecessary or too late. The latency and deadline must follow the rules; the referee should not retrospectively create urgency to reward a favoured choice.

Initially keep the source condition fixed so that the larger state remains inspectable. A later version can let physical intervention change that condition, at which point sample dates and changing mechanisms become additional scientific questions.

### C. Give reuse a real prerequisite that can expire

Construction supplies a works asset, but operation also needs an access compact. A small candidate state is a remaining-use permission \(k_t\), initially two after an agreed construction. Each reuse operation consumes one permission. Renewal costs a work slot and a declared payment or compensating action. The compact records who accepted which burden and what remedy was promised.

This interrupts the present rule that construction makes every later operational choice routine. The asset can survive while access to its use changes.

Choose an explicit public procedure for exceptional use when permission is exhausted. One charter can require renewal; another can permit a narrowly defined emergency use accompanied by a recorded remedy. Physically possible but unauthorised acts should be represented distinctly from physically impossible ones, so a violation can be observed rather than silently removed from consideration.

The numerical costs and permission lengths above are candidate starting parameters. They need calibration against reference policies and scenario coverage. They are not evidence that two uses is a natural or morally preferred limit.

### D. Keep the extension small enough to understand

A candidate state is the existing resource/asset/debt state plus monitoring configuration, pending assay, permission count, and outstanding obligation. Start with six seasons and two public charters. Use a finite source-state family so a reference remains possible. If exact enumeration becomes expensive, state the approximation rather than continuing to call it exact.

This extension can create a coherent sequence:

1. Establish a temporary operating arrangement to meet an emergency.
2. Receive readings from the monitoring configuration it created.
3. Order or decline information before an investment or renewal deadline.
4. Use the arrangement while consuming its permission and imposing a known burden.
5. Confront a later shortage after permission expires.
6. Renew, revise, replace, or exceptionally extend the arrangement under the mandate.

Some worlds must favour renewing the original arrangement; others should favour replacement. Preserving the institution or increasing cooperation should not be the universal solution.

## 7. Make scenario coverage a property of the benchmark

Before comparing model rankings, audit the generated worlds against targeted control policies.

For every claimed capability, record:

- Whether a relevant decision was reached.
- Whether correct and ablated interpretations change a feasible continuation.
- The expected loss gap between those continuations under the public information.
- Whether a simpler policy already solves the case.

A masking probe with no later observation has zero exposure. A probe whose actions are nearly tied has little decision-discrimination power even if its posterior calculation is revealing. Both can remain useful diagnostics, but should not inflate the number of substantive dilemmas encountered.

Use controls such as ignoring a monitoring change, treating a late test as timely, forgetting an access condition, or always preserving the original institution. Generate and freeze coverage-balanced worlds using those mechanism-specific controls before inspecting the candidate LLM ranking.

Do not make every episode a trap. Include matched worlds in which the new evidence really is diagnostic, an old commitment really should be maintained, and further inquiry really is wasteful. Failure on those counterparts detects an equally shallow habit of suspicion or reversal.

## 8. What the immediate Astra baseline can establish

Keep v0.1 frozen during the first run. Do not incorporate this review's changes while contestants are playing.

Four complete games and four diagnostic decisions can answer useful operational questions:

- Can Astra follow the two-phase interface and produce valid actions?
- Does it reconstruct the short public history's posterior?
- Does it value assays selectively?
- Does it plan beyond the current season and include the terminal liability?
- Do the selected diagnostic checkpoints actually distinguish the target error?

The following should be recorded for every submitted decision: exact public input, returned action, hazard forecast, concise public explanation, validity, reference posterior, action values, local regret, and elapsed time. Preserve raw model outputs. Do not repair or coach selectively. Report protocol deviations.

Use fresh contestant instances without the design review, source implementation, reference results, prior game outcomes, or hidden referee files. If access is restricted only by instruction rather than an enforced sandbox, label the run accordingly.

Distinguish three budgets: the game's resource credits, the number of model decisions and permitted tools, and paid inference expenditure. A limit on decision count is enforceable in an in-session run. Without billing telemetry it is not a dollar cap. Record unavailable usage fields as unavailable.

The four games are an exploratory baseline. They do not supply a population ranking or a power calculation. Paired worlds help, but repeated turns within one world are not independent experiments. A later comparison should preregister the number of independent world families and reruns using a pilot-based variance estimate and a minimum relevant effect.

## 9. Three priorities

| Priority | Change | Why it comes first | Cost and risk |
|---|---|---|---|
| **1. Make exposure and reconstruction observable** | Add per-mechanism exposure counts, exact posterior forecast error, reachable checkpoint manifests, and exact input/output provenance | Prevents a favourable score from standing in for a capability that the run never exercised | Low implementation cost; the risk is overusing selected checkpoints as if they were ordinary-play statistics |
| **2. Implement the temporary operating compact** | Persistent monitoring configuration, delayed assay, and expiring access/renewal obligation | Makes an early intervention consequential several decisions later and prevents permanent reuse from ending the inquiry | Moderate engine and reference-planner work; state-space growth and contrived balance need inspection |
| **3. Run a controlled depth comparison** | Connected versus independent cases; full history versus sufficient-state summary; multiple charters; documented inference budgets | Tests the specific sustained-understanding hypothesis and locates the source of any advantage | Moderate experiment cost; narrative difficulty, context length, tools, and provider state can confound the result |

A multiplayer council, richly simulated ecology, open-ended invention parser, and large public leaderboard can wait. They would increase production complexity and introduce additional measurement ambiguity before the core capability has been isolated.

## 10. Engineering details to resolve before broader runs

The public packet omits the prior and relies on a separate player brief containing fixed defaults. `Config` nevertheless permits alternate priors and horizons. That is consistent for the current default run, but future configurable runs could accidentally give the reference more information than the player. Generate a versioned public rules/configuration manifest from the same source used by the referee; include its identifier with each packet.

Retain separate locations or access controls for public rules, contestant notebooks, private world state, and evaluator outputs. File naming alone does not isolate a contestant that has general filesystem access.

The current default terminal penalty is public and consistently implemented, but it is a stipulated finite model. Add sensitivity checks before drawing behavioural conclusions that depend on it. A late action can be attractive because of the cutoff, even when all explicit liabilities are counted; the absence of a salvage value for built works is also a declared modelling choice.

Preserve v0.1 as a versioned reference. New results should identify engine version, rules version, charter, world family, selection procedure, model configuration, and budget. Publish demonstration seeds after use; keep confirmatory holdouts separate until the evaluation is complete.

## Conclusion

The design's strongest idea survives this review: **a model's earlier intervention can change the meaning of its later evidence and the conditions of its later obligations**. That supplies a coherent route to evaluating sustained judgment without requiring deception.

The immediate advance should be to make that relation recur in a small complete episode. A persistent monitoring change and a temporary operating compact would turn an early response into a later dilemma whose solution depends on acquired understanding. This is a more informative next step than merely adding more seasons to the current rules.

### Evidence status and reviewed sources

- **Inspected:** `engine.py`, especially `surface_likelihoods`, `belief_from_history`, `Planner`, `Game`, and `run_policy`; `PLAYER_BRIEF.txt`; the v1 design document; `test_engine.py`; `demo_scripted_results.json`; and the documented checkpoint status.
- **Recomputed:** action counts in the 64-world exact-policy demonstration and the timing of its blending operation.
- **Executed:** the existing fourteen semantic tests, all passing.
- **Derived:** post-construction default-charter dominance of reuse; conditional decomposition of Brier loss.
- **Proposed:** all v0.2 changes and the broader controlled evaluation.
- **Not established:** any model superiority, any architectural explanation, broad moral competence, or reliable long-horizon discrimination by v0.1.

No external literature services or paid API calls were used. Private source attachments and newly requested contestant-result files were not opened for this review.
