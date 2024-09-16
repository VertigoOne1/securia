#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import streamlit as st
import requests
import pandas as pd
import s3fs

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

def fetch_images_by_channel(channel_id, limit, sort):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }

    response = requests.get(f"{API_BASE}/image/channel/{channel_id}?{urlencode(params)}")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch details: {response.status_code}")
        return None

def fetch_detections_by_channel(channel_id, limit, sort):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }

    response = requests.get(f"{API_BASE}/detection/channel/{channel_id}?{urlencode(params)}")
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

@st.cache_data
def get_images_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = fetch_images_by_channel(channel_id,limit,sort)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data
def get_detections_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = fetch_detections_by_channel(channel_id,limit,sort)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

def main():

    st.set_page_config(page_title="Securia", layout="wide")

    left, middle = st.columns(2)
    with left:
        st.title("Recorders")
        recorders = get_recorders_dataset()
        recorders_display_columns = ['friendly_name', 'uri']
        recorders_event = st.dataframe(
            recorders[recorders_display_columns],
            # column_config=column_configuration,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        st.header("Channels")
        selected_recorder = recorders_event.selection.rows
        recorders_filtered_df = recorders.iloc[selected_recorder]
        try:
            recorder_selected_id = recorders_filtered_df['id'].values[0]

            channels = get_channels_dataset(recorder_selected_id)
            channels_display_columns = ['friendly_name', 'channel_id']
            channels_event = st.dataframe(
                channels[channels_display_columns],
                # column_config=column_configuration,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )
        except:
            st.write("No recorder selected")

        selected_channel = channels_event.selection.rows
        channels_filtered_df = channels.iloc[selected_channel]
        channel_selected_id = channels_filtered_df['id'].values[0]

        st.header("Detections")
        detections = get_detections_by_channel_dataset(channel_selected_id, 10, "desc")

        detections_display_columns = ['friendly_name', 'channel_id']
        detections_event = st.dataframe(
            detections,
            # column_config=column_configuration,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

    with middle:
        try:
            tab1, tab2 = st.tabs(["Latest", "Detections"])
            with tab1:
                # st.header("Latest Captures")

                images = get_images_by_channel_dataset(channel_selected_id, 10, "desc")
                # images_display_columns = ['collected_timestamp']
                # images_event = st.dataframe(
                #     images[images_display_columns],
                #     # column_config=column_configuration,
                #     use_container_width=True,
                #     hide_index=True,
                #     on_select="rerun",
                #     selection_mode="single-row",
                # )
                fs = s3fs.S3FileSystem(anon=False, key=config['storage']['access_key'], secret=config['storage']['secret_access_key'], endpoint_url='http://10.0.0.59:32650')
                for index, row in images.iterrows():
                    st.write(row['collected_timestamp'])
                    st.image(fs.open(row['s3_path'], mode='rb').read())

        except:
            st.write("No Channel selected")

            # st.image(fs.open('test/56b9c7d4-155e-4903-8b44-2066907a01e8', mode='rb').read())
            # # st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
if __name__ == "__main__":
    main()