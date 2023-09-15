import requests
import pprint
import re

class FPLQuerier:

    FPL_GENERAL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
    FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
    FPL_ENTRY_URL = "https://fantasy.premierleague.com/api/entry/"
    FPL_ENTRY_HISTORY_URL = "https://fantasy.premierleague.com/api/entry/{}/history/"
    FPL_ELEMENT_SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{}/"

    teams = {}
    data = {}

    def __init__(self):
        """
        Constructor for FPLQuerier class
        """
        self.data = requests.get(FPLQuerier.FPL_GENERAL_URL).json()
        self.teams = {}
        self.players = {}
        for team in self.data.get('teams', []):
            self.teams[team['id']] = team
        for player in self.data.get('elements', []):
            self.players[player['web_name']] = player['id']
    
    def query_player_kpi(self, player_id: int):
        """
        Query KPI data for a player
        """
        data = requests.get(FPLQuerier.FPL_ELEMENT_SUMMARY_URL.format(player_id)).json()
        results = []
        for gw in data['history']:
            round, pts, bpts, cost = gw['round'], gw['total_points'], gw['bonus'], gw['value']
            xg, xa, xgi, xgc = gw['expected_goals'], gw['expected_assists'], gw['expected_goal_involvements'], gw['expected_goals_conceded']
            goals, assists = gw['goals_scored'], gw['assists']
            gi = goals + assists
            # TODO: Get opponent
            opponent = self.teams.get(gw['opponent_team'], {}).get('name', 'Unknown')
            # form = gw['form']
            results.append({
                'round': round,
                'points': pts,
                'gi': gi,
                'xgi': xgi,
                'opponent': opponent,
                'form': pts / round,
            })
        return results

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
        for player in self.data['elements']:
            if name is not None and name in player['web_name'].lower():
                results.append((player['web_name'], player['id']))
                count += 1
            if count >= max_results:
                break
        return results

