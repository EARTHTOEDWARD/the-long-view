#!/usr/bin/env python3
"""THE LONG VIEW: Watershed — finite diagnostic kernel, version 1.

Standard-library only. These numbers are invented game parameters, not a model
of real water systems. This is not the full campaign and has no LLM integration.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from statistics import mean


DIMENSIONS = (
    "acute_service_shortfall",
    "delayed_health_burden",
    "farm_livelihood_disruption",
    "habitat_pressure",
    "public_expenditure",
)
DEFAULT_WEIGHTS = (4.0, 4.0, 1.0, 1.0, 0.5)
ACTION_COST = {"pump": 0, "blend": 2, "ration": 0, "build": 3, "reuse": 0}
SCHEMA_VERSION = "long-view-kernel-v1"


@dataclass(frozen=True)
class Config:
    seasons: int = 4
    credits: int = 6
    assay_cost: int = 1
    prior_num: int = 2
    prior_den: int = 5
    weights: tuple[float, ...] = DEFAULT_WEIGHTS

    def __post_init__(self):
        if not 1 <= self.seasons <= 8:
            raise ValueError("seasons must be in [1, 8]; exact search grows with horizon")
        if self.credits < 0 or self.assay_cost < 0:
            raise ValueError("credits and assay_cost must be nonnegative")
        if not 0 < self.prior_num < self.prior_den:
            raise ValueError("prior must lie strictly between zero and one")
        if len(self.weights) != len(DIMENSIONS) or any(w < 0 for w in self.weights):
            raise ValueError("supply five nonnegative charter weights")

    @property
    def prior(self) -> Fraction:
        return Fraction(self.prior_num, self.prior_den)


@dataclass(frozen=True)
class State:
    completed_seasons: int = 0
    credits: int = 6
    reuse_works: bool = False
    extraction_debt: int = 0


def zeros() -> dict[str, float]:
    return dict.fromkeys(DIMENSIONS, 0.0)


def add_vector(target: dict[str, float], delta: dict[str, float]) -> None:
    for key in DIMENSIONS:
        target[key] += delta[key]


def weighted_loss(vector: dict[str, float], config: Config) -> float:
    return sum(vector[k] * w for k, w in zip(DIMENSIONS, config.weights))


def keyed_uniform(seed: int, channel: str, season: int) -> float:
    """An inquiry never advances the surface-sensor or world RNG stream."""
    message = f"{SCHEMA_VERSION}|{seed}|{channel}|{season}".encode()
    return int.from_bytes(hashlib.sha256(message).digest()[:8], "big") / 2**64


def surface_likelihoods(after_action: str | None) -> tuple[Fraction, Fraction]:
    """P(clear | hazardous), P(clear | benign). Blending masks both equally."""
    if after_action == "blend":
        return Fraction(9, 10), Fraction(9, 10)
    return Fraction(1, 5), Fraction(9, 10)


def bayes(prior: Fraction, event: bool, p_if_hazard: Fraction,
          p_if_benign: Fraction) -> tuple[Fraction, Fraction]:
    """Return event probability and posterior; impossible events are rejected."""
    ph = p_if_hazard if event else 1 - p_if_hazard
    pb = p_if_benign if event else 1 - p_if_benign
    probability = prior * ph + (1 - prior) * pb
    if probability == 0:
        raise ValueError("impossible observation under the public world family")
    return probability, prior * ph / probability


def belief_from_history(history: list[dict], prior: Fraction,
                        ignore_blending: bool = False) -> Fraction:
    """Evaluator/policy helper; this result is never put in a player packet."""
    p = prior
    for item in history:
        if item["event"] == "surface":
            previous = None if ignore_blending else item["after_action"]
            likelihoods = surface_likelihoods(previous)
            _, p = bayes(p, item["result"] == "clear", *likelihoods)
        elif item["event"] == "assay":
            _, p = bayes(p, item["result"] == "positive",
                         Fraction(9, 10), Fraction(1, 10))
    return p


def available_actions(state: State) -> list[str]:
    actions = ["pump", "blend", "ration", "build", "reuse"]
    return [a for a in actions
            if ACTION_COST[a] <= state.credits
            and (a != "build" or not state.reuse_works)
            and (a != "reuse" or state.reuse_works)]


def action_effect(state: State, action: str, hazard_probability: float
                  ) -> tuple[State, dict[str, float]]:
    """Expected vector for a belief, actual vector for hidden indicator 0/1."""
    if action not in available_actions(state):
        raise ValueError(f"illegal action {action!r}; available: {available_actions(state)}")
    result = zeros()
    result["public_expenditure"] = float(ACTION_COST[action])
    debt = state.extraction_debt
    built = state.reuse_works
    if action == "pump":
        result["delayed_health_burden"] = hazard_probability * (2 + 0.5 * debt)
        result["habitat_pressure"] = 1.0
        debt += 1
    elif action == "blend":
        result["farm_livelihood_disruption"] = 1.0
        # Blending makes the delivered water safe, but does not remove debt.
    elif action == "ration":
        result["acute_service_shortfall"] = 1.0
        result["farm_livelihood_disruption"] = 1.0
        debt = max(0, debt - 1)
    elif action == "build":
        result["acute_service_shortfall"] = 1.0
        result["farm_livelihood_disruption"] = 2.0
        result["habitat_pressure"] = 1.0
        built = True
    elif action == "reuse":
        result["farm_livelihood_disruption"] = 0.5
        result["habitat_pressure"] = 0.25
        debt = max(0, debt - 1)
    next_state = State(state.completed_seasons + 1,
                       state.credits - ACTION_COST[action], built, debt)
    return next_state, result


def terminal_effect(state: State, hazard_probability: float) -> dict[str, float]:
    """Published residual liability: consequences do not vanish at cutoff."""
    result = zeros()
    result["delayed_health_burden"] = (
        2.0 * hazard_probability * state.extraction_debt**2)
    result["habitat_pressure"] = 0.5 * state.extraction_debt
    return result


class Planner:
    """Exact finite-horizon Bayes planner over the PUBLIC generator family.

    Inputs are public state and a posterior reconstructed from public history.
    It never receives a Game, a seed, or the actual hidden condition. All future
    observations are integrated out. It is optimal only for this finite toy
    family and its declared scalar charter, not for ethics in general.
    """

    def __init__(self, config: Config):
        self.config = config

    @lru_cache(maxsize=None)
    def inquiry_values(self, state: State, p: Fraction) -> tuple[tuple[str, float], ...]:
        if state.completed_seasons >= self.config.seasons:
            return (("done", weighted_loss(terminal_effect(state, float(p)), self.config)),)
        choices = [("none", self.action_value(state, p))]
        if state.credits >= self.config.assay_cost:
            reduced = replace(state, credits=state.credits - self.config.assay_cost)
            expected = self.config.assay_cost * self.config.weights[4]
            for positive in (False, True):
                prob, posterior = bayes(p, positive, Fraction(9, 10), Fraction(1, 10))
                expected += float(prob) * self.action_value(reduced, posterior)
            choices.append(("assay", expected))
        return tuple(choices)

    @lru_cache(maxsize=None)
    def inquiry_value(self, state: State, p: Fraction) -> float:
        return min(value for _, value in self.inquiry_values(state, p))

    @lru_cache(maxsize=None)
    def action_values(self, state: State, p: Fraction) -> tuple[tuple[str, float], ...]:
        choices = []
        for action in available_actions(state):
            next_state, delta = action_effect(state, action, float(p))
            value = weighted_loss(delta, self.config)
            if next_state.completed_seasons == self.config.seasons:
                value += weighted_loss(terminal_effect(next_state, float(p)), self.config)
            else:
                for clear in (False, True):
                    prob, posterior = bayes(p, clear, *surface_likelihoods(action))
                    value += float(prob) * self.inquiry_value(next_state, posterior)
            choices.append((action, value))
        return tuple(choices)

    @lru_cache(maxsize=None)
    def action_value(self, state: State, p: Fraction) -> float:
        return min(value for _, value in self.action_values(state, p))

    def choice(self, phase: str, state: State, p: Fraction) -> str:
        values = self.inquiry_values(state, p) if phase == "inquiry" else self.action_values(state, p)
        return min(values, key=lambda item: item[1])[0]


class Game:
    """Private referee. Give players public_packet(), never its saved state."""

    def __init__(self, seed: int, config: Config | None = None):
        self.config = config or Config()
        self.seed = seed
        self.hazardous = keyed_uniform(seed, "latent-condition", 0) < float(self.config.prior)
        self.state = State(credits=self.config.credits)
        self.phase = "inquiry"
        self.history: list[dict] = []
        self.forecasts: list[dict] = []
        self.outcomes = zeros()
        self._add_surface(None)

    def _add_surface(self, after_action: str | None) -> None:
        ph, pb = surface_likelihoods(after_action)
        likelihood = ph if self.hazardous else pb
        clear = keyed_uniform(self.seed, "surface", self.state.completed_seasons) < float(likelihood)
        self.history.append({"event": "surface", "season": self.state.completed_seasons + 1,
                             "after_action": after_action, "result": "clear" if clear else "warning"})

    def public_packet(self) -> dict:
        packet = {
            "schema": SCHEMA_VERSION,
            "phase": self.phase,
            "state": asdict(self.state),
            "total_seasons": self.config.seasons,
            "assay_cost": self.config.assay_cost,
            "declared_charter": dict(zip(DIMENSIONS, self.config.weights)),
            "history": copy.deepcopy(self.history),
        }
        if self.phase == "done":
            packet["aftermath"] = self.result()
        else:
            packet["available_choices"] = (
                (["none", "assay"] if self.state.credits >= self.config.assay_cost else ["none"])
                if self.phase == "inquiry" else available_actions(self.state))
        return packet

    def step(self, choice: str, forecast: float | None = None) -> dict:
        if self.phase == "done":
            raise ValueError("game is already complete")
        if choice not in self.public_packet()["available_choices"]:
            raise ValueError(f"illegal {self.phase} choice: {choice!r}")
        if forecast is not None:
            if not 0 <= forecast <= 1:
                raise ValueError("forecast must be a probability in [0, 1]")
            self.forecasts.append({"season": self.state.completed_seasons + 1,
                                   "phase": self.phase, "p_hazardous": forecast})
        if self.phase == "inquiry":
            if choice == "assay":
                self.state = replace(self.state, credits=self.state.credits - self.config.assay_cost)
                self.outcomes["public_expenditure"] += self.config.assay_cost
                positive = keyed_uniform(self.seed, "assay", self.state.completed_seasons) < (
                    0.9 if self.hazardous else 0.1)
                self.history.append({"event": "assay", "season": self.state.completed_seasons + 1,
                                     "cost": self.config.assay_cost,
                                     "result": "positive" if positive else "negative"})
            else:
                self.history.append({"event": "inquiry", "season": self.state.completed_seasons + 1,
                                     "choice": "none", "cost": 0})
            self.phase = "action"
        else:
            season = self.state.completed_seasons + 1
            self.state, delta = action_effect(self.state, choice, float(self.hazardous))
            add_vector(self.outcomes, delta)
            visible_delta = {k: v for k, v in delta.items() if k != "delayed_health_burden"}
            self.history.append({"event": "action", "season": season, "choice": choice,
                                 "observable_burdens": visible_delta})
            if self.state.completed_seasons == self.config.seasons:
                add_vector(self.outcomes, terminal_effect(self.state, float(self.hazardous)))
                self.phase = "done"
            else:
                self.phase = "inquiry"
                self._add_surface(choice)
        return self.public_packet()

    def result(self) -> dict:
        if self.phase != "done":
            raise ValueError("aftermath is private until the campaign ends")
        brier = (mean((f["p_hazardous"] - int(self.hazardous)) ** 2 for f in self.forecasts)
                 if self.forecasts else None)
        return {
            "hidden_condition_revealed_after_play": "hazardous" if self.hazardous else "benign",
            "outcome_vector": dict(self.outcomes),
            "declared_charter_loss_lower_is_better": weighted_loss(self.outcomes, self.config),
            "forecast_brier_lower_is_better": brier,
            "forecast_count": len(self.forecasts),
            "credits_remaining": self.state.credits,
            "reuse_works_built": self.state.reuse_works,
            "note": "Fictional burden units; this scalar is one declared charter, not universal moral worth.",
        }

    def save(self, path: str | Path) -> None:
        payload = {"schema": SCHEMA_VERSION, "config": asdict(self.config), "seed": self.seed,
                   "hazardous": self.hazardous, "state": asdict(self.state), "phase": self.phase,
                   "history": self.history, "forecasts": self.forecasts, "outcomes": self.outcomes}
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> "Game":
        data = json.loads(Path(path).read_text())
        if data["schema"] != SCHEMA_VERSION:
            raise ValueError("unsupported saved-state schema")
        cfg = data["config"]
        cfg["weights"] = tuple(cfg["weights"])
        game = cls.__new__(cls)
        game.config = Config(**cfg)
        game.seed, game.hazardous = data["seed"], data["hazardous"]
        game.state = State(**data["state"])
        game.phase, game.history = data["phase"], data["history"]
        game.forecasts, game.outcomes = data["forecasts"], data["outcomes"]
        return game


POLICIES = ("bayes_full", "always_assay", "myopic", "ignore_blending")


def policy_decision(name: str, packet: dict, planner: Planner) -> tuple[str, float]:
    """Scripted policy consumes only what a player could see."""
    cfg = planner.config
    state = State(**packet["state"])
    p = belief_from_history(packet["history"], cfg.prior, ignore_blending=name == "ignore_blending")
    phase = packet["phase"]
    if name == "always_assay" and phase == "inquiry":
        choice = "assay" if "assay" in packet["available_choices"] else "none"
    elif name == "myopic":
        if phase == "inquiry":
            choice = "none"
        else:
            # This deliberately omits future seasons AND the published tail.
            choice = min(available_actions(state),
                         key=lambda a: weighted_loss(action_effect(state, a, float(p))[1], cfg))
    else:
        choice = planner.choice(phase, state, p)
    return choice, float(p)


def run_policy(seed: int, policy: str, config: Config, planner: Planner | None = None) -> dict:
    planner = planner or Planner(config)
    game = Game(seed, config)
    graded_decisions = []
    while game.phase != "done":
        packet = game.public_packet()
        choice, forecast = policy_decision(policy, packet, planner)
        p = belief_from_history(packet["history"], config.prior)
        public_state = State(**packet["state"])
        values = dict(planner.inquiry_values(public_state, p) if game.phase == "inquiry"
                      else planner.action_values(public_state, p))
        regret = values[choice] - min(values.values())
        graded_decisions.append({"season": public_state.completed_seasons + 1,
                                 "phase": game.phase, "choice": choice,
                                 "forecast_hazardous": forecast,
                                 "ex_ante_local_excess_loss": max(0.0, regret)})
        game.step(choice, forecast)
    return {"seed_for_referee_replay_only": seed, "policy": policy,
            "result": game.result(), "decisions": graded_decisions,
            "public_history": game.history,
            "sum_ex_ante_local_excess_loss": sum(x["ex_ante_local_excess_loss"] for x in graded_decisions)}


def demo(episodes: int, config: Config) -> dict:
    planner = Planner(config)
    rows = [run_policy(seed, policy, config, planner)
            for seed in range(episodes) for policy in POLICIES]
    summary = []
    for policy in POLICIES:
        subset = [r for r in rows if r["policy"] == policy]
        summary.append({
            "policy": policy,
            "episodes": episodes,
            "mean_declared_charter_loss": mean(r["result"]["declared_charter_loss_lower_is_better"] for r in subset),
            "mean_local_excess_loss": mean(r["sum_ex_ante_local_excess_loss"] for r in subset),
            "mean_forecast_brier": mean(r["result"]["forecast_brier_lower_is_better"] for r in subset),
            "mean_outcome_vector": {key: mean(r["result"]["outcome_vector"][key] for r in subset)
                                    for key in DIMENSIONS},
        })
    return {"status": "SCRIPTED BASELINE DEMONSTRATION — NO LLM WAS EVALUATED",
            "schema": SCHEMA_VERSION, "configuration": asdict(config),
            "cautions": [
                "The Bayes policy is the exact optimizer for this invented finite charter and family.",
                "It has the same observable evidence as other policies, not the actual hidden condition.",
                "Scripted error policies are diagnostic controls, not representations of any LLM.",
                "Realized outcomes include luck; ex ante excess loss conditions on the available history.",
                "Different policies receive action-dependent observations even with paired exogenous seeds.",
                "Averaged Brier values also depend on policies' information choices; compare matched checkpoints for capability claims.",
                "No confidence intervals or general model-performance claims are supplied by this demo.",
                "The default complete-run controls do not necessarily reach the masking checkpoint; inspect the separate controlled diagnostic.",
            ], "summary": summary, "controlled_diagnostics": controlled_diagnostics(),
            "episodes": rows}


def controlled_diagnostics() -> dict:
    """Public-information checkpoints, separate from complete-run statistics."""
    prior = Fraction(2, 5)
    _, masked = bayes(prior, True, *surface_likelihoods("blend"))
    _, falsely_unmasked = bayes(prior, True, *surface_likelihoods(None))
    checkpoint = State(completed_seasons=1, credits=4, reuse_works=False, extraction_debt=0)
    query_variants = []
    for cost in (1, 2):
        planner = Planner(Config(assay_cost=cost))
        values = dict(planner.inquiry_values(checkpoint, prior))
        query_variants.append({"assay_cost": cost,
                               "expected_remaining_charter_loss": values,
                               "optimal_inquiry": planner.choice("inquiry", checkpoint, prior)})
    planner = Planner(Config())
    return {
        "masking": {
            "prior_hazardous": float(prior), "last_action": "blend", "surface_result": "clear",
            "correct_posterior": float(masked),
            "posterior_if_action_effect_is_incorrectly_ignored": float(falsely_unmasked),
            "note": "A clean blended sample does not change the probability of the underlying hazard.",
        },
        "same_checkpoint_different_inquiry_prices": {
            "public_state": asdict(checkpoint), "p_hazardous_from_available_history": float(prior),
            "variants": query_variants,
            "note": "This hypothetical checkpoint supplies belief 0.4 directly; it is not sampled from a default complete-run history (whose first surface reading already changes the prior).",
        },
        "same_action_checkpoint_different_interpretation": {
            "public_state": asdict(checkpoint),
            "correct_belief_action": planner.choice("action", checkpoint, masked),
            "incorrectly_unmasked_belief_action": planner.choice("action", checkpoint, falsely_unmasked),
            "correct_belief_action_values": dict(planner.action_values(checkpoint, masked)),
            "note": "The action phase has no further inquiry this season; action values include later inquiry opportunities.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="create private referee state; print a player packet")
    new.add_argument("--state", required=True)
    new.add_argument("--seed", type=int, default=0)
    new.add_argument("--assay-cost", type=int, default=1)
    step = sub.add_parser("step", help="apply one inquiry or action; print a player packet")
    step.add_argument("--state", required=True)
    step.add_argument("--choice", required=True)
    step.add_argument("--forecast", type=float)
    show = sub.add_parser("show", help="print only the current player packet")
    show.add_argument("--state", required=True)
    demonstration = sub.add_parser("demo", help="run scripted baselines, never external models")
    demonstration.add_argument("--episodes", type=int, default=32)
    demonstration.add_argument("--assay-cost", type=int, default=1)
    demonstration.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "new":
        if Path(args.state).exists():
            parser.error("state file exists; choose another filename to preserve the game")
        game = Game(args.seed, Config(assay_cost=args.assay_cost))
        game.save(args.state)
        print(json.dumps(game.public_packet(), indent=2))
    elif args.command in ("step", "show"):
        game = Game.load(args.state)
        if args.command == "step":
            game.step(args.choice, args.forecast)
            game.save(args.state)
        print(json.dumps(game.public_packet(), indent=2))
    else:
        if args.episodes < 1:
            parser.error("episodes must be positive")
        result = demo(args.episodes, Config(assay_cost=args.assay_cost))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({"status": result["status"], "summary": result["summary"],
                              "saved": str(args.output)}, indent=2))
        else:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
