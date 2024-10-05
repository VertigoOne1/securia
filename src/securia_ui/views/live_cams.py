#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import streamlit as st
import requests
import pandas as pd
import s3fs
from streamlit_autorefresh import st_autorefresh
import logic

import logger

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

@st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_recorders(token=st.session_state.token)
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_channels_dataset(recorder_id) -> pd.DataFrame:
    channel_data = logic.fetch_channels(recorder_id, token=st.session_state.token)
    if channel_data:
        df = pd.DataFrame(channel_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def get_images_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = logic.fetch_images_by_channel(channel_id,limit,sort, token=st.session_state.token)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_detections_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = logic.fetch_detections_by_channel(channel_id,limit,sort, token=st.session_state.token)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

st.set_page_config(page_title="Securia", layout="wide")
# count = st_autorefresh(interval=config['general']['auto_refresh_miliseconds'], limit=0, key="imagerefresh")
with st.expander("Select Recorder and Channel", expanded=True):
    st.title("Recorders")
    recorders = get_recorders_dataset()
    recorders_display_columns = ['friendly_name']
    recorders_event = st.dataframe(
        recorders[recorders_display_columns],
        # column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    if len(recorders_event.selection.rows) > 0:
        selected_recorder = recorders_event.selection.rows
        recorders_filtered_df = recorders.iloc[selected_recorder]
        recorder_selected_id = recorders_filtered_df['id'].values[0]
    channels_event = None
    if len(recorders_event.selection.rows) > 0:
        st.header("Channels")
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
left, middle = st.columns(2)
with left:
    if channels_event is not None:
        if len(channels_event.selection.rows) > 0:
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
    if channels_event is not None:
        if len(channels_event.selection.rows) > 0:
            tab1, tab2 = st.tabs(["All Images", "Only Detections"])
            with tab1:
                # st.header("Latest Captures")
                if True:
                    images = get_images_by_channel_dataset(channel_selected_id, 5, "desc")
                    # images_display_columns = ['collected_timestamp']
                    # images_event = st.dataframe(
                    #     images[images_display_columns],
                    #     # column_config=column_configuration,
                    #     use_container_width=True,
                    #     hide_index=True,
                    #     on_select="rerun",
                    #     selection_mode="single-row",
                    # )
                    endpoint_url = f"{config['storage']['endpoint_method']}://{config['storage']['endpoint_hostname']}:{config['storage']['port']}"
                    fs = s3fs.S3FileSystem(anon=False, key=config['storage']['access_key'], secret=config['storage']['secret_access_key'], endpoint_url=endpoint_url)
                    for index, row in images.iterrows():
                        st.write(f"{row['s3_path']} - {row['collected_timestamp']}")
                        if "NO_IMAGE" in row['s3_path']:
                            st.image(f"{config['api']['static_content_root']}/no_image.png")
                        else:
                            st.image(fs.open(row['s3_path'], mode='rb').read())