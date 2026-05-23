"""
AggressiveAgent — Gap-closing first strategy.
PUSH when gap > 0.5, only pits at wear 90+.
"""

from .base_agent import BaseAgent


class AggressiveAgent(BaseAgent):
    """
    High-risk agent that prioritises track position and closing the gap:
      R1. wear >= 90            → PIT (pushed beyond normal failure limit)
      R2. rain + slick tyres   → SWAP
      R3. gap > 0.5 + wear < 90 → PUSH
      R4. everything else      → STAY
    """

    WEAR_CRITICAL = 90
    GAP_TARGET = 0.5

    def select_action(self, obs: dict) -> int:
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]
        gap     = obs["gap_to_car"]

        if wear >= self.WEAR_CRITICAL:
            return self.ACTION_PIT

        if weather == self.WEATHER_RAIN and tyre == 0:
            return self.ACTION_SWAP

        if gap > self.GAP_TARGET and wear < self.WEAR_CRITICAL:
            return self.ACTION_PUSH

        return self.ACTION_STAY
