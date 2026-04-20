from backend.domain.actions import (
    ComboAttack,
    Heal,
    PhysicalSingleAttack,
    SpellSave,
    SpellSingleAttack,
    create_action,
)
from backend.domain.dice import parse_dice_str
from backend.repositories.base import JsonDirectoryRepository


class ActionRepository(JsonDirectoryRepository):
    def __init__(self, directory, effect_repository):
        super().__init__(directory)
        self.effect_repository = effect_repository

    def list(self):
        payloads = self._list_payloads()
        payload_map = {payload["name"]: payload for payload in payloads}
        return [self._from_payload(payload, payload_map) for payload in payloads]

    def get(self, name):
        payloads = self._list_payloads()
        payload_map = {payload["name"]: payload for payload in payloads}
        for payload in payloads:
            if payload["name"] == name:
                return self._from_payload(payload, payload_map)
        raise KeyError(f"Action {name} not found")

    def exists(self, name):
        try:
            self.get(name)
            return True
        except KeyError:
            return False

    def save(self, action):
        self._write_payload(action.name, action.to_storage())

    def create(self, action_type, **kwargs):
        kwargs = dict(kwargs)
        kwargs["dice"] = kwargs["dice"] if isinstance(kwargs.get("dice"), dict) else parse_dice_str(kwargs.get("dice"))
        effect_names = kwargs.get("effects", [])
        if isinstance(effect_names, str):
            effect_names = [effect_names] if effect_names else []
        kwargs["effects"] = effect_names

        msg, action = create_action(action_type, **kwargs)
        if action is None:
            return msg, None
        if self.exists(action.name):
            return "Action needs a unique name", None

        missing_effects = [name for name in effect_names if not self.effect_repository.exists(name)]
        if missing_effects:
            return f"Could not find effects with names: {', '.join(missing_effects)}", None

        self.save(action)
        return "Success", action

    def _from_payload(self, payload, payload_map):
        base_kwargs = dict(
            name=payload["name"],
            action_type=payload.get("action_type", "Attack"),
            description=payload.get("description"),
            recharge_percentile=payload.get("recharge_percentile", 0.0),
            stat_bonus=payload.get("stat_bonus"),
            is_legendary=payload.get("is_legendary", False),
            legendary_action_cost=payload.get("legendary_action_cost", 0),
            effect_names=list(payload.get("effects", [])),
            effects=[self.effect_repository.get(name) for name in payload.get("effects", [])],
        )

        kind = payload["kind"]
        if kind == "PhysicalSingleAttack":
            return PhysicalSingleAttack(
                **base_kwargs,
                multi_attack=payload.get("multi_attack", 1),
                is_aoe=payload.get("is_aoe", False),
                aoe_type=payload.get("aoe_type"),
                damage_type=payload.get("damage_type"),
                save_stat=payload.get("save_stat"),
                save_dc=payload.get("save_dc"),
                dice={int(k): v for k, v in (payload.get("dice") or {}).items()},
                bonus_to_hit=payload.get("bonus_to_hit", 0),
                bonus_to_damage=payload.get("bonus_to_damage", 0),
            )
        if kind == "SpellSingleAttack":
            return SpellSingleAttack(
                **base_kwargs,
                multi_attack=payload.get("multi_attack", 1),
                is_aoe=payload.get("is_aoe", False),
                aoe_type=payload.get("aoe_type"),
                damage_type=payload.get("damage_type"),
                save_stat=payload.get("save_stat"),
                save_dc=payload.get("save_dc"),
                dice={int(k): v for k, v in (payload.get("dice") or {}).items()},
                bonus_to_hit=payload.get("bonus_to_hit", 0),
                bonus_to_damage=payload.get("bonus_to_damage", 0),
            )
        if kind == "SpellSave":
            return SpellSave(
                **base_kwargs,
                multi_attack=payload.get("multi_attack", 1),
                is_aoe=payload.get("is_aoe", False),
                aoe_type=payload.get("aoe_type"),
                damage_type=payload.get("damage_type"),
                save_stat=payload.get("save_stat"),
                save_dc=payload.get("save_dc"),
                dice={int(k): v for k, v in (payload.get("dice") or {}).items()},
                bonus_to_hit=payload.get("bonus_to_hit", 0),
                bonus_to_damage=payload.get("bonus_to_damage", 0),
            )
        if kind == "Heal":
            return Heal(
                **base_kwargs,
                dice={int(k): v for k, v in (payload.get("dice") or {}).items()},
                num_targets=payload.get("num_targets", 1),
            )
        if kind == "ComboAttack":
            component_names = list(payload.get("components", []))
            return ComboAttack(
                **base_kwargs,
                component_names=component_names,
                components=[self._from_payload(payload_map[name], payload_map) for name in component_names],
            )
        raise ValueError(f"Unknown action kind {kind}")
