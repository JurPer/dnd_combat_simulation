from pathlib import Path

from backend.repositories.actions import ActionRepository
from backend.repositories.battles import BattleRepository
from backend.repositories.combatants import CombatantRepository
from backend.repositories.effects import EffectRepository


class RepositoryContainer:
    def __init__(self, base_dir=None):
        base_dir = Path(base_dir or Path(__file__).resolve().parents[2] / "data")
        self.effects = EffectRepository(base_dir / "effects")
        self.actions = ActionRepository(base_dir / "actions", self.effects)
        self.combatants = CombatantRepository(base_dir / "combatants", self.actions, self.effects)
        self.battles = BattleRepository(base_dir / "battles")
