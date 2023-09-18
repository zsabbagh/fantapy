import streamlit as st, pandas as pd
import plotly.graph_objects as go
from pprint import pprint
from src.querier import FPLQuerier
from src.data import FPLData
from src.visualiser import FPLVisualiser


# Apply custom CSS to control the width
class GlobalState:
    def __init__(self):
        self.players = []
        self.player = "Haaland (MCI)"


state = GlobalState()

fpl = FPLData()
refresh = 0


def main():
    # Initialize querier
    st.title("FantaPy Premier League \U0001F3C6")
    (
        fpl.curr_gw,
        fpl.data,
        fpl.teams,
        fpl.teams_by_name,
        fpl.players,
        fpl.players_by_name,
    ) = FPLQuerier.run(refresh)
    FPLVisualiser.generate_top_players(fpl)
    FPLVisualiser.generate_player_section(fpl)
    FPLVisualiser.generate_team_metrics(fpl)


if __name__ == "__main__":
    main()
