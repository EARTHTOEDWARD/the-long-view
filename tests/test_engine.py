"""Checks of scientific/benchmark semantics, not LLM performance tests."""

import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from the_long_view.engine import (Config, Game, Planner, State, available_actions, bayes,
                    belief_from_history, policy_decision, surface_likelihoods)


class KernelTests(unittest.TestCase):
    def test_clean_blended_sample_carries_no_hazard_information(self):
        prior = Fraction(2, 5)
        _, masked = bayes(prior, True, *surface_likelihoods("blend"))
        _, unmasked = bayes(prior, True, *surface_likelihoods(None))
        self.assertEqual(masked, prior)
        self.assertEqual(unmasked, Fraction(4, 31))

    def test_history_conditions_on_the_action_that_generated_evidence(self):
        history = [{"event": "surface", "after_action": "blend", "result": "clear"}]
        self.assertEqual(belief_from_history(history, Fraction(2, 5)), Fraction(2, 5))
        self.assertEqual(belief_from_history(history, Fraction(2, 5), True), Fraction(4, 31))

    def test_reachable_blended_warning_does_not_create_spurious_alarm(self):
        game = Game(29)
        game.step("none")
        game.step("blend")
        game.step("none")
        self.assertEqual(game.history[0]["result"], "clear")
        self.assertEqual(game.history[3]["result"], "warning")
        correct = belief_from_history(game.history, game.config.prior)
        mistaken = belief_from_history(game.history, game.config.prior, True)
        self.assertEqual(correct, Fraction(4, 31))
        self.assertEqual(mistaken, Fraction(32, 59))
        planner = Planner(game.config)
        self.assertEqual(planner.choice("action", game.state, correct), "pump")
        self.assertEqual(planner.choice("action", game.state, mistaken), "blend")

    def test_cost_changes_whether_inquiry_is_worth_doing(self):
        state, belief = State(1, 4, False, 0), Fraction(2, 5)
        self.assertEqual(Planner(Config(assay_cost=1)).choice("inquiry", state, belief), "assay")
        self.assertEqual(Planner(Config(assay_cost=2)).choice("inquiry", state, belief), "none")

    def test_no_reward_for_irrelevant_inquiry(self):
        state = State(2, 3, True, 0)
        self.assertEqual(Planner(Config()).choice("inquiry", state, Fraction(1, 2)), "none")

    def test_one_period_values_match_hand_calculation_including_tail(self):
        planner = Planner(Config(seasons=1))
        values = dict(planner.action_values(State(credits=6), Fraction(2, 5)))
        # Pump: habitat 1 + terminal habitat 0.5 + probability .4 ×
        # (two immediate-latent health units + two residual units) × weight 4.
        self.assertAlmostEqual(values["pump"], 1.5 + 0.4 * 4 * 4)
        self.assertAlmostEqual(values["blend"], 1 + 2 * 0.5)
        self.assertEqual(planner.choice("action", State(credits=6), Fraction(2, 5)), "blend")

    def test_declared_charter_can_change_choice(self):
        state = State(credits=6)
        standard = Planner(Config(seasons=1))
        farm_priority = Planner(Config(seasons=1, weights=(4, 4, 20, 1, 0.5)))
        self.assertEqual(standard.choice("action", state, Fraction(2, 5)), "blend")
        self.assertEqual(farm_priority.choice("action", state, Fraction(2, 5)), "pump")

    def test_time_horizon_changes_investment_choice(self):
        state = State(credits=6)
        self.assertEqual(Planner(Config(seasons=4)).choice("action", state, Fraction(1)), "build")
        self.assertEqual(Planner(Config(seasons=1)).choice("action", state, Fraction(1)), "blend")

    def test_observer_packet_hides_actual_state_and_oracle_and_is_not_an_alias(self):
        game = Game(7)
        packet = game.public_packet()
        serialized = json.dumps(packet)
        for private in ('"seed"', '"hazardous"', '"posterior"', '"outcomes"'):
            self.assertNotIn(private, serialized)
        packet["history"][0]["result"] = "tampered"
        self.assertNotEqual(game.history[0]["result"], "tampered")
        with self.assertRaises(ValueError):
            game.result()

    def test_policy_cannot_distinguish_identical_public_histories(self):
        first = Game(7)
        second = copy.deepcopy(first)
        second.hazardous = not first.hazardous
        second.seed = 12345
        self.assertEqual(first.public_packet(), second.public_packet())
        planner = Planner(first.config)
        self.assertEqual(policy_decision("bayes_full", first.public_packet(), planner),
                         policy_decision("bayes_full", second.public_packet(), planner))

    def test_query_does_not_shift_later_surface_randomness(self):
        querying, skipping = Game(25), Game(25)
        querying.step("assay")
        skipping.step("none")
        querying.step("pump")
        skipping.step("pump")
        self.assertEqual(querying.history[-1], skipping.history[-1])

    def test_budget_violation_does_not_mutate_game(self):
        game = Game(1, Config(credits=0))
        before = game.public_packet()
        with self.assertRaises(ValueError):
            game.step("assay")
        self.assertEqual(game.public_packet(), before)
        game.step("none")
        before = game.public_packet()
        with self.assertRaises(ValueError):
            game.step("blend")
        self.assertEqual(game.public_packet(), before)

    def test_investment_changes_future_action_set(self):
        game = Game(2)
        self.assertNotIn("reuse", available_actions(game.state))
        game.step("none")
        game.step("build")
        self.assertIn("reuse", available_actions(game.state))
        self.assertNotIn("build", available_actions(game.state))

    def test_save_resume_preserves_world_and_future_evidence(self):
        original = Game(14)
        original.step("assay")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            original.save(path)
            resumed = Game.load(path)
            self.assertEqual(original.public_packet(), resumed.public_packet())
            self.assertEqual(original.step("pump"), resumed.step("pump"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
