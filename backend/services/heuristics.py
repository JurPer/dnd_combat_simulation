import random
from dataclasses import dataclass


class TargetSelectionHeuristic:
    def select(self, targets):
        raise NotImplementedError


class Random(TargetSelectionHeuristic):
    def select(self, targets):
        return random.choice(targets)


class HighestHealth(TargetSelectionHeuristic):
    def select(self, targets):
        return max(targets, key=lambda target: target.hp)


class LowestHealth(TargetSelectionHeuristic):
    def select(self, targets):
        return min(targets, key=lambda target: target.hp)


class HighestAC(TargetSelectionHeuristic):
    def select(self, targets):
        return max(targets, key=lambda target: target.ac)


class LowestAC(TargetSelectionHeuristic):
    def select(self, targets):
        return min(targets, key=lambda target: target.ac)


class LowestHealthPercentage(TargetSelectionHeuristic):
    def select(self, targets):
        return min(targets, key=lambda target: target.hp / target.max_hp)


class LowestHealthPercentageBelowThreshold(TargetSelectionHeuristic):
    def __init__(self, threshold=0.4):
        self.threshold = threshold

    def select(self, targets):
        eligible_targets = [
            target for target in targets if target.hp <= target.max_hp * self.threshold
        ]
        if not eligible_targets:
            return None
        return min(eligible_targets, key=lambda target: target.hp / target.max_hp)


@dataclass
class HeuristicContainer:
    attack_selection: TargetSelectionHeuristic = None
    heal_selection: TargetSelectionHeuristic = None


HEURISTIC_MAPPING = {
    "Random": Random,
    "HighestHealth": HighestHealth,
    "LowestHealth": LowestHealth,
    "HighestAC": HighestAC,
    "LowestAC": LowestAC,
    "LowestHealthPercentage": LowestHealthPercentage,
    "LowestHealthPercentageBelowThreshold": LowestHealthPercentageBelowThreshold,
}
