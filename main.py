import matplotlib.pyplot as plt
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pprint import pprint
from src.querier import FPLQuerier


def main():
    # Initialize querier
    fpl = FPLQuerier()
    st.title("FPyL")
    # TODO: Top X Players
    # Search bar
    # First div with a clickable table
    players_sorted = sorted(fpl.players.keys(), key=lambda x: x[0])
    st.header("Player KPI")
    # Display the selected option
    player = st.selectbox(
        'Select a player',
        players_sorted,
    )
    kpi = fpl.query_player_kpi(fpl.players[player])
    fig = go.Figure()
    x = list(map(lambda x: f"GW{x['round']}", kpi))
    gi = list(map(lambda x: x['gi'], kpi))
    xgi = list(map(lambda x: x['xgi'], kpi))
    form = list(map(lambda x: x['form'], kpi))
    # form = list(map(lambda x: x['form'], kpi))
    fig.add_trace(go.Scatter(x=x, y=gi, mode='lines+markers', name='GI'))
    fig.add_trace(go.Scatter(x=x, y=xgi, mode='lines+markers', name='xGI'))
    # fig.add_trace(go.Scatter(x=x, y=form, mode='lines', name='Goals+Assists'))
    fig.update_layout(
        xaxis_title='GW',
        yaxis_title='',
        title='Dynamic Scatter Plot',
        hovermode="closest",
    )
    st.plotly_chart(fig)

if __name__ == '__main__':
    main()