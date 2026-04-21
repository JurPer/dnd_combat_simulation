from dataclasses import dataclass, field
from math import floor
from typing import List, Optional

from backend.domain.actions import ComboAttack, SingleAttack
from backend.domain.constants import (
    SELF_ADVANTAGE_SET,
    SELF_DISADVANTAGE_SET,
    TARGET_ADVANTAGE_SET,
    TARGET_DISADVANTAGE_SET,
    TYPE_IMMUNITY_TYPE,
    TYPE_RESISTANCE_TYPE,
    TYPE_VULNERABILITY_TYPE,
)


@dataclass
class Combatant:
    name: str
    max_hp: int
    ac: int
    proficiency: int
    str_save: int
    dex_save: int
    con_save: int
    wis_save: int
    int_save: int
    cha_save: int
    cr: float
    num_legendary_actions: int = 0
    combatant_type: Optional[str] = None
    size: Optional[str] = None
    speed: Optional[int] = None
    action_names: List[str] = field(default_factory=list)
    innate_effect_names: List[str] = field(default_factory=list)
    actions: List = field(default_factory=list)
    innate_effects: List = field(default_factory=list)
    applied_effects: List = field(default_factory=list)
    hp: int = field(default=0, init=False)
    saves: dict = field(default_factory=dict, init=False)
    attacks: List = field(default_factory=list, init=False)
    heals: List = field(default_factory=list, init=False)
    legendary_actions: List = field(default_factory=list, init=False)
    legendary_actions_left: int = field(default=0, init=False)
    num_actions_available: int = field(default=1, init=False)
    heuristics = None

    def copy(self):
        duplicate = Combatant(
            name=self.name,
            max_hp=self.max_hp,
            ac=self.ac,
            proficiency=self.proficiency,
            str_save=self.str_save,
            dex_save=self.dex_save,
            con_save=self.con_save,
            wis_save=self.wis_save,
            int_save=self.int_save,
            cha_save=self.cha_save,
            cr=self.cr,
            num_legendary_actions=self.num_legendary_actions,
            combatant_type=self.combatant_type,
            size=self.size,
            speed=self.speed,
            action_names=list(self.action_names),
            innate_effect_names=list(self.innate_effect_names),
            actions=[action.copy() for action in self.actions],
            innate_effects=[effect.copy() for effect in self.innate_effects],
        )
        return duplicate

    def prepare_for_battle(self, heuristics=None, applied_effects=None, num_enemies=1):
        self.hp = self.max_hp
        self.saves = self._convert_saves_to_dict()
        self.attacks = sorted(
            [
                action.instantiate()
                for action in self.actions
                if action.action_type == "Attack" and not action.is_legendary
            ],
            key=lambda x: x.calc_expected_damage(num_enemies),
            reverse=True,
        )
        self.heals = sorted(
            [
                action.instantiate()
                for action in self.actions
                if action.action_type == "Heal"
            ],
            key=lambda x: x.calc_expected_heal(),
            reverse=True,
        )
        self.legendary_actions = sorted(
            [
                action.instantiate()
                for action in self.actions
                if action.action_type == "Attack" and action.is_legendary
            ],
            key=lambda x: x.calc_expected_damage(num_enemies),
            reverse=True,
        )
        self.legendary_actions_left = self.num_legendary_actions
        self.num_actions_available = 1
        self.heuristics = heuristics
        self.applied_effects = [effect.instantiate() for effect in self.innate_effects]
        if applied_effects:
            self.applied_effects.extend(
                effect.instantiate() for effect in applied_effects
            )

    def _convert_saves_to_dict(self):
        return {
            "STR": self.str_save,
            "DEX": self.dex_save,
            "CON": self.con_save,
            "WIS": self.wis_save,
            "INT": self.int_save,
            "CHA": self.cha_save,
        }

    @staticmethod
    def create(**kwargs):
        save_range = set(range(1, 31))
        if not kwargs["name"]:
            return "Combatant needs a name", None
        if int(kwargs["hp"]) < 1:
            return "Combatant HP must be greater than 1", None
        if int(kwargs["ac"]) < 1:
            return "Combatant AC must be greater than 1", None
        if int(kwargs["proficiency"]) < 1:
            return "Combatant proficiency must be greater than 1", None
        if {
            int(kwargs["strength"]),
            int(kwargs["dexterity"]),
            int(kwargs["constitution"]),
            int(kwargs["wisdom"]),
            int(kwargs["intelligence"]),
            int(kwargs["charisma"]),
        }.difference(save_range):
            return "All combatant stats must be between 1 and 30", None
        combatant = Combatant(
            name=kwargs["name"],
            max_hp=int(kwargs["hp"]),
            ac=int(kwargs["ac"]),
            proficiency=int(kwargs["proficiency"]),
            str_save=floor((int(kwargs["strength"]) - 10) / 2),
            dex_save=floor((int(kwargs["dexterity"]) - 10) / 2),
            con_save=floor((int(kwargs["constitution"]) - 10) / 2),
            wis_save=floor((int(kwargs["wisdom"]) - 10) / 2),
            int_save=floor((int(kwargs["intelligence"]) - 10) / 2),
            cha_save=floor((int(kwargs["charisma"]) - 10) / 2),
            cr=float(kwargs.get("cr", 1)),
            action_names=[name for name in kwargs["actions"].split(",") if name],
        )
        return "Success", combatant

    @staticmethod
    def choose_action(action_set):
        for action in action_set:
            if not action.ready:
                action.try_recharge()
            if action.ready and action.num_available != 0:
                action.num_available -= 1
                action.ready = False
                return action
        return None

    def on_turn_start(self):
        expired = []
        for effect in list(self.applied_effects):
            if not effect.on_turn_start(self):
                expired.append(effect)
        for effect in expired:
            if effect in self.applied_effects:
                self.applied_effects.remove(effect)
        self.legendary_actions_left = self.num_legendary_actions

    def on_turn_end(self):
        expired = []
        for effect in list(self.applied_effects):
            if not effect.on_turn_end(self):
                expired.append(effect)
        for effect in expired:
            if effect in self.applied_effects:
                self.applied_effects.remove(effect)
        self.num_actions_available = 1

    def take_turn(self, allies, enemies, heuristic):
        self.on_turn_start()
        if self.hp <= 0:
            return
        while self.num_actions_available > 0:
            self.num_actions_available -= 1
            did_heal = self._try_heal(allies, heuristic)
            if not did_heal:
                self._try_attack(enemies, heuristic)
        self.on_turn_end()

    def try_legendary_action(self, enemies, heuristic):
        possible_actions = [
            action
            for action in self.legendary_actions
            if action.legendary_action_cost <= self.legendary_actions_left
        ]
        if not possible_actions:
            return
        self._try_attack(enemies, heuristic, attack=possible_actions[0])
        self.legendary_actions_left -= possible_actions[0].legendary_action_cost

    def make_attack(self, targets, attack_heuristic, attack_to_use):
        target = self._choose_target(targets, attack_heuristic)
        targets_left = targets
        if attack_to_use.is_aoe:
            targets_left = [enemy for enemy in targets if enemy != target]
        attack_to_use.do_damage(self, target)
        attack_to_use.apply_effects(target)
        return [enemy for enemy in targets_left if enemy.hp > 0]

    def _try_attack(self, enemies, heuristic, attack=None):
        if attack is None:
            attack = Combatant.choose_action(self.attacks)
        if attack is None or not enemies:
            return

        if isinstance(attack, SingleAttack):
            num_targets_hit = 1
            if attack.aoe_type:
                num_targets_hit = max(1, attack.calc_expected_enemies_hit(len(enemies)))
            for _ in range(num_targets_hit):
                if not enemies:
                    break
                enemies = self.make_attack(enemies, heuristic.attack_selection, attack)
        elif isinstance(attack, ComboAttack):
            for single_attack in attack.components:
                self._try_attack(enemies, heuristic, attack=single_attack)
        attack.ready = False

    def _try_heal(self, allies, heuristic):
        heal_target = self._check_heal_need(allies, heuristic.heal_selection)
        available_heals = [heal for heal in self.heals if heal.num_available > 0]
        healed = False
        if available_heals and heal_target:
            heal = Combatant.choose_action(self.heals)
            if heal is None:
                return False
            for _ in range(heal.num_targets):
                if heal_target is None:
                    break
                heal.do_heal(self, heal_target)
                allies = [ally for ally in allies if ally != heal_target]
                heal_target = self._check_heal_need(allies, heuristic.heal_selection)
                healed = True
        return healed

    def _choose_target(self, enemies, heuristic):
        if self.heuristics and self.heuristics.attack_selection:
            return self.heuristics.attack_selection.select(enemies)
        return heuristic.select(enemies)

    def _check_heal_need(self, allies, heuristic):
        if self.heuristics and self.heuristics.heal_selection:
            return self.heuristics.heal_selection.select(allies)
        return heuristic.select(allies)

    def take_damage(self, damage, attack_type):
        for effect in self.applied_effects:
            if (
                effect.effect_type == TYPE_RESISTANCE_TYPE
                and effect.name == attack_type
            ):
                damage *= 0.5
            if (
                effect.effect_type == TYPE_VULNERABILITY_TYPE
                and effect.name == attack_type
            ):
                damage *= 2.0
            if effect.effect_type == TYPE_IMMUNITY_TYPE and effect.name == attack_type:
                damage = 0
        self.hp -= floor(damage)

    def check_for_effect(self, effect_type):
        return any(effect.effect_type == effect_type for effect in self.applied_effects)

    def check_for_advantage(self, target):
        return any(
            effect.effect_type in SELF_ADVANTAGE_SET for effect in self.applied_effects
        ) or any(
            effect.effect_type in TARGET_ADVANTAGE_SET
            for effect in target.applied_effects
        )

    def check_for_disadvantage(self, target):
        return any(
            effect.effect_type in SELF_DISADVANTAGE_SET
            for effect in self.applied_effects
        ) or any(
            effect.effect_type in TARGET_DISADVANTAGE_SET
            for effect in target.applied_effects
        )

    def jsonify(self, jsonify_actions=False):
        return {
            "label": self.name,
            "value": self.name,
            "name": self.name,
            "hp": self.max_hp,
            "ac": self.ac,
            "proficiency": self.proficiency,
            "saves": self._convert_saves_to_dict(),
            "actions": [
                action.jsonify() if jsonify_actions else action.name
                for action in self.actions
            ],
            "innate_effects": [effect.name for effect in self.innate_effects],
            "cr": self.cr,
            "speed": self.speed,
        }

    def to_storage(self):
        return {
            "name": self.name,
            "max_hp": self.max_hp,
            "ac": self.ac,
            "proficiency": self.proficiency,
            "str_save": self.str_save,
            "dex_save": self.dex_save,
            "con_save": self.con_save,
            "wis_save": self.wis_save,
            "int_save": self.int_save,
            "cha_save": self.cha_save,
            "cr": self.cr,
            "num_legendary_actions": self.num_legendary_actions,
            "combatant_type": self.combatant_type,
            "size": self.size,
            "speed": self.speed,
            "actions": list(self.action_names),
            "innate_effects": list(self.innate_effect_names),
        }
