import json
import re
from pathlib import Path


def slugify(value):
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned or "item"


class JsonDirectoryRepository:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for_name(self, name):
        return self.directory / f"{slugify(name)}.json"

    def _list_payloads(self):
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(self.directory.glob("*.json"))
        ]

    def _write_payload(self, name, payload):
        path = self._path_for_name(name)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
