from copy import deepcopy

from backend.domain.dice import d20


class Simulator:
    def __init__(self, pcs, enemies):
        self.pcs = deepcopy(pcs)
        self.enemies = deepcopy(enemies)
        self.legendary_action_users = [
            combatant
            for combatant in self.pcs + self.enemies
            if combatant.legendary_actions
        ]
        self.battle_order = None

        for pc in self.pcs:
            pc.enemies = self.enemies
            pc.allies = [ally for ally in self.pcs if ally is not pc]
        for enemy in self.enemies:
            enemy.enemies = self.pcs
            enemy.allies = [ally for ally in self.enemies if ally is not enemy]

    def calc_initiative(self):
        pc_initiative = [(pc, d20() + pc.saves["DEX"]) for pc in self.pcs]
        enemy_initiative = [(enemy, d20() + enemy.saves["DEX"]) for enemy in self.enemies]
        self.battle_order = [
            (turn[0], 0 if turn[0] in self.pcs else 1)
            for turn in sorted(pc_initiative + enemy_initiative, key=lambda value: value[1], reverse=True)
        ]

    def run_round(self, heuristic):
        for creature, team in list(self.battle_order):
            if creature.hp <= 0:
                continue
            allies = [entry[0] for entry in self.battle_order if entry[1] == team and entry[0].hp > 0]
            enemies = [entry[0] for entry in self.battle_order if entry[1] != team and entry[0].hp > 0]
            if not enemies:
                break
            creature.take_turn(allies, enemies, heuristic)
            for legendary_action_user in self.legendary_action_users:
                legendary_action_user.try_legendary_action(
                    legendary_action_user.enemies, heuristic
                )

        dead_enemies = [combatant.name for combatant in self.enemies if combatant.hp <= 0]
        dead_pcs = [combatant.name for combatant in self.pcs if combatant.hp <= 0]

        self.battle_order = [entry for entry in self.battle_order if entry[0].hp > 0]
        self.enemies = [combatant for combatant in self.enemies if combatant.hp > 0]
        self.pcs = [combatant for combatant in self.pcs if combatant.hp > 0]
        return dead_enemies, dead_pcs

    def run_battle(self, heuristic):
        num_player_deaths = 0
        round_num = 0
        self.calc_initiative()
        while self.enemies and self.pcs:
            enemies_dead, players_dead = self.run_round(heuristic)
            if players_dead:
                num_player_deaths += len(players_dead)
            round_num += 1
        winning_team = 0 if self.pcs else 1
        return round_num, num_player_deaths, winning_team
