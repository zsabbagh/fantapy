import streamlit as st, pandas as pd
import plotly.graph_objects as go
from pprint import pprint
from src.querier import FPLQuerier


# Apply custom CSS to control the width
class GlobalState:
    def __init__(self):
        self.players = []
        self.player = "Haaland (MCI)"


state = GlobalState()


def rnd(x):
    return round(x, 2)


def colour_text(string, colour="white"):
    return f"<span style='color:{colour}'>{string}</span>"


def generate_top_players(fpl: FPLQuerier):
    """
    Generate table of top players
    """
    st.header("Top Players")
    results = []
    columns = [
        "Name",
        "Team",
        "Position",
        "Price",
        "Points",
        "Bonus/Game",
        "Goals",
        "xG",
        "Assists",
        "xA",
        "GI",
        "xGI",
        "Team Goals",
        "Team GI %",
        "Fixture Score",
        "ICT",
        "Minutes",
        "Minutes/Game",
        "Form",
        "Form/Cost",
        "Starts/Game",
    ]
    # TODO: Filter on easy fixtures
    for player, info in fpl.players.items():
        team_games = info["team"]["games"]
        values = [
            player.split(" (")[0],
            info["team"]["name"],
            info["position"],
            round(info["stats"]["now_cost"] / 10.0, 2),
            info["stats"]["total_points"],
            round(float(info["stats"]["bonus_per_game"]), 2),
            info["stats"]["goals_scored"],
            info["stats"]["expected_goals"],
            info["stats"]["assists"],
            info["stats"]["expected_assists"],
            info["stats"]["goals_scored"] + info["stats"]["assists"],
            info["stats"]["expected_goal_involvements"],
            info["team"]["goals_scored"],
            round(100 * info["stats"]["gi_per_goal_scored"], 1),
            info["team"]["fixture_score"],
            round(float(info["stats"]["ict_index"]), 2),
            info["stats"]["minutes"],
            float(info["stats"]["minutes_per_game"]),
            float(info["stats"]["points_per_game"]),  # form
            float(info["stats"]["form_per_cost"]),  # form
            float(info["stats"]["starts_per_game"]),
        ]
        results.append(values)
    st.write(f"Total players: {len(results)}")
    df = pd.DataFrame(results, columns=columns).sort_values(by=["Name"], ascending=True)
    selected_pos = st.multiselect(
        "Select positions", ["GK", "DEF", "MID", "FWD"], ["GK", "DEF", "MID", "FWD"]
    )
    col1, col2 = st.columns(2)
    selected_price = col1.slider("Select price range", 3.5, 14.5, (3.5, 14.5), step=0.5)
    selected_team_gi = col2.slider(
        "Minimum team GI %",
        0,
        100,
        step=5,
        help="Measures how much of the team's goals a player is involved in",
    )
    col1, col2 = st.columns(2)
    selected_minutes = col1.slider("Minimum min/game", 0, 90, step=5, value=80)
    selected_bonus = col2.slider("Minimum bonus/game", 0.0, 3.0, step=0.1)
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
        & df["Minutes/Game"].between(selected_minutes, 90)
        & df["Bonus/Game"].between(selected_bonus, 3.0)
    ]
    unavailable = ["Name"]
    available = sorted(list(set(df.columns) - set(unavailable)))
    selected_columns = st.multiselect("Select columns", available, default=available)
    filtered_df = df.drop(
        columns=list(set(df.columns) - set(selected_columns + unavailable))
    )
    st.dataframe(filtered_df, width=1500, height=500)


def generate_fixture_for_player(fpl: FPLQuerier, player=None):
    col1, col2 = st.columns(2)
    col1.write(f"Upcoming Fixtures for {player}")
    col2.write(
        f"Fixture Difficulty: {fpl.players[player]['team']['fixture_score']} / 10.0"
    )
    team = fpl.players[player]["team"]
    fixtures = team["fixtures"]
    upcoming_gws = sorted(list(fixtures.keys()))
    cola, colb, colc, cold, cole = st.columns(5)
    team_strength = fpl.players[player]["team"]["strength"]
    cola.metric(
        label=f"GW{upcoming_gws[0]}, {'Home' if fixtures[upcoming_gws[0]]['where'] == 'H' else 'Away'}",
        value=fixtures[upcoming_gws[0]]["code"],
        delta=fixtures[upcoming_gws[0]]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    colb.metric(
        label=f"GW{upcoming_gws[1]}, {'Home' if fixtures[upcoming_gws[1]]['where'] == 'H' else 'Away'}",
        value=fixtures[upcoming_gws[1]]["code"],
        delta=fixtures[upcoming_gws[1]]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    colc.metric(
        label=f"GW{upcoming_gws[2]}, {'Home' if fixtures[upcoming_gws[2]]['where'] == 'H' else 'Away'}",
        value=fixtures[upcoming_gws[2]]["code"],
        delta=fixtures[upcoming_gws[2]]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    cold.metric(
        label=f"GW{upcoming_gws[3]}, {'Home' if fixtures[upcoming_gws[3]]['where'] == 'H' else 'Away'}",
        value=fixtures[upcoming_gws[3]]["code"],
        delta=fixtures[upcoming_gws[3]]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    cole.metric(
        label=f"GW{upcoming_gws[4]}, {'Home' if fixtures[upcoming_gws[4]]['where'] == 'H' else 'Away'}",
        value=fixtures[upcoming_gws[4]]["code"],
        delta=fixtures[upcoming_gws[4]]["difficulty"] - team_strength,
        delta_color="inverse",
    )


def generate_player_metrics(fpl: FPLQuerier, player=None, player_comp=None):
    """
    Generate player metrics
    """
    if player is not None:
        fpl.query_player_kpi(player)
    if player_comp is not None:
        fpl.query_player_kpi(player_comp)
    stats = fpl.players[player]["stats"]
    (
        goals,
        assists,
        xg,
        xa,
        xgi,
        points,
        form_value,
        minutes_per_game,
        bonus_received,
    ) = (
        float(stats["goals_scored"]),
        float(stats["assists"]),
        float(stats["expected_goals"]),
        float(stats["expected_assists"]),
        float(stats["expected_goal_involvements"]),
        float(stats["total_points"]),
        float(stats["form_per_cost"]),
        float(stats["minutes_per_game"]),
        float(stats["bonus_received"]),
    )
    gi = goals + assists
    team_goals = fpl.players[player]["team"]["goals_scored"]
    team_gi = round(float(gi) / team_goals, 2) if team_goals > 0 else 0
    if player_comp in fpl.players:
        (
            comp_goals,
            comp_assists,
            comp_xg,
            comp_xa,
            comp_xgi,
            comp_points,
            comp_form_value,
            comp_minutes_per_game,
            comp_bonus_received,
        ) = (
            float(fpl.players[player_comp]["stats"]["goals_scored"]),
            float(fpl.players[player_comp]["stats"]["assists"]),
            float(fpl.players[player_comp]["stats"]["expected_goals"]),
            float(fpl.players[player_comp]["stats"]["expected_assists"]),
            float(fpl.players[player_comp]["stats"]["expected_goal_involvements"]),
            float(fpl.players[player_comp]["stats"]["total_points"]),
            float(fpl.players[player_comp]["stats"]["form_per_cost"]),
            float(fpl.players[player_comp]["stats"]["minutes_per_game"]),
            float(fpl.players[player_comp]["stats"]["bonus_received"]),
        )
        comp_gi = comp_goals + comp_assists
        comp_price = fpl.players[player_comp]["stats"]["now_cost"] / 10
        comp_team_goals = fpl.players[player_comp]["team"]["goals_scored"]
        comp_team_gi = (
            round(float(comp_gi) / comp_team_goals, 2) if comp_team_goals > 0 else 0
        )
    fixtures = fpl.players[player]["team"]["fixtures"]
    price = fpl.players[player]["stats"]["now_cost"] / 10
    comp_price_diff = round(price - comp_price, 2) if player_comp is not None else None
    st.markdown(
        f"Price: £{stats['now_cost'] / 10}"
        if player_comp is None
        else colour_text(
            f"Price diff: {'+' if comp_price_diff > 0 else '-'}£{str(abs(comp_price_diff))}",
            "green" if comp_price_diff < 0 else "yellow",
        ),
        unsafe_allow_html=True,
    )
    st.write(f"Metrics for {player}, {fpl.players[player]['position']}")
    if player_comp is None:
        col1, col2, col3, col4, col5 = st.columns(5)
        dgoals = f"{str(round(goals - xg, 2))} ({xg} xG)" if goals != xg else None
        dassists = f"{str(round(assists - xa, 2))} ({xa} xA)" if assists != xa else None
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
            value=f"{100.0*bonus_received:.1f} %",
            delta=None,
            delta_color="off",
        )
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Goal Involvements", value=gi, delta=f"{gi - comp_gi:.1f}")
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
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Bonus",
            f"{100.0*bonus_received:.1f} %",
            delta=f"{100.0*(bonus_received - comp_bonus_received):.1f} %",
        )
    if player is not None:
        generate_fixture_for_player(fpl, player)
    if player_comp is not None:
        generate_fixture_for_player(fpl, player_comp)


def generate_player_charts(fpl: FPLQuerier, player=None, player_comp=None):
    """
    Generate player KPI
    """
    kpi = fpl.query_player_kpi(player)
    # Generate figure
    fig = go.Figure()
    x = list(map(lambda x: f"GW{x['round']} ({x['opponent']})", kpi))
    gi = list(map(lambda x: x["gi"], kpi))
    xgi = list(map(lambda x: x["xgi"], kpi))
    # form = list(map(lambda x: x['form'], kpi))
    fig.add_trace(go.Scatter(x=x, y=gi, mode="lines+markers", name="GI"))
    fig.add_trace(go.Scatter(x=x, y=xgi, mode="lines+markers", name="xGI"))
    # fig.add_trace(go.Scatter(x=x, y=form, mode='lines', name='Goals+Assists'))
    fig.update_layout(
        xaxis_title="GW",
        yaxis_title="",
        title="Goal Involvements / xGI",
        hovermode="closest",
    )
    fig.update_xaxes(tick0=1, dtick=1)
    fig.update_yaxes(tick0=0, dtick=1, range=[0, round(max(gi + xgi)) + 1])
    st.plotly_chart(fig)
    # Generate figure for form/price


def generate_team_metrics(fpl: FPLQuerier):
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
        "Fixture Score",
        "Score",
        "Diff. 1",
        "Diff. 2",
        "Diff. 3",
        "Diff. 4",
        "Diff. 5",
    ]
    results = []
    for other, matchup in fpl.teams_by_name[team].get("matchups", {}).items():
        results.append(
            [
                other,
                fpl.teams_by_name[other]["fixture_score"],
                matchup["score"],
                matchup["overlapping"][1],
                matchup["overlapping"][2],
                matchup["overlapping"][3],
                matchup["overlapping"][4],
                matchup["overlapping"][5],
            ]
        )
    df = pd.DataFrame(results, columns=columns).sort_values(
        by=["Score"], ascending=False
    )
    st.dataframe(df, width=1500, height=500)


def main():
    # Initialize querier
    st.title("FantaPy Premier League \U0001F3C6")
    fpl = FPLQuerier()
    clicked = st.button("Refresh")
    if clicked:
        fpl.refresh()
    generate_top_players(fpl)
    # Player KPI
    st.header("Player KPI")
    debug = st.checkbox("Debug", value=False)
    players_sorted = sorted(fpl.players.keys(), key=lambda x: x[0])
    player = st.selectbox("Select a player", players_sorted, index=0)
    if debug:
        st.write(f"Player: {player}")
        st.write(fpl.players[player])
    col1, col2 = st.columns(2)
    compare = col2.checkbox("Compare with player", value=False)
    player_comp = (
        col1.selectbox(
            f"Select player to compare {player} with", list(fpl.players.keys())
        )
        if compare
        else None
    )
    generate_player_metrics(fpl, player=player, player_comp=player_comp)
    generate_player_charts(fpl, player=player, player_comp=player_comp)
    generate_team_metrics(fpl)


if __name__ == "__main__":
    main()
