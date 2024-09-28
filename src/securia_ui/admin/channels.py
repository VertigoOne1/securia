import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd
import time

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if 'update_channel' not in st.session_state:
    st.session_state['update_channel'] = 'false'
if 'delete_channel' not in st.session_state:
    st.session_state['delete_channel'] = 'false'
if 'add_channel' not in st.session_state:
    st.session_state['add_channel'] = 'false'

st.set_page_config(page_title="Securia - Channels", layout="wide")
st.title("Channel management")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_recorders(token=st.session_state.token)
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_channels_dataset(id) -> pd.DataFrame:
    channels_data = logic.fetch_channels(id, token=st.session_state.token)
    if channels_data:
        df = pd.DataFrame(channels_data)
        return df
    else:
        return pd.DataFrame()

def create_channel(updated_data):
    logger.info(f"Create channel: {updated_data['channel_id']}")
    logger.debug("Updated data:", updated_data)
    response = logic.create_channel(updated_data, token=st.session_state.token)
    return response

def update_channel(channel_id, updated_data):
    logger.info(f"Updating channel with ID: {channel_id}")
    logger.debug("Updated data:", updated_data)
    response = logic.update_channel(channel_id, updated_data, token=st.session_state.token)
    return response

def delete_channel(channel_id):
    logger.info(f"Deleting channel with ID: {channel_id}")
    response = logic.delete_channel(channel_id, token=st.session_state.token)
    return response

with st.expander("Recorders", expanded=True):
    # Fetch Recorder data
    recorders = get_recorders_dataset()
    recorders_display_columns = ['friendly_name', 'uri', 'recorder_uuid', 'owner_user_id', 'owner', 'type', 'location', 'contact']
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

with st.expander("Channels", expanded=True):
    if recorders_selected_id is not None:
        # Fetch channels data
        channels = get_channels_dataset(recorders_selected_id)
        if not channels.empty:
            channels_display_columns = ['channel_id', 'friendly_name', 'description','fid']
            channels_event = st.dataframe(
                channels[channels_display_columns],
                # column_config=column_configuration,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )
        else:
            channels_event = st.dataframe(pd.DataFrame(),selection_mode="single-row", on_select="rerun")
        col1, col2, col3, col4, col5 = st.columns(spec=[0.2, 0.2, 0.2, 0.2, 0.6])
        with col1:
            refresh = st.button("Refresh")
        with col2:
            update_channel_pane = st.button("Update Channel")
        with col3:
            add_channel_pane = st.button("New Channel")
        with col4:
            delete_channel_pane = st.button("Delete Channel")
        if refresh:
            st.rerun()
        channels_selected_id = None
        if len(channels_event.selection.rows) > 0:
            selected_channel = channels_event.selection.rows
            channels_filtered_df = channels.iloc[selected_channel]
            channels_selected_id = channels_filtered_df['id'].values[0]
        # This is done because the state of the buttons is "sticky", which results in multiple edit panes
        if channels_selected_id is not None:
            if update_channel_pane:
                st.session_state['update_channel'] = 'true'
            if delete_channel_pane:
                st.session_state['delete_channel'] = 'true'
            if add_channel_pane:
                st.session_state['add_channel'] = 'true'
        if channels_selected_id is None:
            if add_channel_pane:
                st.session_state['add_channel'] = 'true'
            if delete_channel_pane:
                st.session_state['delete_channel'] = 'true'
            if update_channel_pane:
                st.session_state['update_channel'] = 'true'
        st.write(f"{st.session_state['add_channel']} - {st.session_state['update_channel']} - {st.session_state['delete_channel']}")
        if st.session_state['add_channel'] == 'true':
            st.header("Add Channel")
            with st.form(key=f"addchannel"):
                input11 = st.text_input(label='channel_id')
                input22 = st.text_input(label='friendly_name')
                input33 = st.text_input(label='description')
                input44 = st.text_input(label='fid')
                submit_button_add_channel = st.form_submit_button(label='Add Channel')
                if submit_button_add_channel:
                    updated_channel = {}
                    updated_channel['channel_id'] = input11
                    updated_channel['friendly_name'] = input22
                    updated_channel['description'] = input33
                    updated_channel['fid'] = input44
                    result = create_channel(updated_channel)
                    if result:
                        # st.write(f"{result.json()}")
                        st.success(f"Channel: {updated_channel['channel_id']} successfully created")
                        st.session_state['add_channel'] = "false"
                        st.session_state['delete_channel'] = "false"
                        st.session_state['update_channel'] = "false"
                    else:
                        st.write(f"{result.json()}")
                        st.error(f"Channel: {updated_channel['channel_id']} not created")
                        st.session_state['add_channel'] = "false"
                        st.session_state['delete_channel'] = "false"
                        st.session_state['update_channel'] = "false"
        elif st.session_state['update_channel'] == 'true':
            st.header("Update Channel")
            try:
                with st.form(key="updatechannel"):
                    input1 = st.text_input(value=f"{channels_filtered_df['channel_id'].values[0]}", label='channel_id')
                    input2 = st.text_input(value=f"{channels_filtered_df['friendly_name'].values[0]}", label='friendly_name')
                    input3 = st.text_input(value=f"{channels_filtered_df['description'].values[0]}", label='description')
                    input4 = st.text_input(value=f"{channels_filtered_df['fid'].values[0]}", label='fid')
                    submit_button_update_channel = st.form_submit_button()

                    if submit_button_update_channel:
                        updated_channel = {}
                        updated_channel['channel_id'] = input1
                        updated_channel['friendly_name'] = input2
                        updated_channel['description'] = input3
                        updated_channel['fid'] = input4
                        result = update_channel(channels_selected_id, updated_channel)
                        if result:
                            # st.write(f"{result.json()}")
                            # st.toast("Channel successfully updated")
                            st.success("Channel successfully updated")
                            st.session_state['add_channel'] = "false"
                            st.session_state['delete_channel'] = "false"
                            st.session_state['update_channel'] = "false"
                        else:
                            st.write(f"{result.json()}")
                            st.error("Channel not updated")
                            st.session_state['add_channel'] = "false"
                            st.session_state['delete_channel'] = "false"
                            st.session_state['update_channel'] = "false"
            except:
                st.warning("Please select a channel to update first")
                st.session_state['add_channel'] = "false"
                st.session_state['delete_channel'] = "false"
                st.session_state['update_channel'] = "false"
        elif st.session_state['delete_channel'] == 'true':
            st.header("Delete Channel")
            try:
                result = delete_channel(channels_selected_id)
                if result:
                    st.success(f"Channel ID:{channels_selected_id} successfully deleted")
                    st.session_state['add_channel'] = "false"
                    st.session_state['delete_channel'] = "false"
                    st.session_state['update_channel'] = "false"
                else:
                    if result.status_code == 422:
                        st.warning("Please select a channel to delete first")
                        st.session_state['add_channel'] = "false"
                        st.session_state['delete_channel'] = "false"
                        st.session_state['update_channel'] = "false"
                    else:
                        st.write(f"{result.status_code} - {result.json()}")
                        st.error("Channel not deleted")
                        st.session_state['add_channel'] = "false"
                        st.session_state['delete_channel'] = "false"
                        st.session_state['update_channel'] = "false"
            except:
                st.write(channels_selected_id)
                st.warning("Please select a channel to delete first")
                st.session_state['add_channel'] = "false"
                st.session_state['delete_channel'] = "false"
                st.session_state['update_channel'] = "false"