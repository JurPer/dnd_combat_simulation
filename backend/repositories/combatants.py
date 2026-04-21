from backend.domain.combatants import Combatant
from backend.repositories.base import JsonDirectoryRepository


class CombatantRepository(JsonDirectoryRepository):
    def __init__(self, directory, action_repository, effect_repository):
        super().__init__(directory)
        self.action_repository = action_repository
        self.effect_repository = effect_repository

    def list(self):
        return [self._from_payload(payload) for payload in self._list_payloads()]

    def get(self, name):
        for combatant in self.list():
            if combatant.name == name:
                return combatant
        raise KeyError(f"Combatant {name} not found")

    def exists(self, name):
        try:
            self.get(name)
            return True
        except KeyError:
            return False

    def save(self, combatant):
        self._write_payload(combatant.name, combatant.to_storage())

    def create(self, **kwargs):
        msg, combatant = Combatant.create(**kwargs)
        if combatant is None:
            return msg
        if self.exists(combatant.name):
            return "Combatant needs a unique name"
        missing_actions = [
            name
            for name in combatant.action_names
            if not self.action_repository.exists(name)
        ]
        if missing_actions:
            return f"Could not find action with name {missing_actions[0]}"
        self.save(combatant)
        return "Success"

    def get_prepared(self, name, name_suffix="", heuristics=None, num_enemies=1):
        combatant = self.get(name).copy()
        if name_suffix:
            combatant.name = f"{combatant.name}_{name_suffix}"
        combatant.prepare_for_battle(heuristics=heuristics, num_enemies=num_enemies)
        return combatant

    def _from_payload(self, payload):
        combatant = Combatant(
            name=payload["name"],
            max_hp=payload["max_hp"],
            ac=payload["ac"],
            proficiency=payload["proficiency"],
            str_save=payload["str_save"],
            dex_save=payload["dex_save"],
            con_save=payload["con_save"],
            wis_save=payload["wis_save"],
            int_save=payload["int_save"],
            cha_save=payload["cha_save"],
            cr=payload["cr"],
            num_legendary_actions=payload.get("num_legendary_actions", 0),
            combatant_type=payload.get("combatant_type"),
            size=payload.get("size"),
            speed=payload.get("speed"),
            action_names=list(payload.get("actions", [])),
            innate_effect_names=list(payload.get("innate_effects", [])),
        )
        combatant.actions = [
            self.action_repository.get(name) for name in combatant.action_names
        ]
        combatant.innate_effects = [
            self.effect_repository.get(name) for name in combatant.innate_effect_names
        ]
        return combatant
