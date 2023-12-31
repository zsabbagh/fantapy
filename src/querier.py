import requests, streamlit as st
from src.data import FPLData
from pprint import pprint


class FPLQuerier:
    FPL_GENERAL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
    FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
    FPL_ENTRY_URL = "https://fantasy.premierleague.com/api/entry/"
    FPL_ENTRY_HISTORY_URL = "https://fantasy.premierleague.com/api/entry/{}/history/"
    FPL_MANAGER_TEAM_URL = (
        "https://fantasy.premierleague.com/api/entry/{}/event/{}/picks/"
    )
    FPL_ELEMENT_SUMMARY_URL = (
        "https://fantasy.premierleague.com/api/element-summary/{}/"
    )
    FPL_GW_LIVE_URL = "https://fantasy.premierleague.com/api/event/{}/live/"

    teams = {}
    teams_by_name = {}
    data = {}

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_manager_data(manager_id: int, gw: int):
        """
        Get manager data from previous seasons
        """
        manager = requests.get(FPLQuerier.FPL_ENTRY_URL + str(manager_id)).json()
        data = requests.get(
            FPLQuerier.FPL_MANAGER_TEAM_URL.format(manager_id, gw)
        ).json()
        return {
            "name": manager["name"],
            "gw": gw,
            "team": data.get("picks", {}),
        }

    @staticmethod
    def get_team_difficulty(team_code: str):
        team_code = team_code.upper()
        if team_code in ("LUT", "BOU"):
            return 1
        elif team_code in ("ARS", "LIV", "MCI"):
            return 5
        elif team_code in ("NEW", "BHA", "BRE", "AVL", "CHE", "TOT"):
            return 4
        elif team_code in ("BUR", "SHE", "WOL", "EVE"):
            return 2
        else:
            return 3

    @staticmethod
    def get_players(data, teams):
        """
        TODO: Run the querier and cache the results
              - Should run EACH gameweek and parse all the data
        returns: curr_gw, players
        """
        curr_gw, players, players_by_name = 0, {}, {}
        for player in data.get("elements", []):
            id = player["id"]
            team = teams.get(player["team"], {})
            player_name = player["web_name"]
            player["gi_per_goal_scored"] = (
                float(player["goals_scored"] + player["assists"]) / team["goals_scored"]
            )
            name = f"{player_name} ({team['code']})"
            for k, v in player.items():
                if type(v) == str and v != "":
                    try:
                        player[k] = round(float(v), 3)
                    except ValueError:
                        pass
            players[id] = {
                "id": id,
                "name": player_name,
                "name_with_team": name,
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
            players_by_name[name] = players[id]
        for gw in range(1, 39):
            data = requests.get(FPLQuerier.FPL_GW_LIVE_URL.format(gw)).json()
            if data is None or len(data.get("elements", [])) == 0:
                curr_gw = gw
                break
            for player in data["elements"]:
                pid = player["id"]
                for k, v in player["stats"].items():
                    if type(v) == str:
                        try:
                            player["stats"][k] = round(float(v), 3)
                        except ValueError:
                            player["stats"][k] = 0
                if pid not in players:
                    raise Exception(f"Player {pid} not found")
                if "history" not in players[pid]:
                    players[pid]["history"] = {}
                pdict = players[pid]
                stats = pdict["stats"]
                pdict["history"][gw] = player["stats"]
                stats["games_played"] = stats.get("games_played", 0) + 1
                stats["games_w_bonus"] = stats.get("games_w_bonus", 0) + (
                    1 if player["stats"]["bonus"] > 0 else 0
                )
                stats["games_started"] = stats.get("games_started", 0) + (
                    1 if player["stats"]["starts"] > 0 else 0
                )
        for player in players.values():
            stats = player["stats"]
            games_played = stats["games_played"]
            stats["minutes_per_game"] = (
                stats["minutes"] / games_played if games_played > 0 else 0
            )
            stats["bonus_per_game"] = (
                stats["bonus"] / games_played if games_played > 0 else 0
            )
            stats["bonus_chance"] = (
                stats["games_w_bonus"] / games_played if games_played > 0 else 0
            )
            stats["starts_per_game"] = (
                stats["starts"] / games_played if games_played > 0 else 0
            )
            stats["form_per_cost"] = (
                10 * float(stats["points_per_game"]) / stats["now_cost"]
            )
            stats["minutes_per_xgi"] = (
                stats["minutes"] / stats["expected_goal_involvements"]
                if stats["expected_goal_involvements"] > 0
                else 0
            )
        return curr_gw, players, players_by_name

    @staticmethod
    def get_teams(data):
        teams, teams_by_name = {}, {}
        for team in data.get("teams", []):
            teams[team["id"]] = {
                "id": team["id"],
                "info": team,
                "name": team["name"],
                "strength": FPLQuerier.get_team_difficulty(team["short_name"]),
                "code": team["short_name"],
                "fixtures": {},
                "goals_scored": 0,
                "goals_conceded": 0,
                "games": 0,
                "clean_sheets": 0,
                "matchups": {},
                "strength_home": team["strength_overall_home"] - 1000,
                "strength_away": team["strength_overall_away"] - 1000,
                "strength_attack_home": team["strength_attack_home"] - 1000,
                "strength_attack_away": team["strength_attack_away"] - 1000,
                "strength_defence_home": team["strength_defence_home"] - 1000,
                "strength_defence_away": team["strength_defence_away"] - 1000,
            }
            teams_by_name[team["name"]] = teams[team["id"]]
        fixtures = requests.get(FPLQuerier.FPL_FIXTURES_URL).json()
        for fixture in fixtures:
            if fixture.get("event", None) is None:
                continue
            team_a = fixture.get("team_a", None)
            team_h = fixture.get("team_h", None)
            gw = fixture["event"]
            done_fixture = fixture["finished"] is True or fixture["started"] is True
            if team_a in teams:
                if done_fixture:
                    teams[team_a]["goals_scored"] += fixture["team_a_score"]
                    teams[team_a]["goals_conceded"] += fixture["team_h_score"]
                    teams[team_a]["games"] += 1
                    teams[team_a]["clean_sheets"] += (
                        1 if fixture["team_h_score"] == 0 else 0
                    )
                teams[team_a]["fixtures"][gw] = {
                    "team": team_h,
                    "code": teams[team_h]["code"],
                    "difficulty": teams[team_h]["strength"],
                    "where": "H",
                    "done": done_fixture,
                }
            if team_h in teams:
                if done_fixture:
                    teams[team_h]["goals_scored"] += fixture["team_h_score"]
                    teams[team_h]["goals_conceded"] += fixture["team_a_score"]
                    teams[team_h]["games"] += 1
                    teams[team_h]["clean_sheets"] += (
                        1 if fixture["team_a_score"] == 0 else 0
                    )
                teams[team_h]["fixtures"][gw] = {
                    "team": team_a,
                    "code": teams[team_a]["code"],
                    "where": "A",
                    "difficulty": teams[team_a]["strength"],
                    "done": done_fixture,
                }
        # Generate fixture score
        for team in teams.values():
            count = fixture_score = 0
            factor = [5, 3, 2, 1, 1]
            upcoming = sorted(
                [i for i in team["fixtures"] if not team["fixtures"][i]["done"]][:5]
            )
            for gw in upcoming:
                fixture = team["fixtures"][gw]
                fixture_score += fixture["difficulty"] * factor.pop(0)
                if (count := count + 1) >= 5:
                    break
            team["fixture_score"] = round(
                5 * fixture_score / (25 + 15.0 + 5 + 8), 2
            )  # 38 is the max difficulty
            for other in teams.values():
                if other["id"] in team["matchups"]:
                    continue
                if other["name"] == team["name"]:
                    continue
                overlapping = [0] * 6
                for i in range(0, 38):
                    if i >= len(other["fixtures"]):
                        break
                    if i not in team["fixtures"] or i not in other["fixtures"]:
                        continue
                    tdiff = team["fixtures"][i]["difficulty"]
                    odiff = other["fixtures"][i]["difficulty"]
                    mindiff = min(tdiff, odiff)
                    overlapping[mindiff] += 1
                score = sum([i * overlapping[i] for i in range(0, len(overlapping))])
                team["matchups"][other["name"]] = {
                    "id": other["id"],
                    "score": score,
                    "overlapping": overlapping,
                }
                other["matchups"][team["name"]] = {
                    "id": team["id"],
                    "score": score,
                    "overlapping": overlapping,
                }
        return teams, teams_by_name

    @staticmethod
    @st.cache_data(ttl=3600)
    def run():
        """
        placeholder for streamlit caching
        """
        data = requests.get(FPLQuerier.FPL_GENERAL_URL).json()
        teams, teams_by_name = FPLQuerier.get_teams(data)
        curr_gw, players, players_by_name = FPLQuerier.get_players(data, teams)
        return curr_gw, data, teams, teams_by_name, players, players_by_name
