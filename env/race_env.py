class RaceEnvironment:
    """
    GP-Stratz Motorsport Strategy Environment  v4
    ─────────────────────────────────────────────
    Reward structure (clamped to [-2.0, +2.0]):
      correctness   1.2 * (±1)    dominant correctness term
      forward_bonus up to +0.4    for provably smart moves
      seq_bonus     +0.3          consistent 3+ lap strategy
      seq_penalty   -0.3          erratic flip-flop behavior
      mismatch      -0.2 to -0.5  physics-level bad choices
    """

    # Actions
    ACTION_PIT      = 0
    ACTION_STAY     = 1
    ACTION_CONSERVE = 2
    ACTION_PUSH     = 3
    ACTION_SWAP     = 4

    # Weather
    WEATHER_CLEAR = 0
    WEATHER_SOON  = 1
    WEATHER_RAIN  = 2

    # Traffic
    TRAFFIC_LOW    = 0
    TRAFFIC_MEDIUM = 1
    TRAFFIC_HIGH   = 2

    # Decision thresholds — shared with agent & dataset rules
    WEAR_CRITICAL          = 86    # R2: >= this → must pit
    WEAR_SC_PIT            = 55    # R3: SC active + wear >= this → pit
    WEAR_CONSERVE_MIN      = 60    # R7: start conserving in clear weather
    WEAR_CONSERVE_MAX      = 85    # R7: upper limit (R2 kicks in above 85)
    WEAR_RAIN_SOON_CONSERVE= 70    # R5: rain_soon + >= this → conserve
    GAP_PUSH               = 2.0   # R8: gap < this → attack
    GAP_CONSERVE           = 5.0   # R7: gap >= this → conserve in clear

    def __init__(self, max_laps=30):
        self.max_laps = max_laps
        self.reset()

    # ──────────────────────────────────────────────────────────
    def reset(self, initial_state=None):
        s = initial_state or {}
        self.lap        = s.get("lap",        1)
        self.wear       = float(s.get("wear", 0.0))
        self.weather    = s.get("weather",    self.WEATHER_CLEAR)
        self.gap        = float(s.get("gap",  5.0))
        self.tyre_type  = s.get("tyre_type",  0)
        self.safety_car = bool(s.get("safety_car", False))
        self.traffic    = s.get("traffic",    self.TRAFFIC_LOW)
        self.deg_rate   = float(s.get("deg_rate", 1.0))
        self.done           = False
        self.steps_in_ep    = 0
        self.action_history = []
        return self._obs()

    # ──────────────────────────────────────────────────────────
    def _obs(self):
        return {
            "lap_number":   self.lap,
            "tyre_wear":    round(self.wear, 2),
            "weather":      self.weather,
            "gap_to_car":   round(self.gap, 2),
            "safety_car":   self.safety_car,
            "traffic_level":self.traffic,
            "tyre_deg_rate":self.deg_rate,
            "tyre_type":    self.tyre_type,
        }

    def state(self):
        return self._obs()

    # ──────────────────────────────────────────────────────────
    def step(self, action, optimal_action=None):
        if self.done:
            return self._obs(), 0.0, True, {"msg": "Episode already finished."}

        self.steps_in_ep += 1
        self.action_history.append(action)
        prev_wear = self.wear

        wear_delta   = 5.0 * self.deg_rate   # base per-lap wear (modified below)
        forward_bonus    = 0.0
        mismatch_penalty = 0.0

        # ── Action physics ─────────────────────────────────────
        if action == self.ACTION_PIT:
            self.wear  = 0.0
            wear_delta = 0.0
            if self.safety_car:
                forward_bonus += 0.4     # SC pit costs only 10s — huge strategic win
            elif prev_wear < 40 and self.weather == self.WEATHER_CLEAR:
                mismatch_penalty -= 0.3  # wasteful early pit

        elif action == self.ACTION_SWAP:
            self.wear      = 0.0
            wear_delta     = 0.0
            self.tyre_type = 1 - self.tyre_type
            if self.weather == self.WEATHER_RAIN:
                forward_bonus += 0.4     # mandatory swap executed correctly
            elif self.weather == self.WEATHER_CLEAR:
                mismatch_penalty -= 0.4  # swapping for no reason

        elif action == self.ACTION_CONSERVE:
            wear_delta *= 0.5
            if self.WEAR_CONSERVE_MIN <= prev_wear <= self.WEAR_CONSERVE_MAX:
                forward_bonus += 0.2
            elif self.weather == self.WEATHER_SOON and prev_wear >= self.WEAR_RAIN_SOON_CONSERVE:
                forward_bonus += 0.2     # smart: extend stint to merge with wet-change
            elif prev_wear < 40:
                mismatch_penalty -= 0.2  # over-conserving on fresh tyres

        elif action == self.ACTION_PUSH:
            wear_delta *= 1.8
            if self.gap < self.GAP_PUSH and prev_wear < 50:
                forward_bonus += 0.3     # textbook undercut attempt
            elif self.traffic == self.TRAFFIC_HIGH:
                mismatch_penalty -= 0.4  # pushing in gridlock accomplishes nothing
            elif prev_wear >= self.WEAR_CRITICAL:
                mismatch_penalty -= 0.5  # reckless on destroyed tyres

        elif action == self.ACTION_STAY:
            if prev_wear >= self.WEAR_CRITICAL:
                mismatch_penalty -= 0.5  # ignoring tyre failure warning
            elif prev_wear < self.WEAR_CONSERVE_MIN:
                forward_bonus += 0.1     # steady efficient lap

        # ── Wear update ────────────────────────────────────────
        if action not in (self.ACTION_PIT, self.ACTION_SWAP):
            if self.traffic == self.TRAFFIC_HIGH:
                wear_delta += 2.0        # high traffic = more sliding
            if self.weather == self.WEATHER_RAIN and self.tyre_type == 0:
                wear_delta += 4.0        # slicks in rain destroy tyre rapidly
                mismatch_penalty -= 0.3
            self.wear += wear_delta

        # ── DNF check ──────────────────────────────────────────
        if self.wear >= 100.0:
            self.done = True
            return self._obs(), -2.0, True, {"msg": "DNF: tyre failure"}

        # ── Advance lap ────────────────────────────────────────
        self.lap += 1
        if self.lap > self.max_laps:
            self.done = True

        # ── Gap update (deterministic) ─────────────────────────
        if action == self.ACTION_PUSH:
            self.gap = max(0.0, self.gap - 0.5)
        elif action == self.ACTION_CONSERVE:
            self.gap = self.gap + 0.5

        # ── Correctness (dominant term, weight = 1.2) ──────────
        if optimal_action is not None:
            correctness = 1.2 if action == optimal_action else -1.2
        else:
            correctness = 0.0

        # ── Sequence consistency ────────────────────────────────
        seq_bonus = 0.0
        if len(self.action_history) >= 3:
            last3 = self.action_history[-3:]
            # Reward 3 laps of same strategic intent
            if len(set(last3)) == 1:
                seq_bonus = 0.3
            # Penalize flip-flop: PUSH ↔ CONSERVE
            elif (last3[-1] in (self.ACTION_PUSH, self.ACTION_CONSERVE)
                  and last3[-2] in (self.ACTION_PUSH, self.ACTION_CONSERVE)
                  and last3[-1] != last3[-2]):
                seq_bonus = -0.3

        # ── Compose & clamp ────────────────────────────────────
        raw = correctness + forward_bonus + mismatch_penalty + seq_bonus
        reward = max(-2.0, min(2.0, round(raw, 3)))

        info = {
            "reward_breakdown": {
                "correctness":    round(correctness, 3),
                "forward_bonus":  round(forward_bonus, 3),
                "mismatch":       round(mismatch_penalty, 3),
                "seq_bonus":      round(seq_bonus, 3),
                "raw":            round(raw, 3),
                "clamped":        reward,
            }
        }
        return self._obs(), reward, self.done, info