import statistics
from dataclasses import dataclass, field

from backend.services.heuristics import HEURISTIC_MAPPING, HeuristicContainer
from backend.services.simulator import Simulator


@dataclass
class ResultContainer:
    num_sims: int = 0
    number_of_rounds: list = field(default_factory=list)
    number_of_player_deaths: list = field(default_factory=list)
    winning_teams: list = field(default_factory=list)

    def to_json(self):
        players_won = [
            self.number_of_rounds[i]
            for i in range(self.num_sims)
            if self.winning_teams[i] == 0
        ]
        monsters_won = [
            self.number_of_rounds[i]
            for i in range(self.num_sims)
            if self.winning_teams[i] == 1
        ]
        avg_num_rounds = (
            statistics.mean(self.number_of_rounds) if self.number_of_rounds else 0
        )
        avg_t1_deaths = (
            statistics.mean(self.number_of_player_deaths)
            if self.number_of_player_deaths
            else 0
        )
        at_least_1_t1_death = len(
            [value for value in self.number_of_player_deaths if value > 0]
        )
        perc_times_t1_won = (
            1 - statistics.mean(self.winning_teams) if self.winning_teams else 0
        )
        avg_num_round_when_t1_won = statistics.mean(players_won) if players_won else 0
        avg_num_round_when_t2_won = statistics.mean(monsters_won) if monsters_won else 0
        return {
            "avg_num_rounds": f"{avg_num_rounds:.2f}",
            "avg_t1_deaths": f"{avg_t1_deaths:.2f}",
            "num_times_at_least_one_t1_death": at_least_1_t1_death,
            "perc_time_t1_won": f"{perc_times_t1_won:.2f}",
            "avg_num_round_when_t1_won": f"{avg_num_round_when_t1_won:.2f}",
            "avg_num_round_when_t2_won": f"{avg_num_round_when_t2_won:.2f}",
        }


class BattleRunner:
    def __init__(self, combatant_repository):
        self.combatant_repository = combatant_repository
        self.res = ResultContainer()

    def run_simulator(
        self,
        team1_names,
        team2_names,
        num_sims,
        attack_heuristic="Random",
        heal_heuristic="LowestHealth",
    ):
        self.res = ResultContainer(num_sims=num_sims)
        heuristics = HeuristicContainer(
            attack_selection=HEURISTIC_MAPPING[attack_heuristic](),
            heal_selection=HEURISTIC_MAPPING[heal_heuristic](),
        )

        team1 = [
            self.combatant_repository.get_prepared(
                name,
                name_suffix=f"t1_{index}",
                heuristics=heuristics,
                num_enemies=len(team2_names),
            )
            for index, name in enumerate(team1_names)
        ]
        team2 = [
            self.combatant_repository.get_prepared(
                name,
                name_suffix=f"t2_{index}",
                heuristics=heuristics,
                num_enemies=len(team1_names),
            )
            for index, name in enumerate(team2_names)
        ]

        for _ in range(num_sims):
            sim = Simulator(team1, team2)
            num_rounds, num_player_deaths, winning_team = sim.run_battle(heuristics)
            self.res.number_of_rounds.append(num_rounds)
            self.res.number_of_player_deaths.append(num_player_deaths)
            self.res.winning_teams.append(winning_team)

    def get_results(self):
        return self.res
