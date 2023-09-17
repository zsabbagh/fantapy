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
        "Team Goals",
        "Team GI",
        "Fixture Score",
        "ICT",
        "Minutes",
        "Form",
        "Minutes/Game",
        "Starts/Game",
    ]
    # TODO: Filter on easy fixtures
    for player, info in fpl.players.items():
        team_games = info["team"]["games"]
        results.append(
            [
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
                info["team"]["goals_scored"],
                round(info["stats"]["gi_per_goal_scored"], 2),
                info["stats"]["fixture_score"],
                round(float(info["stats"]["ict_index"]), 2),
                info["stats"]["minutes"],
                float(info["stats"]["points_per_game"]),
                float(info["stats"]["minutes_per_game"]),
                float(info["stats"]["starts_per_game"]),
            ]
        )
    df = pd.DataFrame(results, columns=columns).sort_values(by=["Name"], ascending=True)
    selected_pos = st.multiselect(
        "Select positions", ["GK", "DEF", "MID", "FWD"], ["GK", "DEF", "MID", "FWD"]
    )
    col1, col2 = st.columns(2)
    selected_price = col1.slider("Select price range", 3.5, 14.5, (3.5, 14.5), step=0.5)
    selected_team_gi = col2.slider("Minimum team GI", 0.0, 1.0, step=0.1)
    col1, col2 = st.columns(2)
    selected_minutes = col1.slider("Minimum min/game", 0, 90, step=5, value=80)
    selected_bonus = col2.slider("Minimum bonus/game", 0.0, 3.0, step=0.1)
    df = df[
        df["Position"].isin(selected_pos)
        & df["Price"].between(selected_price[0], selected_price[1])
        & df["Team GI"].between(selected_team_gi, 1.0)
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


def generate_player_metrics(fpl: FPLQuerier, player=None, player_comp=None):
    """
    Generate player metrics
    """
    stats = fpl.players[player]["stats"]
    goals, assists, xg, xa, xgi, minutes, points = (
        float(stats["goals_scored"]),
        float(stats["assists"]),
        float(stats["expected_goals"]),
        float(stats["expected_assists"]),
        float(stats["expected_goal_involvements"]),
        float(stats["minutes"]),
        float(stats["total_points"]),
    )
    gi = goals + assists
    team_goals = fpl.players[player]["team"]["goals_scored"]
    team_gi = round(float(gi) / team_goals, 2) if team_goals > 0 else 0
    min_per_point = minutes / points if points > 0 else 0
    if player_comp in fpl.players:
        (
            comp_goals,
            comp_assists,
            comp_xg,
            comp_xa,
            comp_xgi,
            comp_minutes,
            comp_points,
        ) = (
            float(fpl.players[player_comp]["stats"]["goals_scored"]),
            float(fpl.players[player_comp]["stats"]["assists"]),
            float(fpl.players[player_comp]["stats"]["expected_goals"]),
            float(fpl.players[player_comp]["stats"]["expected_assists"]),
            float(fpl.players[player_comp]["stats"]["expected_goal_involvements"]),
            float(fpl.players[player_comp]["stats"]["minutes"]),
            float(fpl.players[player_comp]["stats"]["total_points"]),
        )
        comp_gi = comp_goals + comp_assists
        comp_price = fpl.players[player_comp]["stats"]["now_cost"] / 10
        comp_team_goals = fpl.players[player_comp]["team"]["goals_scored"]
        comp_team_gi = (
            round(float(comp_gi) / comp_team_goals, 2) if comp_team_goals > 0 else 0
        )
        comp_min_per_point = minutes / points if points > 0 else 0
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
    st.write(f"Metrics for {player}")
    if player_comp is None:
        col1, col2, col3, col4 = st.columns(4)
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
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Goal Involvements", value=gi, delta=f"{gi - comp_gi:.1f}")
        col2.metric(label="xGI", value=xgi, delta=f"{xgi - comp_xgi:.1f}")
        col3.metric(
            label="Team GI",
            value=f"{100*team_gi:.1f} %",
            delta=f"{100 * (team_gi - comp_team_gi):.1f}",
        )
        col4.metric(label="Minutes", value=minutes, delta=f"{minutes - comp_minutes}")
        col5.metric(
            label="Minutes / Point",
            value=f"{min_per_point:.1f}",
            delta=f"{min_per_point - comp_min_per_point:.1f}",
        )
    # TODO: Good pick on fixtures?
    st.write(f"Upcoming Fixtures for {player}")
    cola, colb, colc, cold, cole = st.columns(5)
    team_strength = fpl.players[player]["team"]["strength"]
    cola.metric(
        label=f"GW{fixtures[0]['gw']}",
        value=fixtures[0]["code"],
        delta=fixtures[0]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    colb.metric(
        label=f"GW{fixtures[1]['gw']}",
        value=fixtures[1]["code"],
        delta=fixtures[1]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    colc.metric(
        label=f"GW{fixtures[2]['gw']}",
        value=fixtures[2]["code"],
        delta=fixtures[2]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    cold.metric(
        label=f"GW{fixtures[3]['gw']}",
        value=fixtures[3]["code"],
        delta=fixtures[3]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    cole.metric(
        label=f"GW{fixtures[4]['gw']}",
        value=fixtures[4]["code"],
        delta=fixtures[4]["difficulty"] - team_strength,
        delta_color="inverse",
    )
    st.write(
        "Fixture Difficulty",
        fpl.players[player]["stats"]["fixture_score"],
        " vs. team ",
        fpl.players[player]["team"]["name"],
    )


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
    players_sorted = sorted(fpl.players.keys(), key=lambda x: x[0])
    player = st.selectbox("Select a player", players_sorted, index=0)
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


if __name__ == "__main__":
    main()
