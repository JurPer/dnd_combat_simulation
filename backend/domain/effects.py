from dataclasses import dataclass, field
from typing import Optional

from backend.domain.constants import (
    BLINDED_EFFECT_TYPE,
    DOT_EFFECT_TYPE,
    EFFECT_TYPES,
    INVISIBLE_EFFECT_TYPE,
    PARALYZE_EFFECT_TYPE,
    PETRIFIED_EFFECT_TYPE,
    POISONED_EFFECT_TYPE,
    PRONE_EFFECT_TYPE,
    RESTRAINED_EFFECT_TYPE,
    STUN_EFFECT_TYPE,
    TYPE_IMMUNITY_TYPE,
    TYPE_RESISTANCE_TYPE,
    TYPE_VULNERABILITY_TYPE,
)
from backend.domain.dice import calc_roll, d20, serialize_dice


@dataclass
class Effect:
    name: str
    effect_type: str
    description: Optional[str] = None
    max_turns: int = -1
    save_stat: Optional[str] = None
    save_dc: Optional[int] = None
    damage_dice: Optional[dict] = None
    turns_left: int = field(default=-1, init=False)

    def instantiate(self):
        copy = self.copy()
        copy.turns_left = copy.max_turns
        return copy

    def copy(self):
        return Effect(
            name=self.name,
            effect_type=self.effect_type,
            description=self.description,
            max_turns=self.max_turns,
            save_stat=self.save_stat,
            save_dc=self.save_dc,
            damage_dice=dict(self.damage_dice or {}),
        )

    def apply(self, creature):
        if self.effect_type in {
            TYPE_RESISTANCE_TYPE,
            TYPE_IMMUNITY_TYPE,
            TYPE_VULNERABILITY_TYPE,
            INVISIBLE_EFFECT_TYPE,
        }:
            creature.applied_effects.append(self.instantiate())
            return

        if self.save_stat and self.save_dc is not None:
            save_attempt = d20() + creature.saves[self.save_stat]
            if save_attempt >= self.save_dc:
                return
        creature.applied_effects.append(self.instantiate())

    def on_turn_start(self, creature):
        if self.effect_type == STUN_EFFECT_TYPE:
            creature.num_actions_available = 0
            self.turns_left -= 1
            return True
        if self.effect_type == DOT_EFFECT_TYPE:
            creature.hp -= calc_roll(self.damage_dice or {})
            self.turns_left -= 1
            return True
        if self.effect_type == PRONE_EFFECT_TYPE:
            return False
        if self.effect_type in {
            POISONED_EFFECT_TYPE,
            BLINDED_EFFECT_TYPE,
            INVISIBLE_EFFECT_TYPE,
        }:
            self.turns_left -= 1
            return True
        if self.effect_type == PETRIFIED_EFFECT_TYPE:
            save_attempt = d20() + creature.saves[self.save_stat]
            return save_attempt < self.save_dc
        return True

    def on_turn_end(self, creature):
        if self.effect_type in {
            TYPE_RESISTANCE_TYPE,
            TYPE_IMMUNITY_TYPE,
            TYPE_VULNERABILITY_TYPE,
        }:
            return True
        if self.effect_type in {
            STUN_EFFECT_TYPE,
            PARALYZE_EFFECT_TYPE,
            DOT_EFFECT_TYPE,
        }:
            if self.turns_left <= 0:
                return False
            if self.save_stat and self.save_dc is not None:
                save_attempt = d20() + creature.saves[self.save_stat]
                return save_attempt < self.save_dc
            return True
        if self.effect_type == RESTRAINED_EFFECT_TYPE:
            if self.save_stat and self.save_dc is not None:
                save_attempt = d20() + creature.saves[self.save_stat]
                return save_attempt < self.save_dc
            return True
        if self.effect_type == INVISIBLE_EFFECT_TYPE:
            if self.turns_left <= 0:
                return False
            return creature.num_actions_available > 0
        if self.effect_type == PRONE_EFFECT_TYPE:
            return False
        if self.effect_type in {
            POISONED_EFFECT_TYPE,
            BLINDED_EFFECT_TYPE,
            PETRIFIED_EFFECT_TYPE,
        }:
            return self.turns_left > 0
        return self.turns_left != 0

    def jsonify(self):
        return {
            "label": self.name,
            "value": self.name,
            "name": self.name,
            "type": self.effect_type,
            "description": self.description,
        }

    def to_storage(self):
        return {
            "name": self.name,
            "effect_type": self.effect_type,
            "description": self.description,
            "max_turns": self.max_turns,
            "save_stat": self.save_stat,
            "save_dc": self.save_dc,
            "damage_dice": serialize_dice(self.damage_dice),
        }


def create_effect(
    name, effect_type, max_turns, save_stat=None, save_dc=None, damage_dice=None
):
    if not name:
        return None, "Name must be non-empty"
    if effect_type not in EFFECT_TYPES and effect_type not in {
        TYPE_RESISTANCE_TYPE,
        TYPE_IMMUNITY_TYPE,
        TYPE_VULNERABILITY_TYPE,
    }:
        return None, f"Unaccounted for effect type: {effect_type}"
    if effect_type != INVISIBLE_EFFECT_TYPE and max_turns <= 0:
        return None, "Effect must last for at least 1 turn"

    if effect_type == DOT_EFFECT_TYPE and not damage_dice:
        return None, "DOT effects require damage dice"

    if effect_type in {
        STUN_EFFECT_TYPE,
        PARALYZE_EFFECT_TYPE,
        PRONE_EFFECT_TYPE,
        POISONED_EFFECT_TYPE,
        BLINDED_EFFECT_TYPE,
        RESTRAINED_EFFECT_TYPE,
        PETRIFIED_EFFECT_TYPE,
        DOT_EFFECT_TYPE,
    } and (not save_stat or save_dc is None):
        return None, "This effect requires save_stat and save_dc"

    if effect_type == INVISIBLE_EFFECT_TYPE:
        description = "Makes target invisible"
    elif effect_type == DOT_EFFECT_TYPE:
        description = (
            f"{damage_dice} damage per turn with a DC {save_dc} {save_stat} save"
        )
    elif effect_type in {
        STUN_EFFECT_TYPE,
        PARALYZE_EFFECT_TYPE,
        PRONE_EFFECT_TYPE,
        POISONED_EFFECT_TYPE,
        BLINDED_EFFECT_TYPE,
        RESTRAINED_EFFECT_TYPE,
        PETRIFIED_EFFECT_TYPE,
    }:
        verb_map = {
            STUN_EFFECT_TYPE: "Stuns",
            PARALYZE_EFFECT_TYPE: "Paralyzes",
            PRONE_EFFECT_TYPE: "Knocks target prone",
            POISONED_EFFECT_TYPE: "Poisons",
            BLINDED_EFFECT_TYPE: "Blinds",
            RESTRAINED_EFFECT_TYPE: "Restrains",
            PETRIFIED_EFFECT_TYPE: "Petrifies",
        }
        description = f"{verb_map[effect_type]} if the target fails a DC {save_dc} {save_stat} save"
    else:
        description = effect_type

    return Effect(
        name=name,
        effect_type=effect_type,
        description=description,
        max_turns=max_turns,
        save_stat=save_stat,
        save_dc=save_dc,
        damage_dice=damage_dice,
    ), "Success"
