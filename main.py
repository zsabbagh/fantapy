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
    st.set_page_config(layout="wide")
    with st.sidebar:
        st.title("FantaPy!")
        (
            fpl.curr_gw,
            fpl.data,
            fpl.teams,
            fpl.teams_by_name,
            fpl.players,
            fpl.players_by_name,
        ) = FPLQuerier.run(refresh)
        what_to_show = st.multiselect(
            "What to show?",
            [
                "Top players",
                "Player section",
                "Team metrics",
            ],
            ["Top players", "Player section", "Team metrics"],
        )
    if "Top players" in what_to_show:
        FPLVisualiser.top_players(fpl)
    if "Player section" in what_to_show:
        FPLVisualiser.player_section(fpl)
    if "Team metrics" in what_to_show:
        FPLVisualiser.team_metrics(fpl)


if __name__ == "__main__":
    main()
