#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import streamlit as st
import requests
import pandas as pd

import logger

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

# if __name__ == '__main__':
#     logger.info(f"Start - {config['general']['app_name']}")
#     # scheduling = start_schedules()
#     # apiserver = start_api_server()

#     st.write("Hello world 5")


API_BASE = config["api"]["uri"]

def fetch_recorders():
    response = requests.get(f"{API_BASE}/recorder")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return None

def fetch_channels(recorder_id):
    response = requests.get(f"{API_BASE}/channels_by_recorder/{recorder_id}")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch details: {response.status_code}")
        return None

@st.cache_data
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = fetch_recorders()
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data
def get_channels_dataset(recorder_id) -> pd.DataFrame:
    channel_data = fetch_channels(recorder_id)
    if channel_data:
        df = pd.DataFrame(channel_data)
        return df
    else:
        return pd.DataFrame()

def main():
    st.title("Recorders")

    recorders = get_recorders_dataset()

    recorders_event = st.dataframe(
        recorders,
        # column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    st.header("Recorder Channels")
    selected_recorder = recorders_event.selection.rows
    filtered_df = recorders.iloc[selected_recorder]
    try:
        selected_id = filtered_df['id'].values[0]

        channels = get_channels_dataset(selected_id)
        channels_event = st.dataframe(
            channels,
            # column_config=column_configuration,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )
    except:
        st.write("No recorder selected")
if __name__ == "__main__":
    main()