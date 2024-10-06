import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd
import time

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

st.set_page_config(page_title="Securia - Detection", layout="wide")
st.title("Detections")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_recorders(token=st.session_state.token)
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_detections_summary_dataset(recorder_id) -> pd.DataFrame:
    data = logic.fetch_detections_summary(recorder_id, token=st.session_state.token)
    if data:
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()

with st.expander("Recorders", expanded=True):
    # Fetch Recorder data
    recorders = get_recorders_dataset()
    recorders_display_columns = ['friendly_name', 'uri', 'type', 'location', 'contact']
    recorders_event = st.dataframe(
        recorders[recorders_display_columns],
        # column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    recorders_selected_id = None
    if len(recorders_event.selection.rows) > 0:
        selected_recorder = recorders_event.selection.rows
        recorders_filtered_df = recorders.iloc[selected_recorder]
        recorders_selected_id = recorders_filtered_df['id'].values[0]

if recorders_selected_id is not None:
    # Fetch channels data
    detections_summary = get_detections_summary_dataset(recorders_selected_id)
    df = pd.DataFrame(detections_summary)
    df['collected_timestamp'] = pd.to_datetime(df['collected_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2%}")
    if not detections_summary.empty:
        detections_summary_display_columns = ['collected_timestamp', 'detection_name', 'confidence', 'channel_friendly_name', 'channel_description', 'channel_id']
        channels_event = st.dataframe(
            df[detections_summary_display_columns],
            # detections_summary,
            # column_config=column_configuration,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )