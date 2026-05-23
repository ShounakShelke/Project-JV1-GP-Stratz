"""
ConservativeAgent — Wear-first strategy.
Always CONSERVE unless a critical rule forces otherwise.
"""

from .base_agent import BaseAgent


class ConservativeAgent(BaseAgent):
    """
    Minimal-risk agent that prioritises tyre longevity:
      R1. wear >= 86            → PIT (can't delay)
      R2. rain + slick tyres   → SWAP (safety rule)
      R3. safety_car active    → PIT if wear >= 40 (opportunistic)
      R4. everything else      → CONSERVE
    """

    WEAR_CRITICAL   = 86
    WEAR_SC_OPP     = 40

    def select_action(self, obs: dict) -> int:
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]
        sc      = obs["safety_car"]

        if wear >= self.WEAR_CRITICAL:
            return self.ACTION_PIT

        if weather == self.WEATHER_RAIN and tyre == 0:
            return self.ACTION_SWAP

        if sc and wear >= self.WEAR_SC_OPP:
            return self.ACTION_PIT

        return self.ACTION_CONSERVE
