import streamlit as st
import plotly.graph_objects as go
from pprint import pprint
from src.querier import FPLQuerier

def generate_top_players(fpl: FPLQuerier, container=st):
    """
    Generate table of top players
    """
    results = []
    columns = ['Name', 'Team', 'Position', 'Price', 'Points', 'xGI']
    # TODO: Filter on easy fixtures
    for player in fpl.players:
        pass

def generate_player_metrics(fpl: FPLQuerier, container=st, player=None):
    """
    Generate player metrics
    """
    stats = fpl.players[player]['stats']
    goals, assists, xg, xa, xgi = (
        float(stats['goals']),
        float(stats['assists']),
        float(stats['xg']),
        float(stats['xa']),
        float(stats['xgi']),
    ) 
    gi = goals + assists
    col1, col2, col3 = container.columns(3)
    dgoals = f"{str(round(goals - xg, 2))} ({xg} xG)" if goals != xg else None
    dassists = f"{str(round(assists - xa, 2))} ({xa} xA)" if assists != xa else None
    dxgi = f"{str(round(gi - xgi, 2))} ({xgi} xGI)" if gi != xgi else None
    col1.metric(label='Goals', value=goals, delta=dgoals)
    col2.metric(label='Assists', value=assists, delta=dassists)
    col3.metric(label='xGI', value=xgi, delta=dxgi)
    # TODO: Good pick on fixtures?
    container.write("Fixtures")
    cola, colb, colc, cold, cole = container.columns(5)
    team_strength = fpl.players[player]['team']['strength']
    fixtures = fpl.players[player]['team']['fixtures']
    cola.metric(label=f"GW{fixtures[0]['gw']}", value=fixtures[0]['code'], delta=fixtures[0]['difficulty']-team_strength, delta_color="inverse")
    colb.metric(label=f"GW{fixtures[1]['gw']}", value=fixtures[1]['code'], delta=fixtures[1]['difficulty']-team_strength, delta_color="inverse")
    colc.metric(label=f"GW{fixtures[2]['gw']}", value=fixtures[2]['code'], delta=fixtures[2]['difficulty']-team_strength, delta_color="inverse")
    cold.metric(label=f"GW{fixtures[3]['gw']}", value=fixtures[3]['code'], delta=fixtures[3]['difficulty']-team_strength, delta_color="inverse")
    cole.metric(label=f"GW{fixtures[4]['gw']}", value=fixtures[4]['code'], delta=fixtures[4]['difficulty']-team_strength, delta_color="inverse")

def generate_player_charts(fpl: FPLQuerier, player=None, container=st):
    """
    Generate player KPI
    """
    kpi = fpl.query_player_kpi(player)
    # Generate figure
    fig = go.Figure()
    x = list(map(lambda x: f"GW{x['round']} ({x['opponent']})", kpi))
    gi = list(map(lambda x: x['gi'], kpi))
    xgi = list(map(lambda x: x['xgi'], kpi))
    # form = list(map(lambda x: x['form'], kpi))
    fig.add_trace(go.Scatter(x=x, y=gi, mode='lines+markers', name='GI'))
    fig.add_trace(go.Scatter(x=x, y=xgi, mode='lines+markers', name='xGI'))
    # fig.add_trace(go.Scatter(x=x, y=form, mode='lines', name='Goals+Assists'))
    fig.update_layout(
        xaxis_title='GW',
        yaxis_title='',
        title='Goal Involvements / xGI',
        hovermode="closest",
    )
    fig.update_xaxes(tick0=1, dtick=1)
    fig.update_yaxes(tick0=0, dtick=1, range=[0, round(max(gi + xgi)) + 1])
    container.plotly_chart(fig)
    # Generate figure for form/price

def main():
    # Initialize querier
    fpl = FPLQuerier()
    st.title("FPyL")
    generate_top_players(fpl)
    # Player KPI
    st.header("Player KPI")
    players_sorted = sorted(fpl.players.keys(), key=lambda x: x[0])
    player = st.selectbox(
        'Select a player',
        players_sorted,
        index=0
    )
    generate_player_metrics(fpl, player=player)
    generate_player_charts(fpl, player=player)

if __name__ == '__main__':
    main()