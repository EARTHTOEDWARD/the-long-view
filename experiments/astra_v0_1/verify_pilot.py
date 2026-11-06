#!/usr/bin/env python3
"""Replay and regrade the complete, fixed 36-response Astra v0.1 pilot.

Run from the repository root:
    python3 experiments/astra_v0_1/verify_pilot.py

Only the Python standard library and this repository's frozen engine are used.
No model calls are made. Missing, partial, or inconsistent records cause a
nonzero exit, without writing a new summary. Verification concerns canonical
engine replay, not independent attestation of the bytes delivered to a model.
Known input discrepancies are checked and retained separately.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))
from the_long_view.engine import (  # noqa: E402
    Config, DIMENSIONS, Game, Planner, State, available_actions,
    belief_from_history,
)

EPISODES = ("A1", "A2", "B1", "B2")
CASES = ("C1", "C2", "C3", "C4")
SCORE_ABS_TOL = 1e-12
SCORE_REL_TOL = 1e-10
OPTIMAL_ABS_TOL = 1e-9
SECONDARY_NOTE = (
    "Posterior reconstruction error and mechanism-exposure counts are post-hoc "
    "secondary diagnostics added following the independent review. They were "
    "not separately preregistered primary endpoints."
)


class VerificationError(Exception):
    """A missing or inconsistent public record."""


def require(condition, message):
    # Do not use Python assert: verification must also work under python -O.
    if not condition:
        raise VerificationError(message)


def same(actual, expected, path):
    """Compare structures exactly and computed floats with a stated tolerance."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict), f"{path}: expected an object")
        require(actual.keys() == expected.keys(), f"{path}: object fields differ")
        for key, value in expected.items():
            same(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list), f"{path}: expected an array")
        require(len(actual) == len(expected), f"{path}: array length differs")
        for index, (left, right) in enumerate(zip(actual, expected)):
            same(left, right, f"{path}[{index}]")
    elif isinstance(expected, float):
        require(type(actual) in (int, float) and math.isfinite(actual),
                f"{path}: expected a finite number")
        require(math.isclose(actual, expected, rel_tol=SCORE_REL_TOL,
                             abs_tol=SCORE_ABS_TOL),
                f"{path}: recorded {actual!r}, recomputed {expected!r}")
    else:
        require(type(actual) is type(expected) and actual == expected,
                f"{path}: recorded {actual!r}, expected {expected!r}")


class Inputs:
    """Keep an immutable snapshot and hashes of all consulted public files."""

    def __init__(self):
        self.data = {}

    def read(self, path):
        path = path.resolve()
        if path not in self.data:
            try:
                self.data[path] = path.read_bytes()
            except OSError as exc:
                raise VerificationError(f"Cannot read {path.relative_to(REPO)}: {exc}") from exc
        return self.data[path]

    def json(self, path):
        try:
            return json.loads(self.read(path))
        except (ValueError, UnicodeError) as exc:
            raise VerificationError(f"Invalid JSON in {path.relative_to(REPO)}: {exc}") from exc

    def digest(self, path):
        return hashlib.sha256(self.read(path)).hexdigest()

    def hashes(self):
        return {str(path.relative_to(REPO)): hashlib.sha256(data).hexdigest()
                for path, data in sorted(self.data.items())}

    def check_unchanged(self):
        for path, data in self.data.items():
            require(path.read_bytes() == data,
                    f"{path.relative_to(REPO)} changed during verification; rerun")


def config_for_packet(packet):
    return Config(seasons=packet["total_seasons"], assay_cost=packet["assay_cost"],
                  weights=tuple(packet["declared_charter"][d] for d in DIMENSIONS))


def reference(packet, planner):
    state = State(**packet["state"])
    phase = packet["phase"]
    require(phase in ("inquiry", "action"), "A decision packet must have an active phase")
    choices = ((["none", "assay"] if state.credits >= planner.config.assay_cost else ["none"])
               if phase == "inquiry" else available_actions(state))
    same(packet["available_choices"], choices, "packet.available_choices")
    posterior = belief_from_history(packet["history"], planner.config.prior)
    values = dict(planner.inquiry_values(state, posterior) if phase == "inquiry"
                  else planner.action_values(state, posterior))
    return posterior, values


def forecast_or_none(response):
    """Use the same acceptance rule as the frozen referee session helper."""
    value = response.get("forecast_hazardous")
    return value if isinstance(value, (int, float)) and 0 <= value <= 1 else None


def grade(record, packet, planner, location, word_limit, regret_field):
    response = record["response"] if isinstance(record["response"], dict) else {}
    valid = response.get("choice") in packet["available_choices"]
    applied = response["choice"] if valid else ("none" if packet["phase"] == "inquiry" else "ration")
    forecast = forecast_or_none(response)
    posterior, values = reference(packet, planner)
    best_value = min(values.values())
    optimal_choices = [choice for choice, value in values.items()
                       if math.isclose(value, best_value, rel_tol=0, abs_tol=OPTIMAL_ABS_TOL)]
    reference_label = min(values, key=values.get)
    regret = values[applied] - best_value
    words = len(str(response.get("brief_reason", "")).split())
    recomputed = {
        "applied_choice": applied, "valid_choice": valid,
        "correct_public_posterior": float(posterior),
        "reference_action": reference_label, "reference_values": values,
        regret_field: regret, "public_reason_words": words,
    }
    for key, value in recomputed.items():
        same(record[key], value, f"{location}.{key}")
    posterior_error = None if forecast is None else forecast - float(posterior)
    return {
        "applied_choice": applied, "forecast": forecast, "valid_choice": valid,
        "optimal_choice": valid and applied in optimal_choices,
        "optimal_choices": optimal_choices,
        "reference_label_match": valid and applied == reference_label,
        "reference_action": reference_label, "reference_values": values,
        "posterior": float(posterior), "posterior_fraction": str(posterior),
        "posterior_squared_error": None if posterior_error is None else posterior_error ** 2,
        "posterior_absolute_error": None if posterior_error is None else abs(posterior_error),
        "regret": regret, "reason_words": words,
        "reason_word_limit_exceeded": words > word_limit,
    }


def exposure(history):
    """Count each observation once, from one final history rather than packets."""
    surfaces = [item for item in history if item["event"] == "surface"]
    require(len({item["season"] for item in surfaces}) == len(surfaces),
            "A history repeats a surface observation within the same season")
    masked = [item for item in surfaces if item["after_action"] == "blend"]
    unmasked = [item for item in surfaces if item["after_action"] != "blend"]
    assays = [item for item in history if item["event"] == "assay"]
    actions = [item for item in history if item["event"] == "action"]
    return {
        "surface_observations": len(surfaces),
        "masked_surface_observations": len(masked),
        "masked_clear": sum(item["result"] == "clear" for item in masked),
        "masked_warning": sum(item["result"] == "warning" for item in masked),
        "unmasked_surface_observations": len(surfaces) - len(masked),
        "unmasked_clear": sum(item["result"] == "clear" for item in unmasked),
        "unmasked_warning": sum(item["result"] == "warning" for item in unmasked),
        "assay_observations": len(assays),
        "positive_assays": sum(item["result"] == "positive" for item in assays),
        "negative_assays": sum(item["result"] == "negative" for item in assays),
        **{action + "_operations": sum(item["choice"] == action for item in actions)
           for action in ("pump", "blend", "ration", "build", "reuse")},
    }


def decision_totals(grades):
    squared = [g["posterior_squared_error"] for g in grades if g["forecast"] is not None]
    absolute = [g["posterior_absolute_error"] for g in grades if g["forecast"] is not None]
    return {
        "decisions": len(grades),
        "valid_decisions": sum(g["valid_choice"] for g in grades),
        "invalid_decisions": sum(not g["valid_choice"] for g in grades),
        "optimal_choice_matches": sum(g["optimal_choice"] for g in grades),
        "reference_label_matches": sum(g["reference_label_match"] for g in grades),
        "sum_local_excess_expected_loss": sum(g["regret"] for g in grades),
        "valid_forecasts": len(squared),
        "max_public_reason_words": max((g["reason_words"] for g in grades), default=0),
        "reason_word_limit_violations": sum(g["reason_word_limit_exceeded"] for g in grades),
        "post_hoc_mean_posterior_squared_error": mean(squared) if squared else None,
        "post_hoc_max_posterior_absolute_error": max(absolute) if absolute else None,
    }


def verify_game(episode, log, protocol):
    same(log["episode"], episode, f"{episode}.episode")
    same(log["model"], protocol["model_requested"], f"{episode}.model")
    same(log["reasoning_effort"], protocol["reasoning_effort_requested"], f"{episode}.reasoning_effort")
    require(len(log["steps"]) == 8, f"{episode}: expected exactly eight decisions")
    seed = log["referee_seed_released_after_completion"]
    require(type(seed) is int, f"{episode}: released seed must be an integer")
    cost = log["steps"][0]["packet"]["assay_cost"]
    same(cost, 1 if episode.endswith("1") else 2, f"{episode}.assay_cost")
    config = Config(assay_cost=cost)
    game, planner = Game(seed, config), Planner(config)
    grades = []
    for index, record in enumerate(log["steps"]):
        location = f"{episode}.steps[{index}]"
        same(record["packet"], game.public_packet(), f"{location}.canonical_packet")
        g = grade(record, record["packet"], planner, location,
                  protocol["budget"]["public_reason_word_limit"], "excess_expected_loss")
        grades.append(g)
        game.step(g["applied_choice"], g["forecast"])
    require(game.phase == "done", f"{episode}: replay did not reach the terminal state")
    same(log["result"], game.result(), f"{episode}.result")
    same(log["sum_local_excess_expected_loss"], sum(g["regret"] for g in grades),
         f"{episode}.sum_local_excess_expected_loss")
    if "final_packet" in log:
        same(log["final_packet"], game.public_packet(), f"{episode}.final_packet")
    if "public_history" in log:
        same(log["public_history"], game.history, f"{episode}.public_history")
    result = game.result()
    row = {
        "episode": episode, "world_pair": episode[0], "assay_cost": cost,
        "released_seed": seed,
        "revealed_condition": result["hidden_condition_revealed_after_play"],
        "realised_charter_loss": result["declared_charter_loss_lower_is_better"],
        "outcome_vector": result["outcome_vector"],
        "forecast_brier": result["forecast_brier_lower_is_better"],
        "final_state": asdict(game.state),
        "inquiry_sequence": [grades[i]["applied_choice"] for i in range(0, 8, 2)],
        "operation_sequence": [grades[i]["applied_choice"] for i in range(1, 8, 2)],
        **decision_totals(grades),
        "post_hoc_exposure": exposure(game.history),
        "post_hoc_action_decisions_with_reuse_available": sum(
            record["packet"]["phase"] == "action" and record["packet"]["state"]["reuse_works"]
            for record in log["steps"]),
    }
    return row, grades


def expected_supplied_packet(case_id):
    packet = {
        "schema": "long-view-kernel-v1", "phase": "action" if case_id == "C3" else "inquiry",
        "state": {"completed_seasons": 1, "credits": 4, "reuse_works": False, "extraction_debt": 0},
        "total_seasons": 4, "assay_cost": 2 if case_id == "C2" else 1,
        "declared_charter": dict(zip(DIMENSIONS, Config().weights)),
        "history": [
            {"event": "inquiry", "season": 1, "choice": "none", "cost": 0},
            {"event": "action", "season": 1, "choice": "blend", "observable_burdens": {
                "acute_service_shortfall": 0.0, "farm_livelihood_disruption": 1.0,
                "habitat_pressure": 0.0, "public_expenditure": 2.0}},
            {"event": "surface", "season": 2, "after_action": "blend", "result": "clear"},
        ],
        "available_choices": ["pump", "blend", "ration", "build"] if case_id == "C3" else ["none", "assay"],
    }
    if case_id == "C3":
        packet["history"].append({"event": "inquiry", "season": 2, "choice": "none", "cost": 0})
    return packet


def verify_checkpoint(case, protocol, reachable_packet):
    case_id, packet = case["case_id"], case["public_packet"]
    require(case["status"] == "completed", f"{case_id}: checkpoint is incomplete")
    same(packet, reachable_packet if case_id == "C4" else expected_supplied_packet(case_id),
         f"{case_id}.predeclared_public_packet")
    prompt = case["prompt"]
    marker = "\n\nFIRST PACKET:\n"
    require(marker in prompt, f"{case_id}: recorded prompt has no packet marker")
    same(json.loads(prompt.rsplit(marker, 1)[1]), packet, f"{case_id}.prompt_packet")
    if case_id != "C4":
        require("No earlier source reading was available." in prompt and
                "prior before the supplied history is P(H)=0.4" in prompt,
                f"{case_id}: missing supplied-checkpoint prior clarification")
    require("Make exactly ONE decision and stop." in prompt,
            f"{case_id}: missing single-decision override")
    try:
        parsed = json.loads(case["raw_response"])
    except json.JSONDecodeError:
        parsed = None
    same(case["response"], parsed, f"{case_id}.raw_response_parsing")
    same(case["parsed_json_object"], isinstance(parsed, dict), f"{case_id}.parsed_json_object")
    config = config_for_packet(packet)
    g = grade(case, packet, Planner(config), case_id,
              protocol["budget"]["public_reason_word_limit"], "action_regret")
    same(case["correct_public_posterior_fraction"], g["posterior_fraction"],
         f"{case_id}.correct_public_posterior_fraction")
    same(case["valid_forecast"], g["forecast"] is not None, f"{case_id}.valid_forecast")
    same(case["posterior_squared_error"], g["posterior_squared_error"], f"{case_id}.posterior_squared_error")
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    if "actual_prompt_sha256" in case:
        same(case["actual_prompt_sha256"], prompt_hash, f"{case_id}.actual_prompt_sha256")
    return {
        "case_id": case_id, "distribution": case["distribution"],
        "checkpoint_type": "reachable_previously_published" if case_id == "C4" else "hypothetical_supplied",
        "phase": packet["phase"], "assay_cost": packet["assay_cost"],
        "choice": g["applied_choice"], "valid_choice": g["valid_choice"],
        "optimal_choice_match": g["optimal_choice"], "optimal_choices": g["optimal_choices"],
        "reference_action": g["reference_action"], "reference_label_match": g["reference_label_match"],
        "action_regret": g["regret"], "reference_values": g["reference_values"],
        "forecast_hazardous": g["forecast"], "correct_public_posterior": g["posterior"],
        "post_hoc_posterior_squared_error": g["posterior_squared_error"],
        "public_reason_words": g["reason_words"], "actual_prompt_sha256": prompt_hash,
        "post_hoc_exposure": exposure(packet["history"]),
    }, g


def verify_deviations(document, logs, cases, common_prompt):
    checks = []
    ids = [deviation["id"] for deviation in document["deviations"]]
    require(len(ids) == len(set(ids)), "Duplicate protocol-deviation identifiers")
    require({"C1-punctuation", "B2-history-expenditure"}.issubset(ids),
            "Known C1 and B2 input deviations must remain in the record")
    for deviation in document["deviations"]:
        if "episode" in deviation:
            episode = deviation["episode"]
            index = deviation["response_number"] - 1
            canonical = logs[episode]["steps"][index]["packet"]
            patched = copy.deepcopy(canonical)
            parts = [part.replace("~1", "/").replace("~0", "~")
                     for part in deviation["json_pointer"].split("/")[1:]]
            target = patched
            for part in parts[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            key = int(parts[-1]) if isinstance(target, list) else parts[-1]
            same(target[key], deviation["canonical_value"], f"{deviation['id']}.canonical_value")
            target[key] = deviation["delivered_value"]
            same(deviation["actual_input_packet"], patched, f"{deviation['id']}.actual_input_patch")
            planner = Planner(config_for_packet(canonical))
            canonical_p, canonical_values = reference(canonical, planner)
            actual_p, actual_values = reference(patched, planner)
            same(float(actual_p), float(canonical_p), f"{deviation['id']}.posterior_invariance")
            same(actual_values, canonical_values, f"{deviation['id']}.continuation_values_invariance")
            checks.append({"id": deviation["id"], "exact_recorded_patch_verified": True,
                           "continuation_values_and_posterior_unchanged": True,
                           "clean_protocol_replication": False})
        elif "case_id" in deviation:
            require(deviation["template_text"] in common_prompt,
                    f"{deviation['id']}: template text missing from common prompt")
            changed_prefix = common_prompt.replace(deviation["template_text"], deviation["delivered_text"], 1)
            require(cases[deviation["case_id"]]["prompt"].startswith(changed_prefix),
                    f"{deviation['id']}: actual prompt does not preserve the documented variation")
            checks.append({"id": deviation["id"], "recorded_prompt_variation_verified": True})
        else:
            raise VerificationError(f"Unsupported deviation record: {deviation.get('id')!r}")
    return checks


def summed_exposure(rows):
    return {key: sum(row["post_hoc_exposure"][key] for row in rows)
            for key in rows[0]["post_hoc_exposure"]}


def verify():
    files = Inputs()
    required = [HERE / name for name in (
        "protocol.json", "contestant_prompt.txt", "protocol_deviations.json", "checkpoints.json",
        *(episode + ".json" for episode in EPISODES),
    )]
    missing = [path.name for path in required if not path.is_file()]
    require(not missing, "Incomplete pilot; missing: " + ", ".join(missing))
    protocol = files.json(HERE / "protocol.json")
    for key, expected in (("complete_games", 4), ("decisions_per_game", 8),
                          ("diagnostic_decisions", 4), ("total_decision_responses", 36)):
        same(protocol["budget"][key], expected, f"protocol.budget.{key}")
    engine_hash = files.digest(REPO / "src" / "the_long_view" / "engine.py")
    verifier_hash = files.digest(Path(__file__).resolve())
    same(engine_hash, protocol["engine_sha256"], "frozen engine SHA-256")
    same(files.digest(REPO / "docs" / "player_brief.txt"), protocol["player_brief_sha256"],
         "frozen player brief SHA-256")
    common_prompt = files.read(HERE / "contestant_prompt.txt").decode()
    checkpoints = files.json(HERE / "checkpoints.json")
    same(checkpoints["model_requested"], protocol["model_requested"], "checkpoints.model_requested")
    same(checkpoints["reasoning_effort_requested"], protocol["reasoning_effort_requested"],
         "checkpoints.reasoning_effort_requested")
    same(checkpoints["common_prompt_file"], "contestant_prompt.txt", "checkpoints.common_prompt_file")
    same(checkpoints["common_prompt_sha256"], files.digest(HERE / "contestant_prompt.txt"),
         "checkpoints.common_prompt_sha256")
    same(checkpoints["predeclared_cases"], list(CASES), "checkpoints.predeclared_cases")
    ids = [case["case_id"] for case in checkpoints["cases"]]
    require(len(ids) == 4 and set(ids) == set(CASES),
            f"Incomplete or duplicate checkpoint set: {ids!r}; expected C1-C4 exactly once")
    require(checkpoints["status"] == "completed fixed four-case diagnostic evaluation",
            "Checkpoint bundle is not marked complete")
    cases = {case["case_id"]: case for case in checkpoints["cases"]}
    logs = {episode: files.json(HERE / (episode + ".json")) for episode in EPISODES}
    rows, all_grades = [], []
    for episode, log in logs.items():
        row, grades = verify_game(episode, log, protocol)
        rows.append(row)
        all_grades.extend(grades)
    seeds = {row["episode"]: row["released_seed"] for row in rows}
    require(seeds["A1"] == seeds["A2"] and seeds["B1"] == seeds["B2"] and seeds["A1"] != seeds["B1"],
            "Released seeds do not match the declared two-world, two-price pairing")
    reachable = files.json(REPO / "examples" / "reachable_checkpoint_v0_1.json")["player_packet"]
    checkpoint_rows, checkpoint_grades = [], []
    for case_id in CASES:
        row, g = verify_checkpoint(cases[case_id], protocol, reachable)
        checkpoint_rows.append(row)
        checkpoint_grades.append(g)
    deviations = files.json(HERE / "protocol_deviations.json")
    deviation_checks = verify_deviations(deviations, logs, cases, common_prompt)
    for row in rows + checkpoint_rows:
        linked = [d["id"] for d in deviations["deviations"]
                  if ("episode" in row and d.get("episode") == row["episode"])
                  or ("case_id" in row and d.get("case_id") == row["case_id"])]
        row["documented_input_deviation"] = bool(linked)
        row["deviation_ids"] = linked
    game_totals = decision_totals(all_grades)
    game_totals.update({
        "completed_games": len(rows), "distinct_exogenous_worlds": len(set(seeds.values())),
        "sum_realised_charter_loss": sum(row["realised_charter_loss"] for row in rows),
        "mean_realised_charter_loss": mean(row["realised_charter_loss"] for row in rows),
        "mean_local_excess_expected_loss_per_game": mean(row["sum_local_excess_expected_loss"] for row in rows),
        "forecast_weighted_brier": (
            sum(row["forecast_brier"] * row["valid_forecasts"] for row in rows if row["valid_forecasts"])
            / game_totals["valid_forecasts"] if game_totals["valid_forecasts"] else None),
        "mean_outcome_vector": {d: mean(row["outcome_vector"][d] for row in rows) for d in DIMENSIONS},
        "worlds_by_revealed_condition": {
            condition: sum(row["revealed_condition"] == condition for row in rows if row["assay_cost"] == 1)
            for condition in ("benign", "hazardous")},
        "post_hoc_exposure": summed_exposure(rows),
        "post_hoc_action_decisions_with_reuse_available": sum(
            row["post_hoc_action_decisions_with_reuse_available"] for row in rows),
    })
    checkpoint_totals = decision_totals(checkpoint_grades)
    checkpoint_totals["post_hoc_exposure"] = summed_exposure(checkpoint_rows)
    recorded_count = len(all_grades) + len(checkpoint_grades)
    same(recorded_count, protocol["budget"]["total_decision_responses"], "recorded response count")
    summary = {
        "schema": "long-view-astra-pilot-summary-v1",
        "status": "Complete exploratory pilot; canonical engine replay and reference regrading verified; documented input deviations retained",
        "model_requested": protocol["model_requested"],
        "reasoning_effort_requested": protocol["reasoning_effort_requested"],
        "verification": {
            "engine_sha256": engine_hash, "engine_and_player_brief_hashes_match_protocol": True,
            "verifier_sha256": verifier_hash,
            "scope": "Canonical engine packets, transitions, final results, posterior/reference scores, choices and reason-word counts; recorded checkpoint replies and prompt packets; documented input patches.",
            "input_provenance_limit": "Canonical replay is not byte-exact attestation of all model inputs. Episode logs preserve parsed response objects. Manual delivery discrepancies remain part of the experiment; B2 is not a clean protocol replication.",
            "score_absolute_tolerance": SCORE_ABS_TOL, "score_relative_tolerance": SCORE_REL_TOL,
            "optimal_choice_absolute_tolerance": OPTIMAL_ABS_TOL,
            "input_files_sha256": files.hashes(),
        },
        "recorded_budget": {"planned_decision_responses": 36, "recorded_game_responses": len(all_grades),
                            "recorded_checkpoint_responses": len(checkpoint_grades), "recorded_total": recorded_count,
                            "scope": "Counts published responses; replay does not independently attest unlogged execution activity."},
        "metric_definitions": {
            "realised_charter_loss": "Weighted fictional burden over one completed game, including terminal liabilities; lower is better under the declared charter.",
            "local_excess_expected_loss": "Chosen or fallback action's expected remaining charter loss minus the minimum at the actual public-history posterior, assuming optimal continuation. The sum over encountered decisions is not a paired realised-outcome difference.",
            "optimal_choice_matches": "Valid submitted choices whose value is within the stated absolute tolerance of the minimum. Tied optimal actions all count; reference_label_matches is the separate literal tie-order label count.",
            "forecast_brier": "Mean squared submitted forecast error against the game's revealed binary condition. Information acquisition and action-dependent observations affect this score.",
            "posterior_squared_error": "Post-hoc squared deviation from the exact public-history posterior, distinct from Brier error against the realised condition; means include only valid forecasts.",
            "mask_exposure": "Post-hoc observations counted once per episode from its final replayed history, or once per supplied checkpoint history, never repeatedly from growing packet histories. Paired episodes and repeated checkpoint presentations are not independent world draws.",
        },
        "secondary_diagnostics_status": SECONDARY_NOTE,
        "full_games": {"rows": rows, "totals": game_totals},
        "diagnostic_checkpoints": {
            "scope": "Three hypothetical supplied checkpoints and one previously published reachable checkpoint. These are a separate diagnostic distribution, not four additional complete games.",
            "rows": checkpoint_rows, "totals": checkpoint_totals,
        },
        "protocol_deviations_present": bool(deviations["deviations"]),
        "protocol_deviations": deviations,
        "deviation_verification": deviation_checks,
        "unavailable_telemetry": deviations["unavailable_telemetry"],
        "limitations": [
            "Four games share two exogenous worlds, with one run at each assay price; this is a tiny mechanics pilot, not a model ranking or an architecture comparison.",
            "Reference optimality is confined to this fully specified four-season kernel and its declared scalar charter, not general ethical reasoning or the proposed longer campaign.",
            "The model name, effort request, fresh-agent setup and no-tools instructions are execution metadata; this replay cannot independently attest model identity or hardened isolation.",
            "All recorded runs and the two documented input discrepancies are retained; no inference latency, reasoning-token usage or monetary cost is fabricated.",
            SECONDARY_NOTE,
        ],
    }
    files.check_unchanged()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="verify without writing summary.json")
    args = parser.parse_args()
    try:
        summary = verify()
        if not args.check_only:
            output = HERE / "summary.json"
            temporary = HERE / "summary.json.tmp"
            try:
                temporary.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                temporary.replace(output)
            finally:
                temporary.unlink(missing_ok=True)
    except (VerificationError, KeyError, TypeError, ValueError, OSError, IndexError) as exc:
        print(f"Verification failed; no new summary written: {exc}", file=sys.stderr)
        return 1
    print("Verified 4 canonical game replays and 4 checkpoint decisions (36 recorded responses).")
    print("Documented input deviations retained; this does not attest byte-exact model input delivery.")
    for row in summary["full_games"]["rows"]:
        print(f"{row['episode']}: loss={row['realised_charter_loss']:.6g}, "
              f"Brier={row['forecast_brier']}, local regret={row['sum_local_excess_expected_loss']:.6g}, "
              f"optimal choices={row['optimal_choice_matches']}/{row['decisions']}, "
              f"input deviation={row['documented_input_deviation']}")
    totals = summary["diagnostic_checkpoints"]["totals"]
    print(f"Checkpoints: optimal choices={totals['optimal_choice_matches']}/4, "
          f"local regret={totals['sum_local_excess_expected_loss']:.6g} (separate diagnostic distribution).")
    print("Check-only: summary not written." if args.check_only else
          "Wrote experiments/astra_v0_1/summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
