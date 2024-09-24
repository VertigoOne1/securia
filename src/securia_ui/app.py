#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import streamlit as st
import requests, time, jwt
import pandas as pd
import s3fs
from streamlit_autorefresh import st_autorefresh
import logic

import logger

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token, refresh_token_func):
        """
        token: The initial token value.
        refresh_token_func: A function to refresh the token.
        """
        self.token = token
        self.payload = jwt.decode(token, options={"verify_signature": False})
        self.expires_at: int = self.payload.get("exp")
        self.refresh_token_func = refresh_token_func  # Function to refresh token

    def is_token_expired(self):
        # Check if the token is about to expire within the next 5 minutes (300 seconds)
        return time.time() > self.expires_at - 300

    def refresh_token(self):
        # Call the refresh token function and update the token and expiration
        new_token = self.refresh_token_func()
        self.token = new_token
        self.payload = jwt.decode(new_token, options={"verify_signature": False})
        self.expires_at = self.payload.get("exp")

    def __call__(self, r):
        # Check if the token is expired or near expiry
        if self.is_token_expired():
            logger.info("Token is about to expire, refreshing token...")
            self.refresh_token()

        r.headers["authorization"] = "Bearer " + self.token
        return r

def login():
    username = config['api']['username']
    password = config['api']['password']
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "api",
        "client_id": "client_id",
        "client_secret": "client_secret"
    }
    try:
        response = requests.post(f"{config['api']['uri']}/token", data=data)

        if response.status_code == 200:
            # Successful login
            token = response.json().get("access_token")
            return token
        else:
            logger.error("Invalid username or password. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"requests - An error occurred: {e}")

@st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_recorders()
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_channels_dataset(recorder_id) -> pd.DataFrame:
    channel_data = logic.fetch_channels(recorder_id)
    if channel_data:
        df = pd.DataFrame(channel_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def get_images_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = logic.fetch_images_by_channel(channel_id,limit,sort)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_detections_by_channel_dataset(channel_id, limit, sort) -> pd.DataFrame:
    image_data = logic.fetch_detections_by_channel(channel_id,limit,sort)
    if image_data:
        df = pd.DataFrame(image_data)
        return df
    else:
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="Securia", layout="wide")
    # count = st_autorefresh(interval=config['general']['auto_refresh_miliseconds'], limit=0, key="imagerefresh")
    with st.sidebar:
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
                                st.image('http://localhost:8501/app/static/no_image.png')
                            else:
                                st.image(fs.open(row['s3_path'], mode='rb').read())
if __name__ == "__main__":
    main()