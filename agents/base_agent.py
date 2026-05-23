"""
Base Agent — Abstract interface for all GP-Stratz strategy agents.
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    All strategy agents must implement `select_action`.

    Parameters
    ----------
    obs : dict
        The observation dict returned by RaceEnvironment._obs():
        {
            "lap_number":    int,
            "tyre_wear":     float,
            "weather":       int  (0=clear, 1=rain_soon, 2=rain),
            "gap_to_car":    float,
            "safety_car":    bool,
            "traffic_level": int  (0=low, 1=medium, 2=high),
            "tyre_deg_rate": float,
            "tyre_type":     int  (0=slick, 1=wet),
        }

    Returns
    -------
    int : one of (0=PIT, 1=STAY, 2=CONSERVE, 3=PUSH, 4=SWAP)
    """

    # Mirror action constants for convenience
    ACTION_PIT      = 0
    ACTION_STAY     = 1
    ACTION_CONSERVE = 2
    ACTION_PUSH     = 3
    ACTION_SWAP     = 4

    # Weather constants
    WEATHER_CLEAR = 0
    WEATHER_SOON  = 1
    WEATHER_RAIN  = 2

    # Traffic constants
    TRAFFIC_LOW    = 0
    TRAFFIC_MEDIUM = 1
    TRAFFIC_HIGH   = 2

    @abstractmethod
    def select_action(self, obs: dict) -> int:
        """Select an action given the current observation."""
        ...

    def reset(self):
        """Optional: called before each episode starts."""
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__
