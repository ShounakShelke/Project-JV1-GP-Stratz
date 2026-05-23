"""
EasyRuleAgent — Phase 1 agent.
Covers the core race rules: critical wear, rain compound swap.
"""

from .base_agent import BaseAgent


class EasyRuleAgent(BaseAgent):
    """
    Decision tree:
      R1. wear >= 86               → PIT  (tyres about to fail)
      R2. rain + slick tyres       → SWAP (must change compound)
      R3. rain_soon + wear >= 70   → CONSERVE (extend to wet-window)
      R4. wear >= 60               → CONSERVE (manage degradation)
      R5. (default)                → STAY
    """

    WEAR_CRITICAL      = 86
    WEAR_CONSERVE_MIN  = 60
    WEAR_RAIN_SOON     = 70

    def select_action(self, obs: dict) -> int:
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]

        # R1: Critical wear → mandatory pit
        if wear >= self.WEAR_CRITICAL:
            return self.ACTION_PIT

        # R2: Rain on slick tyres → compound swap
        if weather == self.WEATHER_RAIN and tyre == 0:
            return self.ACTION_SWAP

        # R3: Rain approaching + wear high → conserve to merge with wet stop
        if weather == self.WEATHER_SOON and wear >= self.WEAR_RAIN_SOON:
            return self.ACTION_CONSERVE

        # R4: Moderate-high wear → conserve to extend tyre life
        if wear >= self.WEAR_CONSERVE_MIN:
            return self.ACTION_CONSERVE

        # Default: steady lap
        return self.ACTION_STAY
