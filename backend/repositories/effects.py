from backend.domain.dice import parse_dice_str
from backend.domain.effects import Effect, create_effect
from backend.repositories.base import JsonDirectoryRepository


class EffectRepository(JsonDirectoryRepository):
    def list(self):
        return [self._from_payload(payload) for payload in self._list_payloads()]

    def get(self, name):
        for effect in self.list():
            if effect.name == name:
                return effect
        raise KeyError(f"Effect {name} not found")

    def exists(self, name):
        try:
            self.get(name)
            return True
        except KeyError:
            return False

    def save(self, effect):
        self._write_payload(effect.name, effect.to_storage())

    def create(self, **kwargs):
        damage_dice = kwargs.get("damage_dice")
        parsed_damage_dice = damage_dice if isinstance(damage_dice, dict) else parse_dice_str(damage_dice)
        effect, msg = create_effect(
            name=kwargs["name"],
            effect_type=kwargs["effect_type"],
            max_turns=int(kwargs["max_turns"]),
            save_stat=kwargs.get("save_stat"),
            save_dc=int(kwargs["save_dc"]) if kwargs.get("save_dc") not in (None, "") else None,
            damage_dice=parsed_damage_dice,
        )
        if effect is None:
            return None, msg
        if self.exists(effect.name):
            return None, "Effect needs a unique name"
        self.save(effect)
        return effect, "Success"

    @staticmethod
    def _from_payload(payload):
        return Effect(
            name=payload["name"],
            effect_type=payload["effect_type"],
            description=payload.get("description"),
            max_turns=payload.get("max_turns", -1),
            save_stat=payload.get("save_stat"),
            save_dc=payload.get("save_dc"),
            damage_dice={int(k): v for k, v in (payload.get("damage_dice") or {}).items()},
        )
