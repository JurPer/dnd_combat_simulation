import json
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.domain.constants import AOE_TYPES, DAMAGE_TYPES, EFFECT_TYPES
from backend.repositories.container import RepositoryContainer
from backend.services.battle_runner import BattleRunner


BASE_DIR = Path(__file__).resolve().parents[2]
repositories = RepositoryContainer(BASE_DIR / "data")
app = FastAPI(title="D&D Combat Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_team_to_list(team):
    return [
        name
        for name, payload in json.loads(team).items()
        for _ in range(int(payload["quantity"]))
    ]


def convert_list_to_team(combatants):
    result = {}
    for combatant in combatants:
        result.setdefault(combatant.name, {"quantity": 0})
        result[combatant.name]["quantity"] += 1
    return result


@app.get("/combatants")
def get_combatants():
    return [combatant.jsonify() for combatant in repositories.combatants.list()]


@app.get("/actions")
def get_actions():
    return [action.jsonify() for action in repositories.actions.list()]


@app.get("/effects")
def get_effects():
    return [effect.jsonify() for effect in repositories.effects.list()]


@app.get("/effectTypes")
def get_effect_types():
    return [
        {"value": effect_type, "label": effect_type} for effect_type in EFFECT_TYPES
    ]


@app.get("/damageTypes")
def get_damage_types():
    return [{"label": value.capitalize(), "value": value} for value in DAMAGE_TYPES]


@app.get("/aoeTypes")
def get_aoe_types():
    return [{"label": value, "value": value} for value in AOE_TYPES]


@app.post("/simulate")
def simulate(team1: str = Form(...), team2: str = Form(...)):
    if not team1 or not team2:
        return {"msg": "Both teams must have at least 1 combatant!"}
    runner = BattleRunner(repositories.combatants)
    runner.run_simulator(convert_team_to_list(team1), convert_team_to_list(team2), 200)
    return runner.get_results().to_json()


@app.post("/saveBattle")
def save_battle(team1: str = Form(...), team2: str = Form(...)):
    if not team1 or not team2:
        return {"msg": "Both teams must have at least 1 combatant!", "battleKey": ""}
    msg, battle_key = repositories.battles.save_battle(
        json.loads(team1), json.loads(team2)
    )
    return {"msg": msg, "battleKey": battle_key}


@app.post("/loadBattle")
def load_battle(battle_key: str = Form(...)):
    msg, team1, team2 = repositories.battles.load_battle(battle_key)
    return {"msg": msg, "team1": team1, "team2": team2}


@app.get("/loadCombatant/{combatant_name}/")
def load_combatant(combatant_name: str):
    combatant = repositories.combatants.get(combatant_name)
    return {"combatant": combatant.jsonify(jsonify_actions=True)}


@app.post("/createCombatant")
def create_combatant(
    name: str = Form(...),
    hp: int = Form(...),
    ac: int = Form(...),
    proficiency: int = Form(...),
    strength: int = Form(...),
    constitution: int = Form(...),
    dexterity: int = Form(...),
    wisdom: int = Form(...),
    intelligence: int = Form(...),
    charisma: int = Form(...),
    actions: str = Form(""),
):
    msg = repositories.combatants.create(
        name=name,
        hp=hp,
        ac=ac,
        proficiency=proficiency,
        strength=strength,
        constitution=constitution,
        dexterity=dexterity,
        wisdom=wisdom,
        intelligence=intelligence,
        charisma=charisma,
        actions=actions,
        cr=1,
    )
    response: dict[str, object] = {"msg": msg}
    if msg == "Success":
        response["combatants"] = [
            combatant.jsonify() for combatant in repositories.combatants.list()
        ]
    return response


@app.post("/createAction")
def create_action(
    name: str = Form(...),
    action_type: str = Form(...),
    stat_bonus: str = Form(None),
    damage_type: str = Form(None),
    bonus_to_hit: int = Form(0),
    bonus_to_damage: int = Form(0),
    multi_attack: int = Form(1),
    recharge_percentile: float = Form(0.0),
    is_legendary: str = Form("false"),
    legendary_action_cost: int = Form(0),
    save_stat: str = Form(None),
    save_dc: str = Form(None),
    is_aoe: str = Form("false"),
    aoe_type: str = Form(None),
    dice: str = Form(None),
):
    msg, action = repositories.actions.create(
        action_type,
        name=name,
        stat_bonus=stat_bonus,
        damage_type=damage_type,
        bonus_to_hit=bonus_to_hit,
        bonus_to_damage=bonus_to_damage,
        multi_attack=multi_attack,
        recharge_percentile=recharge_percentile,
        is_legendary=is_legendary,
        legendary_action_cost=legendary_action_cost,
        save_stat=save_stat,
        save_dc=save_dc,
        is_aoe=is_aoe,
        aoe_type=aoe_type,
        dice=dice,
    )
    return {
        "msg": msg,
        "actions": [item.jsonify() for item in repositories.actions.list()],
    }


@app.post("/createEffect")
def create_effect(
    name: str = Form(...),
    effect_type: str = Form(...),
    damage_dice: str = Form(None),
    save_dc: str = Form(None),
    save_stat: str = Form(None),
    num_turns: int = Form(...),
):
    effect, msg = repositories.effects.create(
        name=name,
        effect_type=effect_type,
        damage_dice=damage_dice,
        save_dc=save_dc,
        save_stat=save_stat,
        max_turns=num_turns,
    )
    response: dict[str, object] = {"msg": msg}
    if effect is not None:
        response["effect"] = effect.jsonify()
    return response


@app.post("/ddbImport")
def ddb_import(url: str = Form(...)):
    return {
        "msg": "D&D Beyond import is not supported in the migrated JSON backend yet."
    }
