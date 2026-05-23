"""
GP-Stratz Agent Package
=======================
Five strategy agents for motorsport decision-making.
"""

from .easy_agent import EasyRuleAgent
from .medium_agent import MediumAgent
from .hard_agent import HardMultiFactorAgent
from .conservative_agent import ConservativeAgent
from .aggressive_agent import AggressiveAgent

AGENT_REGISTRY = {
    "easy": EasyRuleAgent,
    "medium": MediumAgent,
    "hard": HardMultiFactorAgent,
    "conservative": ConservativeAgent,
    "aggressive": AggressiveAgent,
}

AGENT_META = {
    "easy": {
        "name": "EasyRuleAgent",
        "description": "Rule-based agent covering basic wear/weather thresholds.",
        "style": "Balanced",
        "phase": "easy",
    },
    "medium": {
        "name": "MediumAgent",
        "description": "Extends easy rules with safety-car timing and traffic awareness.",
        "style": "Tactical",
        "phase": "medium",
    },
    "hard": {
        "name": "HardMultiFactorAgent",
        "description": "Multi-factor look-ahead optimizer balancing all race variables.",
        "style": "Strategic",
        "phase": "hard",
    },
    "conservative": {
        "name": "ConservativeAgent",
        "description": "Wear-first: always conserve unless forced to pit or swap.",
        "style": "Conservative",
        "phase": "all",
    },
    "aggressive": {
        "name": "AggressiveAgent",
        "description": "Gap-first: push hard and close gaps, pit only when critical.",
        "style": "Aggressive",
        "phase": "all",
    },
}
