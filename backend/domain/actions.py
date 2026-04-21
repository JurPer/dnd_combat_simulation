from dataclasses import dataclass, field
from math import ceil
from typing import Any, Optional, TypedDict

from backend.domain.constants import (
    AOE_PERCENT_HIT_MAP,
    DAMAGE_TYPES,
    PARALYZE_EFFECT_TYPE,
)
from backend.domain.dice import calc_roll, d20, serialize_dice


class ActionKwargs(TypedDict):
    name: str
    action_type: str
    description: Optional[str]
    recharge_percentile: float
    stat_bonus: Optional[str]
    is_legendary: bool
    legendary_action_cost: int
    effect_names: list[str]


class AttackKwargs(ActionKwargs):
    multi_attack: int
    is_aoe: bool
    aoe_type: Optional[str]
    damage_type: str
    save_stat: Optional[str]
    save_dc: Optional[int]
    dice: dict
    bonus_to_hit: int
    bonus_to_damage: int


def calc_attack_roll(attacker, target):
    has_advantage = attacker.check_for_advantage(target)
    has_disadvantage = attacker.check_for_disadvantage(target)
    if has_advantage and not has_disadvantage:
        return max(d20(), d20())
    if has_disadvantage and not has_advantage:
        return min(d20(), d20())
    return d20()


@dataclass
class Action:
    name: str
    action_type: str
    description: Optional[str] = None
    recharge_percentile: float = 0.0
    stat_bonus: Optional[str] = None
    is_legendary: bool = False
    legendary_action_cost: int = 0
    effect_names: list[str] = field(default_factory=list)
    effects: list[Any] = field(default_factory=list)
    ready: bool = field(default=True, init=False)
    num_available: int = field(default=-1, init=False)

    def instantiate(self) -> "Action":
        copy = self.copy()
        copy.ready = True
        copy.num_available = -1
        copy.effects = [effect.instantiate() for effect in self.effects]
        return copy

    def copy(self) -> "Action":
        return Action(
            name=self.name,
            action_type=self.action_type,
            description=self.description,
            recharge_percentile=self.recharge_percentile,
            stat_bonus=self.stat_bonus,
            is_legendary=self.is_legendary,
            legendary_action_cost=self.legendary_action_cost,
            effect_names=list(self.effect_names),
            effects=[effect.copy() for effect in self.effects],
        )

    def try_recharge(self):
        from random import random

        if random() >= self.recharge_percentile:
            self.ready = True

    def jsonify(self, current_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        current_info = current_info or {}
        return {
            **current_info,
            "label": self.name,
            "value": self.name,
            "name": self.name,
            "actionEffects": [e.name for e in self.effects],
            "description": self.description,
        }

    def to_storage(self) -> dict[str, Any]:
        return {
            "kind": "Action",
            "name": self.name,
            "action_type": self.action_type,
            "description": self.description,
            "recharge_percentile": self.recharge_percentile,
            "stat_bonus": self.stat_bonus,
            "is_legendary": self.is_legendary,
            "legendary_action_cost": self.legendary_action_cost,
            "effects": list(self.effect_names),
        }


@dataclass
class SingleAttack(Action):
    multi_attack: int = 1
    is_aoe: bool = False
    aoe_type: Optional[str] = None
    damage_type: Optional[str] = None
    save_stat: Optional[str] = None
    save_dc: Optional[int] = None
    dice: dict = field(default_factory=dict)
    bonus_to_hit: int = 0
    bonus_to_damage: int = 0

    def instantiate(self) -> "SingleAttack":
        copy = self.copy()
        copy.ready = True
        copy.num_available = -1
        copy.effects = [effect.instantiate() for effect in self.effects]
        return copy

    def copy(self) -> "SingleAttack":
        return type(self)(
            name=self.name,
            action_type=self.action_type,
            description=self.description,
            recharge_percentile=self.recharge_percentile,
            stat_bonus=self.stat_bonus,
            is_legendary=self.is_legendary,
            legendary_action_cost=self.legendary_action_cost,
            effect_names=list(self.effect_names),
            effects=[effect.copy() for effect in self.effects],
            multi_attack=self.multi_attack,
            is_aoe=self.is_aoe,
            aoe_type=self.aoe_type,
            damage_type=self.damage_type,
            save_stat=self.save_stat,
            save_dc=self.save_dc,
            dice=dict(self.dice),
            bonus_to_hit=self.bonus_to_hit,
            bonus_to_damage=self.bonus_to_damage,
        )

    def calc_expected_enemies_hit(self, num_enemies: int) -> int:
        if self.is_aoe and self.aoe_type:
            return AOE_PERCENT_HIT_MAP[self.aoe_type](num_enemies)
        return self.multi_attack

    def calc_expected_damage(self, num_enemies=1):
        expected_enemies_hit = self.calc_expected_enemies_hit(num_enemies)
        return expected_enemies_hit * sum(
            num_dice * (int(max_roll) / 2.0 + 0.5)
            for max_roll, num_dice in self.dice.items()
        )

    def apply_effects(self, target):
        for effect in self.effects:
            effect.apply(target)

    def log_attack(self, attacker, target, damage):
        return None

    def jsonify(self, current_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        info = {"expDamage": self.calc_expected_damage()}
        return super().jsonify({**(current_info or {}), **info})

    def to_storage(self) -> dict[str, Any]:
        base: dict[str, Any] = super().to_storage()
        base.update(
            {
                "multi_attack": self.multi_attack,
                "is_aoe": self.is_aoe,
                "aoe_type": self.aoe_type,
                "damage_type": self.damage_type,
                "save_stat": self.save_stat,
                "save_dc": self.save_dc,
                "dice": serialize_dice(self.dice),
                "bonus_to_hit": self.bonus_to_hit,
                "bonus_to_damage": self.bonus_to_damage,
            }
        )
        return base


@dataclass
class PhysicalSingleAttack(SingleAttack):
    def do_damage(self, attacker, target):
        damage = 0
        die_roll = calc_attack_roll(attacker, target)
        hit_check = (
            die_roll
            + attacker.saves[self.stat_bonus]
            + self.bonus_to_hit
            + attacker.proficiency
        )
        if hit_check >= target.ac or die_roll == 20:
            roll_damage = calc_roll(self.dice)
            if die_roll == 20 or target.check_for_effect(PARALYZE_EFFECT_TYPE):
                roll_damage *= 2
            damage = (
                roll_damage + attacker.saves[self.stat_bonus] + self.bonus_to_damage
            )
        target.take_damage(damage, self.damage_type)
        self.log_attack(attacker, target, damage)

    def to_storage(self) -> dict[str, Any]:
        base = super().to_storage()
        base["kind"] = "PhysicalSingleAttack"
        return base


@dataclass
class SpellSingleAttack(SingleAttack):
    def do_damage(self, attacker, target):
        damage = 0
        if self.stat_bonus is not None:
            attack_bonus = attacker.proficiency + attacker.saves[self.stat_bonus]
            die_roll = calc_attack_roll(attacker, target)
            hit_check = die_roll + attack_bonus + self.bonus_to_hit
            if hit_check >= target.ac or die_roll == 20:
                roll_damage = calc_roll(self.dice)
                if die_roll == 20:
                    roll_damage *= 2
                damage = roll_damage + self.bonus_to_damage
        else:
            save_check = d20() + target.saves[self.save_stat]
            if save_check <= self.save_dc:
                damage = calc_roll(self.dice) + self.bonus_to_damage
        target.take_damage(damage, self.damage_type)
        self.log_attack(attacker, target, damage)

    def to_storage(self) -> dict[str, Any]:
        base = super().to_storage()
        base["kind"] = "SpellSingleAttack"
        return base


@dataclass
class SpellSave(SingleAttack):
    def do_damage(self, attacker, target):
        save_check = d20() + target.saves[self.save_stat]
        damage = calc_roll(self.dice)
        if save_check > self.save_dc:
            damage = ceil(damage / 2.0)
        target.take_damage(damage, self.damage_type)
        self.log_attack(attacker, target, damage)

    def to_storage(self) -> dict[str, Any]:
        base = super().to_storage()
        base["kind"] = "SpellSave"
        return base


@dataclass
class Heal(Action):
    dice: dict = field(default_factory=dict)
    num_targets: int = 1

    def copy(self) -> "Heal":
        return Heal(
            name=self.name,
            action_type=self.action_type,
            description=self.description,
            recharge_percentile=self.recharge_percentile,
            stat_bonus=self.stat_bonus,
            is_legendary=self.is_legendary,
            legendary_action_cost=self.legendary_action_cost,
            effect_names=list(self.effect_names),
            effects=[effect.copy() for effect in self.effects],
            dice=dict(self.dice),
            num_targets=self.num_targets,
        )

    def do_heal(self, healer, healed):
        health_up = calc_roll(self.dice) + (
            healer.saves[self.stat_bonus] if self.stat_bonus else 0
        )
        healed.hp = min(healed.hp + health_up, healed.max_hp)

    def calc_expected_heal(self):
        return self.num_targets * sum(
            num_dice * (int(max_roll) / 2.0 + 0.5)
            for max_roll, num_dice in self.dice.items()
        )

    def jsonify(self, current_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        info = {"expHeal": self.calc_expected_heal()}
        return super().jsonify({**(current_info or {}), **info})

    def to_storage(self) -> dict[str, Any]:
        base: dict[str, Any] = super().to_storage()
        base.update(
            {
                "kind": "Heal",
                "dice": serialize_dice(self.dice),
                "num_targets": self.num_targets,
            }
        )
        return base


@dataclass
class ComboAttack(Action):
    component_names: list[str] = field(default_factory=list)
    components: list[SingleAttack] = field(default_factory=list)

    def instantiate(self) -> "ComboAttack":
        copy = self.copy()
        copy.ready = True
        copy.num_available = -1
        copy.components = [component.instantiate() for component in self.components]
        return copy

    def copy(self) -> "ComboAttack":
        return ComboAttack(
            name=self.name,
            action_type=self.action_type,
            description=self.description,
            recharge_percentile=self.recharge_percentile,
            stat_bonus=self.stat_bonus,
            is_legendary=self.is_legendary,
            legendary_action_cost=self.legendary_action_cost,
            effect_names=list(self.effect_names),
            effects=[effect.copy() for effect in self.effects],
            component_names=list(self.component_names),
            components=[component.copy() for component in self.components],
        )

    def calc_expected_damage(self, num_enemies=1):
        return sum(
            component.calc_expected_damage(num_enemies) for component in self.components
        )

    def to_storage(self):
        base = super().to_storage()
        base.update({"kind": "ComboAttack", "components": list(self.component_names)})
        return base

    def jsonify(self, current_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        info = {"expDamage": self.calc_expected_damage()}
        return super().jsonify({**(current_info or {}), **info})


def create_action(action_type, **kwargs):
    name = kwargs.get("name")
    if not name:
        return "Action needs a name", None

    effect_names = kwargs.get("effects", [])
    if isinstance(effect_names, str):
        effect_names = [effect_names] if effect_names else []

    base_kwargs: ActionKwargs = {
        "name": name,
        "action_type": "Heal" if action_type == "Heal" else "Attack",
        "description": kwargs.get("description"),
        "recharge_percentile": float(kwargs.get("recharge_percentile", 0.0) or 0.0),
        "stat_bonus": kwargs.get("stat_bonus") or None,
        "is_legendary": str(kwargs.get("is_legendary", "false")).lower() == "true",
        "legendary_action_cost": int(kwargs.get("legendary_action_cost", 0) or 0),
        "effect_names": effect_names,
    }

    if base_kwargs["is_legendary"] and base_kwargs["legendary_action_cost"] == 0:
        return "An action cannot be legendary and have 0 legendary cost", None

    if action_type == "Heal":
        if not kwargs.get("dice"):
            return "dice argument must be provided and formatted correctly", None
        action = Heal(
            **base_kwargs,
            dice=kwargs["dice"],
            num_targets=int(kwargs.get("num_targets", 1) or 1),
        )
        return "Success", action

    if action_type not in {
        "PhysicalSingleAttack",
        "SpellSingleAttack",
        "SpellSave",
        "ComboAttack",
    }:
        return (
            f"Action.create_action did not receive a valid action_type received {action_type}",
            None,
        )

    if action_type == "ComboAttack":
        components = kwargs.get("components", [])
        if not components:
            return "ComboAttack requires at least one component", None
        action = ComboAttack(
            **base_kwargs,
            component_names=list(components),
        )
        return "Success", action

    damage_type = kwargs.get("damage_type")
    if damage_type not in DAMAGE_TYPES:
        return f"{damage_type} is not a valid damage type", None
    if not kwargs.get("dice"):
        return "dice argument must be provided and formatted correctly", None

    attack_kwargs: AttackKwargs = {
        **base_kwargs,
        "multi_attack": int(kwargs.get("multi_attack", 1) or 1),
        "is_aoe": str(kwargs.get("is_aoe", "false")).lower() == "true",
        "aoe_type": kwargs.get("aoe_type") or None,
        "damage_type": damage_type,
        "save_stat": kwargs.get("save_stat") or None,
        "save_dc": int(kwargs["save_dc"])
        if kwargs.get("save_dc") not in (None, "")
        else None,
        "dice": kwargs["dice"],
        "bonus_to_hit": int(kwargs.get("bonus_to_hit", 0) or 0),
        "bonus_to_damage": int(kwargs.get("bonus_to_damage", 0) or 0),
    }

    if action_type == "PhysicalSingleAttack":
        return "Success", PhysicalSingleAttack(**attack_kwargs)
    if action_type == "SpellSingleAttack":
        return "Success", SpellSingleAttack(**attack_kwargs)
    return "Success", SpellSave(**attack_kwargs)
