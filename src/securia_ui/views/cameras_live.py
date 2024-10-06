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
    image_data = logic.fetch_images_by_channel(channel_id, limit,sort, token=st.session_state.token)
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

@st.cache_data(ttl=5)
def get_camera_grid_dataset(recorder_id) -> pd.DataFrame:
    import json
    data = logic.cameras_view(recorder_id, token=st.session_state.token)
    if data:
        df = pd.DataFrame(json.loads(data))
        return df
    else:
        return pd.DataFrame()

st.set_page_config(page_title="Securia - Cameras Live", layout="wide")
count = st_autorefresh(interval=config['general']['auto_refresh_miliseconds'], limit=0, key="imagerefresh")
st.write(f"Refresh - Interval = {config['general']['auto_refresh_miliseconds']}ms , counter: {count}")

endpoint_url = f"{config['storage']['endpoint_method']}://{config['storage']['endpoint_hostname']}:{config['storage']['port']}"
fs = s3fs.S3FileSystem(anon=False, key=config['storage']['access_key'], secret=config['storage']['secret_access_key'], endpoint_url=endpoint_url)


with st.expander(label='Recorders', expanded=True):
    recorders = get_recorders_dataset()
    # st.write(recorders)
    recorders_display_columns = ['friendly_name', 'id']
    recorders_event = st.dataframe(
        recorders[recorders_display_columns],
        # column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",  # Changed to allow multiple row selection
    )
    # st.write(recorders_event)
    if len(recorders_event.selection.rows) > 0:
        selected_recorders = recorders_event.selection.rows
        # st.write(selected_recorders)
        recorder_ids = []
        for recorder in selected_recorders:
                recorders_filtered_df = recorders.iloc[recorder]
                # st.dataframe(recorders_filtered_df)
                images = get_camera_grid_dataset(recorders_filtered_df['id'])
                st.write(len(images))
                st.subheader(f"Recorder: {recorders_filtered_df['friendly_name']}")
                for index, row in images.iterrows():
                    if "NO_IMAGE" in row['image_s3']:
                        st.image(f"{config['api']['static_content_root']}/no_image.png")
                    else:
                        st.image(fs.open(row['image_s3'], mode='rb').read())