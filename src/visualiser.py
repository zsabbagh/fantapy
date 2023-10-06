import streamlit as st, pandas as pd
from src.querier import FPLQuerier
from src.data import FPLData
import plotly.graph_objects as go


def colour_text(string, colour="white"):
    return f"<span style='color:{colour}'>{string}</span>"


def rnd(x):
    return round(x, 2)


@st.cache_data
def get_teams(fpl: FPLData):
    return sorted(list(fpl.teams_by_name.keys()))


class FPLVisualiser:
    def top_players(fpl: FPLData):
        """
        Generate table of top players
        """
        st.header("Top Players")
        default_players = (
            [
                fpl.players.get(int(x["element"]), {}).get("name_with_team", None)
                for x in fpl.manager_team.get("team", [])
            ]
            if fpl.manager_team is not None
            and st.checkbox(
                f"Show team '{fpl.manager_team['name']}' for GW{fpl.manager_team['gw']}"
            )
            else []
        )
        results = []
        teams_by_name = fpl.teams_by_name
        selected_players = st.multiselect(
            "Select players", fpl.player_names, default_players
        )
        compare = st.checkbox("Compare with players", value=False)
        compare_players = (
            st.multiselect(
                "Select players to compare with", fpl.player_names, selected_players
            )
            if compare
            else []
        )
        if len(selected_players) < 1:
            selected_players = fpl.player_names
        all_players = selected_players + compare_players
        players = {k: v for k, v in fpl.players_by_name.items() if k in all_players}
        columns = [
            "Name",
            "Team",
            "Points",
            "Minutes/Game",
            "xPoints",
            "xPoints/Cost",
            "Selected By",
            "Differential",
            "Team Clean Sheets",
            "Fixture Score",
            "Position",
            "Price",
            "Bonus/Game",
            "Bonus %",
            "Goals",
            "xG",
            "Assists",
            "xA",
            "GI",
            "xGI",
            "Team Goals",
            "Team GI %",
            "ICT",
            "Minutes",
            "Minutes/xGI",
            "Form",
            "Form/Cost",
            "Starts/Game",
            "News",
        ]
        # TODO: Filter on easy fixtures
        total_xpoints = 0.0
        total_xpoints_comp = 0.0
        for player, info in players.items():
            selected_by = float(info["stats"]["selected_by_percent"])
            total_pts = info["stats"]["total_points"]
            differential = total_pts * (1 - (selected_by / 100.0))
            cost = round(info["stats"]["now_cost"] / 10.0, 3)
            points_per_min = (
                total_pts / info["stats"]["minutes"]
                if info["stats"]["minutes"] > 0
                else 0
            )
            minutes_per_game = round(float(info["stats"]["minutes_per_game"]), 3)
            xpoints = points_per_min * 38 * minutes_per_game
            if player in selected_players:
                total_xpoints += xpoints
            if player in compare_players:
                total_xpoints_comp += xpoints
            values = [
                info["name"],
                info["team"]["name"],
                total_pts,
                minutes_per_game,
                xpoints,
                xpoints / cost,
                selected_by,
                differential,
                info["team"]["clean_sheets"],
                float(info["team"]["fixture_score"]),
                info["position"],
                cost,
                round(float(info["stats"]["bonus_per_game"]), 2),
                int(100 * info["stats"]["bonus_chance"]),
                info["stats"]["goals_scored"],
                info["stats"]["expected_goals"],
                info["stats"]["assists"],
                info["stats"]["expected_assists"],
                info["stats"]["goals_scored"] + info["stats"]["assists"],
                info["stats"]["expected_goal_involvements"],
                info["team"]["goals_scored"],
                round(100 * info["stats"]["gi_per_goal_scored"], 1),
                round(float(info["stats"]["ict_index"]), 2),
                info["stats"]["minutes"],
                round(float(info["stats"]["minutes_per_xgi"]), 2),
                float(info["stats"]["points_per_game"]),  # form
                float(info["stats"]["form_per_cost"]),  # form
                float(info["stats"]["starts_per_game"]),
                info["stats"]["news"],
            ]
            results.append(values)
        st.write(f"Total players: {len(results)}")
        if compare:
            st.write(f"Total xPoints: {total_xpoints:.2f}")
            st.write(f"Total xPoints comp: {total_xpoints_comp:.2f}")
        df = pd.DataFrame(results, columns=columns).sort_values(
            by=["Name"], ascending=True
        )
        col1, col2 = st.columns(2)
        selected_pos = col1.multiselect(
            "Select positions", ["GK", "DEF", "MID", "FWD"], []
        )
        selected_pos = (
            selected_pos if len(selected_pos) > 0 else ["GK", "DEF", "MID", "FWD"]
        )
        selected_teams = col2.multiselect("Select teams", teams_by_name, [])
        selected_teams = selected_teams if len(selected_teams) > 0 else teams_by_name
        col1, col2 = st.columns(2)
        selected_fscore = col1.slider(
            "Select fixture score",
            0.0,
            5.0,
            step=0.1,
            value=(0.0, 5.0),
            help="Difficulty of fixture",
        )
        selected_min_per_xgi = col2.slider(
            "Select minutes per xGI",
            0,
            1000,
            step=10,
            value=(0, 1000),
            help="Minutes per expected goal involvement",
        )
        selected_min_per_xgi = (
            (selected_min_per_xgi[0], 10000000)
            if selected_min_per_xgi[1] == 1000
            else selected_min_per_xgi
        )
        col1, col2 = st.columns(2)
        selected_price = col1.slider(
            "Select price range", 3.5, 14.5, (3.5, 14.5), step=0.1
        )
        selected_team_gi = col2.slider(
            "Minimum team GI %",
            0,
            100,
            step=5,
            help="Measures how much of the team's goals a player is involved in",
        )
        col1, col2 = st.columns(2)
        selected_minutes = col1.slider("Minimum min/game", 0, 90, step=5, value=0)
        selected_bonus = col2.slider("Minimum bonus chance", 0, 100, step=5)
        # st.write(f"Players matching criteria: {len(df)}")
        # df = df[df["Position"].isin(selected_pos)]
        # st.write(f"Players matching POSITION criteria: {len(df)}")
        # df = df[df["Price"].between(selected_price[0], selected_price[1])]
        # st.write(f"Players matching PRICE criteria: {len(df)}")
        # df = df[df["Team GI %"].between(selected_team_gi, 100)]
        # st.write(f"Players matching TEAM GI criteria: {len(df)}")
        # df = df[df["Minutes/Game"].between(selected_minutes, 90)]
        # st.write(f"Players matching MINUTES criteria: {len(df)}")
        # df = df[df["Bonus/Game"].between(selected_bonus, 3.0)]
        df = df[
            df["Position"].isin(selected_pos)
            & df["Price"].between(selected_price[0], selected_price[1])
            & df["Team GI %"].between(selected_team_gi, 100)
            & df["Fixture Score"].between(selected_fscore[0], selected_fscore[1])
            & df["Minutes/Game"].between(selected_minutes, 90)
            & df["Bonus %"].between(selected_bonus, 100)
            & df["Team"].isin(selected_teams)
            & df["Minutes/xGI"].between(
                selected_min_per_xgi[0], selected_min_per_xgi[1]
            )
        ]
        unavailable = ["Name"]
        available = sorted(list(set(df.columns) - set(unavailable)))
        selected_columns = st.multiselect("Select columns", available, default=[])
        selected_columns = selected_columns if len(selected_columns) > 0 else available
        filtered_df = df.drop(
            columns=list(set(df.columns) - set(selected_columns + unavailable))
        )
        st.dataframe(filtered_df, width=1500, height=500)

    def fixture_for_player(fpl: FPLData, player=None):
        players = fpl.players_by_name
        col1, col2 = st.columns(2)
        col1.write(f"Upcoming Fixtures for {player}")
        col2.write(
            f"Fixture Difficulty: {players[player]['team']['fixture_score']} / 10.0"
        )
        team = players[player]["team"]
        fixtures = team["fixtures"]
        upcoming_gws = sorted(
            [x for x in fixtures.keys() if fixtures[x].get("done", None) == False]
        )
        cola, colb, colc, cold, cole = st.columns(5)
        team_strength = players[player]["team"]["strength"]
        if len(upcoming_gws) > 0:
            cola.metric(
                label=f"GW{upcoming_gws[0]}, {'Home' if fixtures[upcoming_gws[0]]['where'] == 'H' else 'Away'}",
                value=fixtures[upcoming_gws[0]]["code"],
                delta=fixtures[upcoming_gws[0]]["difficulty"] - team_strength,
                delta_color="inverse",
            )
        if len(upcoming_gws) > 1:
            colb.metric(
                label=f"GW{upcoming_gws[1]}, {'Home' if fixtures[upcoming_gws[1]]['where'] == 'H' else 'Away'}",
                value=fixtures[upcoming_gws[1]]["code"],
                delta=fixtures[upcoming_gws[1]]["difficulty"] - team_strength,
                delta_color="inverse",
            )
        if len(upcoming_gws) > 2:
            colc.metric(
                label=f"GW{upcoming_gws[2]}, {'Home' if fixtures[upcoming_gws[2]]['where'] == 'H' else 'Away'}",
                value=fixtures[upcoming_gws[2]]["code"],
                delta=fixtures[upcoming_gws[2]]["difficulty"] - team_strength,
                delta_color="inverse",
            )
        if len(upcoming_gws) > 3:
            cold.metric(
                label=f"GW{upcoming_gws[3]}, {'Home' if fixtures[upcoming_gws[3]]['where'] == 'H' else 'Away'}",
                value=fixtures[upcoming_gws[3]]["code"],
                delta=fixtures[upcoming_gws[3]]["difficulty"] - team_strength,
                delta_color="inverse",
            )
        if len(upcoming_gws) > 4:
            cole.metric(
                label=f"GW{upcoming_gws[4]}, {'Home' if fixtures[upcoming_gws[4]]['where'] == 'H' else 'Away'}",
                value=fixtures[upcoming_gws[4]]["code"],
                delta=fixtures[upcoming_gws[4]]["difficulty"] - team_strength,
                delta_color="inverse",
            )

    def player_metrics(fpl: FPLData, player=None, player_comp=None):
        """
        Generate player metrics
        """
        players = fpl.players_by_name
        stats = players[player]["stats"]
        goals = int(stats["goals_scored"])
        assists = int(stats["assists"])
        gi = goals + assists
        xg = float(stats["expected_goals"])
        xa = float(stats["expected_assists"])
        xgi = xg + xa
        points = stats["total_points"]
        form_value = stats["form_per_cost"]
        minutes_per_game = stats["minutes_per_game"]
        bonus_per_game = stats["bonus_per_game"]
        bonus_chance = stats["bonus_chance"]
        price = stats["now_cost"] / 10
        fixture_score = players[player]["team"]["fixture_score"]
        team_goals = players[player]["team"]["goals_scored"]
        team_gi = round(float(gi) / team_goals, 2) if team_goals > 0 else 0
        if player_comp in players:
            comp_stats = players[player_comp]["stats"]
            comp_price = comp_stats["now_cost"] / 10
            comp_goals = float(comp_stats["goals_scored"])
            comp_assists = float(comp_stats["assists"])
            comp_gi = comp_goals + comp_assists
            comp_xg = float(comp_stats["expected_goals"])
            comp_xa = float(comp_stats["expected_assists"])
            comp_xgi = float(comp_stats["expected_goal_involvements"])
            comp_points = float(comp_stats["total_points"])
            comp_form_value = float(comp_stats["form_per_cost"])
            comp_minutes_per_game = float(comp_stats["minutes_per_game"])
            comp_bonus_per_game = float(comp_stats["bonus_per_game"])
            comp_bonus_chance = float(comp_stats["bonus_chance"])
            comp_team_goals = players[player_comp]["team"]["goals_scored"]
            comp_team_gi = (
                round(float(comp_gi) / comp_team_goals, 2) if comp_team_goals > 0 else 0
            )
            comp_fixture_score = players[player_comp]["team"]["fixture_score"]
        comp_price_diff = (
            round(price - comp_price, 2) if player_comp is not None else None
        )
        st.markdown(
            f"Price: £{stats['now_cost'] / 10}"
            if player_comp is None
            else colour_text(
                f"Price diff: {'+' if comp_price_diff > 0 else '-'}£{str(abs(comp_price_diff))}",
                "green" if comp_price_diff < 0 else "yellow",
            ),
            unsafe_allow_html=True,
        )
        st.write(f"Metrics for {player}, {players[player]['position']}")
        if player_comp is None:
            col1, col2, col3, col4, col5 = st.columns(5)
            dgoals = f"{str(round(goals - xg, 2))} ({xg} xG)" if goals != xg else None
            dassists = (
                f"{str(round(assists - xa, 2))} ({xa} xA)" if assists != xa else None
            )
            dxgi = f"{str(round(gi - xgi, 2))} ({xgi} xGI)" if gi != xgi else None
            col1.metric(label="Goals", value=goals, delta=dgoals)
            col2.metric(label="Assists", value=assists, delta=dassists)
            col3.metric(label="GI", value=gi, delta=dxgi)
            col4.metric(
                label="Team GI",
                value=f"{(100*team_gi):.2f} %" if team_goals > 0 else 0,
                delta=team_goals,
                delta_color="off",
            )
            col5.metric("Minutes/Game", minutes_per_game, delta=None, delta_color="off")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(
                label="Bonus",
                value=f"{100.0*bonus_chance:.1f} %",
                delta=None,
                delta_color="off",
            )
        else:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(
                label="Goal Involvements", value=gi, delta=f"{gi - comp_gi:.1f}"
            )
            col2.metric(label="xGI", value=xgi, delta=f"{xgi - comp_xgi:.1f}")
            col3.metric(
                label="Team GI",
                value=f"{100*team_gi:.1f} %",
                delta=f"{100 * (team_gi - comp_team_gi):.1f} %",
            )
            col4.metric(
                label="Minutes/Game",
                value=minutes_per_game,
                delta=f"{minutes_per_game - comp_minutes_per_game:.1f}",
            )
            col5.metric(
                label="Form/Cost",
                value=f"{form_value:.1f}",
                delta=f"{form_value - comp_form_value:.1f}",
            )
            # stack 2
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(
                "Bonus/Game",
                value=bonus_per_game,
                delta=f"{bonus_per_game - comp_bonus_per_game:.1f}",
            )
            col2.metric(
                "Bonus %",
                f"{100.0*bonus_chance:.1f} %",
                delta=f"{100.0*(bonus_chance - comp_bonus_chance):.1f} %",
            )
            col3.metric(
                "Fixture Score",
                fixture_score,
                delta=f"{fixture_score - comp_fixture_score:.1f}",
                delta_color="inverse",
            )
        if player is not None:
            FPLVisualiser.fixture_for_player(fpl, player)
        if player_comp is not None:
            FPLVisualiser.fixture_for_player(fpl, player_comp)

    def player_charts(fpl: FPLData, player=None, player_comp=None):
        """
        Generate player KPI
        """
        # Generate figure
        history = fpl.players_by_name[player]["history"]
        comp_history = fpl.players_by_name.get(player_comp, {}).get("history", {})
        columns = ["GW", "GI", "xGI"]
        results = []
        gws, gis, xgis, pts, bpts = [], [], [], [], []
        comp_gis, comp_xgis, comp_pts, comp_bpts = [], [], [], []
        team = fpl.players_by_name[player]["team"]
        team_fixtures = team.get("fixtures", {})
        comp_team = fpl.players_by_name.get(player_comp, {}).get("team", {})
        comp_fixtures = comp_team.get("fixtures", {})
        for gw, info in history.items():
            if gw not in team_fixtures:
                continue
            gws.append(
                f"GW{gw}, {team['fixtures'][gw]['code']}"
                + (
                    f"/{comp_team['fixtures'][gw]['code']}"
                    if gw in comp_fixtures
                    else ""
                )
            )
            gis.append(info["goals_scored"] + info["assists"])
            xgis.append(info["expected_goal_involvements"])
            pts.append(info["total_points"])
            bpts.append(info["bonus"])
            if player_comp is not None:
                comp_info = comp_history.get(gw, {})
                comp_gis.append(
                    comp_info.get("goals_scored", 0) + comp_info.get("assists", 0)
                )
                comp_xgis.append(comp_info.get("expected_goal_involvements", 0))
                comp_pts.append(comp_info.get("total_points", 0))
                comp_bpts.append(comp_info.get("bonus", 0))
        # form = list(map(lambda x: x['form'], kpi))
        fig_gis = go.Figure()
        fig_bonus = go.Figure()
        fig_gis.add_trace(go.Scatter(x=gws, y=gis, mode="lines", name="GI"))
        fig_gis.add_trace(go.Scatter(x=gws, y=xgis, mode="lines", name="xGI"))
        fig_bonus.add_trace(go.Scatter(x=gws, y=pts, mode="lines", name="Points"))
        fig_bonus.add_trace(go.Scatter(x=gws, y=bpts, mode="lines", name="Bonus"))
        if player_comp is not None:
            fig_gis.add_trace(
                go.Scatter(x=gws, y=comp_gis, mode="lines", name=f"GI comp")
            )
            fig_gis.add_trace(
                go.Scatter(x=gws, y=comp_xgis, mode="lines", name="xGI comp")
            )
            fig_bonus.add_trace(
                go.Scatter(x=gws, y=comp_pts, mode="lines", name="Points comp")
            )
            fig_bonus.add_trace(
                go.Scatter(x=gws, y=comp_bpts, mode="lines", name="Bonus comp")
            )
        # fig.add_trace(go.Scatter(x=x, y=form, mode='lines', name='Goals+Assists'))
        fig_gis.update_layout(
            xaxis_title="GW",
            yaxis_title="",
            title="Goal Involvements / xGI",
            hovermode="closest",
        )
        fig_bonus.update_layout(
            xaxis_title="GW",
            yaxis_title="",
            title="Points / Bonus",
            hovermode="closest",
        )
        fig_gis.update_xaxes(tick0=1, dtick=1)
        fig_bonus.update_xaxes(tick0=1, dtick=1)
        fig_gis.update_yaxes(
            tick0=0,
            dtick=1,
            range=[0, round(max(gis + xgis + comp_gis + comp_xgis)) + 1],
        )
        fig_bonus.update_yaxes(
            tick0=0,
            dtick=5,
            range=[0, round(max(pts + bpts + comp_pts + comp_bpts)) + 1],
        )
        st.plotly_chart(fig_gis)
        st.plotly_chart(fig_bonus)
        # Generate figure for form/price

    def team_metrics(fpl: FPLData):
        """
        Generate table of teams
        """
        st.header("Teams")
        team = st.selectbox(
            "Select a team", sorted(list(fpl.teams_by_name.keys())), index=0
        )
        st.write(f"Matchups for {team}")
        columns = [
            "Name",
            "Strength Home",
            "Strength Away",
            "Fixture Score",
            "Matchup Score",
            "Goals Scored",
            "Goals Conceded",
            "Diff. 1",
            "Diff. 2",
            "Diff. 3",
            "Diff. 4",
            "Diff. 5",
        ]
        results = []
        teams_by_name = fpl.teams_by_name
        for other, matchup in fpl.teams_by_name[team].get("matchups", {}).items():
            results.append(
                [
                    other,
                    teams_by_name[other]["strength_home"],
                    teams_by_name[other]["strength_away"],
                    fpl.teams_by_name[other]["fixture_score"],
                    matchup["score"],
                    teams_by_name[other]["goals_scored"],
                    teams_by_name[other]["goals_conceded"],
                    matchup["overlapping"][1],
                    matchup["overlapping"][2],
                    matchup["overlapping"][3],
                    matchup["overlapping"][4],
                    matchup["overlapping"][5],
                ]
            )
        df = pd.DataFrame(results, columns=columns).sort_values(
            by=["Matchup Score"], ascending=False
        )
        st.dataframe(df, width=1500, height=500)

    def player_section(fpl: FPLData):
        """
        Generate player section
        """
        st.header("Player KPI")
        cola, colb = st.columns(2)
        player = cola.selectbox("Select a player", fpl.player_names, index=297)
        compare = cola.checkbox("Compare with player", value=False)
        player_comp = (
            cola.selectbox(
                f"Select player to compare {player} with",
                fpl.player_names,
                index=212,
            )
            if compare
            else None
        )
        with cola:
            FPLVisualiser.player_metrics(fpl, player=player, player_comp=player_comp)
        with colb:
            FPLVisualiser.player_charts(fpl, player=player, player_comp=player_comp)
