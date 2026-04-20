import secrets

from backend.repositories.base import JsonDirectoryRepository


class BattleRepository(JsonDirectoryRepository):
    def save_battle(self, team1, team2):
        battle_key = secrets.token_urlsafe(24)
        payload = {"battle_key": battle_key, "team1": team1, "team2": team2}
        self._write_payload(battle_key, payload)
        return "Successfully saved", battle_key

    def load_battle(self, battle_key):
        for payload in self._list_payloads():
            if payload["battle_key"] == battle_key:
                return "Success", payload["team1"], payload["team2"]
        return f"Could not find battle with key {battle_key}", {}, {}
