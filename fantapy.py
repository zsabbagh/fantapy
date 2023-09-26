import streamlit as st, pandas as pd
import plotly.graph_objects as go
import time
from pprint import pprint
from src.querier import FPLQuerier
from src.data import FPLData
from src.visualiser import FPLVisualiser

st.set_page_config(layout="wide")

if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = None

fpl = FPLData()
refresh = 0


def main():
    # Initialize querier
    # TODO: Pick GW limit of data!
    # TODO: Pick your team and see how it performs
    # TODO: Form should be a function of 2- GWs,
    # add this to each player
    refresh = st.button("Refresh data")
    print(f"State: {st.session_state['last_refresh']}")
    manager_id = None
    with st.sidebar:
        st.title("FantaPy!")
        manager_id = st.text_input("Manager ID", "3177770")
        if st.session_state["last_refresh"] is None or (
            (time.time() - st.session_state["last_refresh"]) > 3600 and refresh
        ):
            (
                fpl.curr_gw,
                fpl.data,
                fpl.teams,
                fpl.teams_by_name,
                fpl.players,
                fpl.players_by_name,
            ) = FPLQuerier.run()
            st.write("Data refreshed!")
            print(f"State: {st.session_state['last_refresh']}")
        else:
            st.write("Using cached data")
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
    if manager_id is not None:
        fpl.manager_team = FPLQuerier.get_manager_data(manager_id, fpl.curr_gw - 1)
    if "Top players" in what_to_show:
        FPLVisualiser.top_players(fpl)
    if "Player section" in what_to_show:
        FPLVisualiser.player_section(fpl)
    if "Team metrics" in what_to_show:
        FPLVisualiser.team_metrics(fpl)


if __name__ == "__main__":
    main()
