import requests
from pprint import pprint
import re


class FPLQuerier:
    FPL_GENERAL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
    FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
    FPL_ENTRY_URL = "https://fantasy.premierleague.com/api/entry/"
    FPL_ENTRY_HISTORY_URL = "https://fantasy.premierleague.com/api/entry/{}/history/"
    FPL_ELEMENT_SUMMARY_URL = (
        "https://fantasy.premierleague.com/api/element-summary/{}/"
    )

    teams = {}
    data = {}

    @staticmethod
    def get_team_difficulty(team_code: str):
        team_code = team_code.upper()
        if team_code == "LUT":
            return 1
        elif team_code in ("ARS", "LIV", "MCI"):
            return 5
        elif team_code in ("NEW", "BHA", "BRE", "AVL", "CHE", "TOT"):
            return 4
        elif team_code in ("BUR", "SHE", "WOL", "EVE", "BOU"):
            return 2
        else:
            return 3

    def refresh(self):
        """
        Refreshes data
        """
        self.data = requests.get(FPLQuerier.FPL_GENERAL_URL).json()
        self.teams, self.players, self.player_stats = {}, {}, {}
        self.fixtures = requests.get(FPLQuerier.FPL_FIXTURES_URL).json()
        for team in self.data.get("teams", []):
            self.teams[team["id"]] = {
                "name": team["name"],
                "strength": FPLQuerier.get_team_difficulty(team["short_name"]),
                "code": team["short_name"],
                "fixtures": [],
                "goals_scored": 0,
                "goals_conceded": 0,
                "games": 0,
            }
        for fixture in self.fixtures:
            if fixture.get("event", None) is None:
                continue
            if fixture["started"] is not True and fixture["finished"] is not True:
                continue
            team_a = fixture.get("team_a", None)
            team_h = fixture.get("team_h", None)
            gw = fixture["event"]
            if team_a in self.teams:
                self.teams[team_a]["goals_scored"] += fixture["team_a_score"]
                self.teams[team_a]["goals_conceded"] += fixture["team_h_score"]
                self.teams[team_a]["games"] += 1
            if team_h in self.teams:
                self.teams[team_h]["goals_scored"] += fixture["team_h_score"]
                self.teams[team_h]["goals_conceded"] += fixture["team_a_score"]
                self.teams[team_h]["games"] += 1
        self.fixtures = list(filter(lambda x: not x["started"], self.fixtures))
        for fixture in self.fixtures:
            team_a = fixture.get("team_a", None)
            team_a_str = self.teams[team_a]["strength"]
            team_h = fixture.get("team_h", None)
            team_h_str = self.teams[team_h]["strength"]
            gw = fixture["event"]
            if team_a in self.teams:
                self.teams[team_a]["fixtures"].append(
                    {
                        "team": team_h,
                        "code": self.teams[team_h]["code"],
                        "difficulty": team_h_str,
                        "gw": gw,
                    }
                )
            if team_h in self.teams:
                self.teams[team_h]["fixtures"].append(
                    {
                        "team": team_a,
                        "code": self.teams[team_a]["code"],
                        "difficulty": team_a_str,
                        "gw": gw,
                    }
                )
        print(f"Loaded {len(self.data.get('elements', []))} players")
        for player in self.data.get("elements", []):
            id = player["id"]
            team = self.teams.get(player["team"], {})
            player_name = f"{player['web_name']} ({team['code']})"
            player["gi_per_goal_scored"] = (
                float(player["goals_scored"] + player["assists"]) / team["goals_scored"]
            )
            self.players[player_name] = {
                "id": id,
                "team": team,
                "position": "GK"
                if player["element_type"] == 1
                else (
                    "DEF"
                    if player["element_type"] == 2
                    else ("MID" if player["element_type"] == 3 else "FWD")
                ),
                "stats": player,
            }
            count = fixture_score = 0
            for fixture in team["fixtures"]:
                fixture_score += fixture["difficulty"]
                if (count := count + 1) >= 10:
                    break
            self.players[player_name]["stats"]["fixture_score"] = round(
                fixture_score / float(count), 2
            )
            team_games = float(team["games"])
            self.players[player_name]["stats"]["minutes_per_game"] = (
                player["minutes"] / team_games if team_games > 0 else 0
            )
            self.players[player_name]["stats"]["bonus_per_game"] = (
                player["bonus"] / team_games if team_games > 0 else 0
            )
            self.players[player_name]["stats"]["starts_per_game"] = (
                player["starts"] / team_games if team_games > 0 else 0
            )
            self.players[player_name]["stats"]["form_per_cost"] = (
                10 * float(player["points_per_game"]) / player["now_cost"]
            )

    def __init__(self):
        """
        Constructor for FPLQuerier class
        """
        self.refresh()

    def query_player_kpi(self, player: str):
        """
        Query KPI data for a player
        """
        player_id = self.players[player]["id"]
        data = requests.get(FPLQuerier.FPL_ELEMENT_SUMMARY_URL.format(player_id)).json()
        history = []
        matches = 0
        minutes = 0
        for gw in data["history"]:
            round, pts, bpts, cost = (
                gw["round"],
                gw["total_points"],
                gw["bonus"],
                gw["value"],
            )
            xg, xa, xgi, xgc = (
                float(gw["expected_goals"]),
                float(gw["expected_assists"]),
                float(gw["expected_goal_involvements"]),
                float(gw["expected_goals_conceded"]),
            )
            goals, assists = gw["goals_scored"], gw["assists"]
            gi = goals + assists
            # TODO: Get opponent
            opponent = self.teams.get(gw["opponent_team"], {}).get("name", "Unknown")
            minutes += gw["minutes"]
            matches += 1
            # form = gw['form']
            history.append(
                {
                    "round": round,
                    "points": pts,
                    "cost": cost,
                    "bonus": bpts,
                    "gi": gi,
                    "xgi": xgi,
                    "opponent": opponent,
                    "form": pts / round,
                }
            )
        self.players[player]["history"] = history
        self.players[player]["stats"]["minutes_per_game"] = float(minutes) / matches
        return history

    def query_player_by_name(self, name=None, max_results=10):
        """
        Query player by name
        :param name: name of player
        :return: player data
        """
        name = name.lower()
        results = []
        if name is None and id is None:
            return None
        count = 0
        for player in self.data["elements"]:
            if name is not None and name in player["web_name"].lower():
                results.append((player["web_name"], player["id"]))
                count += 1
            if count >= max_results:
                break
        return results
