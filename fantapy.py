import streamlit as st, pandas as pd
import plotly.graph_objects as go
import time
from pprint import pprint
from src.querier import FPLQuerier
from src.data import FPLData
from src.visualiser import FPLVisualiser


# Apply custom CSS to control the width
class GlobalState:
    def __init__(self):
        self.players = []
        self.player = "Haaland (MCI)"
        self.last_refresh = time.time()


state = GlobalState()

fpl = FPLData()
refresh = 0


def main():
    # Initialize querier
    st.set_page_config(layout="wide")
    # TODO: Pick GW limit of data!
    # TODO: Pick your team and see how it performs
    # TODO: Form should be a function of the last 5 GWs
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
        if len(fpl.player_names) < 1:
            fpl.player_names = sorted(list(fpl.players_by_name.keys()))
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