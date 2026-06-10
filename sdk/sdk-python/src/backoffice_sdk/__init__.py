from .client import FeatureFlagClient
from .evaluator import evaluate_rule, evaluate_flag, OPERATORS

__all__ = ["FeatureFlagClient", "evaluate_rule", "evaluate_flag", "OPERATORS"]
__version__ = "0.1.0"
