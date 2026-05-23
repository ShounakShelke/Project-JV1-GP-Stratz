"""
HardMultiFactorAgent — Phase 3 agent.
Multi-factor look-ahead optimizer that scores all 5 actions against the
current state and picks the highest expected value.
"""

from .base_agent import BaseAgent


class HardMultiFactorAgent(BaseAgent):
    """
    Scores each candidate action by estimating:
      - Correctness likelihood vs known optimal rules
      - Forward bonus eligibility
      - Mismatch penalty exposure
      - 3-lap sequence consistency bonus

    Picks the action with highest composite estimated reward.
    """

    WEAR_CRITICAL          = 86
    WEAR_SC_PIT            = 55
    WEAR_CONSERVE_MIN      = 60
    WEAR_CONSERVE_MAX      = 85
    WEAR_RAIN_SOON_CONSERVE= 70
    WEAR_PUSH_MAX          = 50
    GAP_PUSH               = 2.0
    GAP_CONSERVE           = 5.0

    def __init__(self):
        self._history = []

    def reset(self):
        self._history = []

    def _estimate_action_value(self, action: int, obs: dict) -> float:
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]
        sc      = obs["safety_car"]
        traffic = obs["traffic_level"]
        gap     = obs["gap_to_car"]
        deg     = obs["tyre_deg_rate"]

        score = 0.0

        # ── Determine optimal action via rule cascade ────────────
        optimal = self._get_optimal(obs)
        # Correctness bonus/penalty
        score += 1.2 if action == optimal else -1.2

        # ── Forward bonus estimation ─────────────────────────────
        if action == self.ACTION_PIT:
            if sc:
                score += 0.4     # free stop
            elif wear < 40 and weather == self.WEATHER_CLEAR:
                score -= 0.3     # too early

        elif action == self.ACTION_SWAP:
            if weather == self.WEATHER_RAIN:
                score += 0.4
            elif weather == self.WEATHER_CLEAR:
                score -= 0.4     # unnecessary swap

        elif action == self.ACTION_CONSERVE:
            if self.WEAR_CONSERVE_MIN <= wear <= self.WEAR_CONSERVE_MAX:
                score += 0.2
            elif weather == self.WEATHER_SOON and wear >= self.WEAR_RAIN_SOON_CONSERVE:
                score += 0.2
            elif wear < 40:
                score -= 0.2     # over-conserving

        elif action == self.ACTION_PUSH:
            if gap < self.GAP_PUSH and wear < self.WEAR_PUSH_MAX:
                score += 0.3
            elif traffic == self.TRAFFIC_HIGH:
                score -= 0.4
            elif wear >= self.WEAR_CRITICAL:
                score -= 0.5

        elif action == self.ACTION_STAY:
            if wear >= self.WEAR_CRITICAL:
                score -= 0.5
            elif wear < self.WEAR_CONSERVE_MIN:
                score += 0.1

        # ── Sequence consistency (look at last 2 laps + this action) ──
        if len(self._history) >= 2:
            last2 = self._history[-2:]
            candidate3 = last2 + [action]
            if len(set(candidate3)) == 1:
                score += 0.3     # 3-lap consistency bonus
            elif (candidate3[-1] in (self.ACTION_PUSH, self.ACTION_CONSERVE)
                  and candidate3[-2] in (self.ACTION_PUSH, self.ACTION_CONSERVE)
                  and candidate3[-1] != candidate3[-2]):
                score -= 0.3     # flip-flop penalty

        # ── Degrade-rate awareness ────────────────────────────────
        projected_wear = wear + (5.0 * deg)
        if projected_wear >= self.WEAR_CRITICAL and action not in (
            self.ACTION_PIT, self.ACTION_CONSERVE, self.ACTION_SWAP
        ):
            score -= 0.3         # heading toward failure without mitigation

        return score

    def _get_optimal(self, obs: dict) -> int:
        """Deterministic rule cascade — mirrors the env's optimal rules."""
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]
        sc      = obs["safety_car"]
        traffic = obs["traffic_level"]
        gap     = obs["gap_to_car"]

        if wear >= self.WEAR_CRITICAL:
            return self.ACTION_PIT
        if weather == self.WEATHER_RAIN and tyre == 0:
            return self.ACTION_SWAP
        if sc and wear >= self.WEAR_SC_PIT:
            return self.ACTION_PIT
        if weather == self.WEATHER_SOON and wear >= self.WEAR_RAIN_SOON_CONSERVE:
            return self.ACTION_CONSERVE
        if traffic == self.TRAFFIC_HIGH and wear >= 40:
            return self.ACTION_CONSERVE
        if gap < self.GAP_PUSH and wear < self.WEAR_PUSH_MAX:
            return self.ACTION_PUSH
        if self.WEAR_CONSERVE_MIN <= wear <= self.WEAR_CONSERVE_MAX and gap >= self.GAP_CONSERVE:
            return self.ACTION_CONSERVE
        return self.ACTION_STAY

    def select_action(self, obs: dict) -> int:
        # Score all 5 candidates
        scores = {a: self._estimate_action_value(a, obs) for a in range(5)}
        best = max(scores, key=scores.__getitem__)
        self._history.append(best)
        return best
