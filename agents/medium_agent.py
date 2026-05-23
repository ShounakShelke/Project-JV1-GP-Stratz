"""
MediumAgent — Phase 2 agent.
Extends EasyRuleAgent with safety-car timing, traffic awareness,
and gap-based push decisions.
"""

from .base_agent import BaseAgent


class MediumAgent(BaseAgent):
    """
    Decision tree (in priority order):
      R1. wear >= 86                        → PIT  (critical)
      R2. rain + slick tyres                → SWAP
      R3. safety_car + wear >= 55           → PIT  (free-stop window!)
      R4. rain_soon + wear >= 70            → CONSERVE
      R5. traffic HIGH + wear >= 40         → CONSERVE (avoid sliding)
      R6. gap < 2.0 + wear < 50            → PUSH  (undercut window)
      R7. wear >= 60 + gap >= 5.0          → CONSERVE
      R8. wear < 40 + gap >= 5.0          → STAY
      R9. (default)                         → STAY
    """

    WEAR_CRITICAL   = 86
    WEAR_SC_PIT     = 55
    WEAR_CONSERVE   = 60
    WEAR_RAIN_SOON  = 70
    WEAR_PUSH_MAX   = 50
    WEAR_TRAFFIC    = 40
    GAP_PUSH        = 2.0
    GAP_CONSERVE    = 5.0

    def select_action(self, obs: dict) -> int:
        wear    = obs["tyre_wear"]
        weather = obs["weather"]
        tyre    = obs["tyre_type"]
        sc      = obs["safety_car"]
        traffic = obs["traffic_level"]
        gap     = obs["gap_to_car"]

        # R1: Critical wear
        if wear >= self.WEAR_CRITICAL:
            return self.ACTION_PIT

        # R2: Rain on slick compound — mandatory
        if weather == self.WEATHER_RAIN and tyre == 0:
            return self.ACTION_SWAP

        # R3: Safety car active — free stop window
        if sc and wear >= self.WEAR_SC_PIT:
            return self.ACTION_PIT

        # R4: Rain approaching — extend to wet-window
        if weather == self.WEATHER_SOON and wear >= self.WEAR_RAIN_SOON:
            return self.ACTION_CONSERVE

        # R5: Heavy traffic — conserving avoids extra wear from sliding
        if traffic == self.TRAFFIC_HIGH and wear >= self.WEAR_TRAFFIC:
            return self.ACTION_CONSERVE

        # R6: Undercut opportunity — rival is close, tyres fresh enough
        if gap < self.GAP_PUSH and wear < self.WEAR_PUSH_MAX:
            return self.ACTION_PUSH

        # R7: High wear + clear gap → manage tyres
        if wear >= self.WEAR_CONSERVE and gap >= self.GAP_CONSERVE:
            return self.ACTION_CONSERVE

        return self.ACTION_STAY
