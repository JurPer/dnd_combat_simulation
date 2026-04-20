import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db.sqlite3"
DATA_DIR = ROOT / "data"


def write_payload(directory, name, payload):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_if_present():
    if not DB_PATH.exists():
        print("No db.sqlite3 file found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    counts = {}
    for table in ["actors_combatant", "actions_action", "effects_effect"]:
        counts[table] = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]

    if not any(counts.values()):
        print("Database is empty; nothing to export.")
        return

    print("Legacy export is not fully implemented for polymorphic Django rows.")
    print("Counts:", counts)


if __name__ == "__main__":
    export_if_present()
