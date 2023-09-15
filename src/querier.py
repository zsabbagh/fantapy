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
        self.teams, self.players, self.player_stats = {}, {}, {}
        self.fixtures = requests.get(FPLQuerier.FPL_FIXTURES_URL).json()
        self.fixtures = list(filter(lambda x: not x['started'], self.fixtures))
        for team in self.data.get('teams', []):
            self.teams[team['id']] = {
                'name': team['name'],
                'strength': team['strength'],
                'code': team['short_name'],
                'fixtures': [],
            }
        for fixture in self.fixtures:
            team_a = fixture.get('team_a', None)
            team_a_diff = fixture.get('team_a_difficulty', None)
            team_h = fixture.get('team_h', None)
            team_h_diff = fixture.get('team_h_difficulty', None)
            gw = fixture['event']
            if team_a in self.teams:
                self.teams[team_a]['fixtures'].append({
                    'team': team_h,
                    'code': self.teams[team_h]['code'],
                    'difficulty': team_a_diff,
                    'gw': gw,
                })
            if team_h in self.teams:
                self.teams[team_h]['fixtures'].append({
                    'team': team_a,
                    'code': self.teams[team_a]['code'],
                    'difficulty': team_h_diff,
                    'gw': gw,
                })
        for player in self.data.get('elements', []):
            id = player['id']
            team = self.teams.get(player['team'], {})
            self.players[player['web_name']] = {
                'id': id,
                'team': team,
                'stats': {
                    'goals': int(player['goals_scored']),
                    'assists': int(player['assists']),
                    'xg': float(player['expected_goals']),
                    'xa': float(player['expected_assists']),
                    'xgi': float(player['expected_goal_involvements']),
                    'xgc': float(player['expected_goals_conceded']),
                },
            }
    
    def query_player_kpi(self, player: str):
        """
        Query KPI data for a player
        """
        player_id = self.players[player]['id']
        data = requests.get(FPLQuerier.FPL_ELEMENT_SUMMARY_URL.format(player_id)).json()
        history = []
        for gw in data['history']:
            round, pts, bpts, cost = gw['round'], gw['total_points'], gw['bonus'], gw['value']
            xg, xa, xgi, xgc = float(gw['expected_goals']), float(gw['expected_assists']), float(gw['expected_goal_involvements']), float(gw['expected_goals_conceded'])
            goals, assists = gw['goals_scored'], gw['assists']
            gi = goals + assists
            # TODO: Get opponent
            opponent = self.teams.get(gw['opponent_team'], {}).get('name', 'Unknown')
            # form = gw['form']
            history.append({
                'round': round,
                'points': pts,
                'cost': cost,
                'bonus': bpts,
                'gi': gi,
                'xgi': xgi,
                'opponent': opponent,
                'form': pts / round,
            })
        self.players[player]['history'] = history
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
        for player in self.data['elements']:
            if name is not None and name in player['web_name'].lower():
                results.append((player['web_name'], player['id']))
                count += 1
            if count >= max_results:
                break
        return results

