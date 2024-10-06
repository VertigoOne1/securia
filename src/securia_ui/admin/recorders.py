import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd
import time

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if 'update_recorder' not in st.session_state:
    st.session_state['update_recorder'] = 'false'
if 'delete_recorder' not in st.session_state:
    st.session_state['delete_recorder'] = 'false'
if 'add_recorder' not in st.session_state:
    st.session_state['add_recorder'] = 'false'
if 'link_recorder' not in st.session_state:
    st.session_state['link_recorder'] = 'false'


st.set_page_config(page_title="Securia - Recorders", layout="wide")
st.title("Recorder management")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_users_dataset() -> pd.DataFrame:
    data = logic.fetch_users(token=st.session_state.token)
    if data:
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_recorders_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_recorders(token=st.session_state.token)
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

def create_recorder(updated_data):
    logger.info(f"Create recorder: {updated_data['friendly_name']}")
    logger.debug("Updated data:", updated_data)
    if updated_data["owner_user_id"] == "None":
        updated_data["owner_user_id"] = 0
    response = logic.create_recorder(updated_data, token=st.session_state.token)
    return response

def update_recorder(id, updated_data):
    logger.info(f"Updating recorder with ID: {id}")
    logger.debug("Updated data:", updated_data)
    if updated_data["owner_user_id"] == "None":
        updated_data["owner_user_id"] = 0
    response = logic.update_recorder(id, updated_data, token=st.session_state.token)
    return response

def link_recorder(recorder_id, user_id):
    logger.info(f"Updating recorder ID:{recorder_id} linked with with user ID: {user_id}")
    updated_recorder = {}
    updated_recorder['owner_user_id'] = str(user_id)
    response = logic.update_recorder(recorder_id, updated_recorder, token=st.session_state.token)
    return response

def delete_recorder(id):
    logger.info(f"Deleting recorder with ID: {id}")
    response = logic.delete_recorder(id, token=st.session_state.token)
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
    col1, col2, col3, col4, col5, col6 = st.columns(spec=[0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
    with col1:
        refresh = st.button("Refresh")
    with col2:
        update_recorder_pane = st.button("Update Recorder")
    with col3:
        add_recorder_pane = st.button("New Recorder")
    with col4:
        delete_recorder_pane = st.button("Delete Recorder")
    with col5:
        link_recorder_pane = st.button("Link Recorder")
    if refresh:
        st.rerun()
    recorders_selected_id = None
    if len(recorders_event.selection.rows) > 0:
        selected_recorder = recorders_event.selection.rows
        recorders_filtered_df = recorders.iloc[selected_recorder]
        recorders_selected_id = recorders_filtered_df['id'].values[0]
# This is done because the state of the buttons is "sticky", which results in multiple edit panes
if recorders_selected_id is not None:
    if update_recorder_pane:
        st.session_state['update_recorder'] = 'true'
    if delete_recorder_pane:
        st.session_state['delete_recorder'] = 'true'
    if add_recorder_pane:
        st.session_state['add_recorder'] = 'true'
    if link_recorder_pane:
        st.session_state['link_recorder'] = 'true'
if recorders_selected_id is None:
    if add_recorder_pane:
        st.session_state['add_recorder'] = 'true'
    if delete_recorder_pane:
        st.session_state['delete_recorder'] = 'true'
    if update_recorder_pane:
        st.session_state['update_recorder'] = 'true'
    if link_recorder_pane:
        st.session_state['link_recorder'] = 'true'
# st.write(f"{st.session_state['add_recorder']} - {st.session_state['update_recorder']} - {st.session_state['delete_recorder']} - {st.session_state['link_recorder']}")

    # recorder_uuid: UUID
    # uri: str
    # owner_user_id: Optional[int] = None
    # friendly_name: Optional[str] = None
    # owner: Optional[str] = None
    # type: Optional[str] = None
    # location: Optional[str] = None
    # contact: Optional[str] = None

if st.session_state['add_recorder'] == 'true':
    st.header("Add Recorder")
    with st.form(key=f"addrecorder"):
        input11 = st.text_input(label='recorder_uuid')
        input22 = st.text_input(label='owner_user_id')
        input33 = st.text_input(label='friendly_name')
        input44 = st.text_input(label='owner')
        input55 = st.text_input(label='type')
        input66 = st.text_input(label='location')
        input77 = st.text_input(label='contact')
        input88 = st.text_input(label='uri')
        submit_button_add_recorder = st.form_submit_button(label='Add Recorder')
        if submit_button_add_recorder:
            updated_recorder = {}
            updated_recorder['recorder_uuid'] = input11
            updated_recorder['owner_user_id'] = input22
            updated_recorder['friendly_name'] = input33
            updated_recorder['owner'] = input44
            updated_recorder['type'] = input55
            updated_recorder['location'] = input66
            updated_recorder['contact'] = input77
            updated_recorder['uri'] = input88
            result = create_recorder(updated_recorder)
            if result:
                # st.write(f"{result.json()}")
                st.success(f"Recorder: {updated_recorder['friendly_name']} successfully created")
                st.session_state['add_recorder'] = "false"
                st.session_state['delete_recorder'] = "false"
                st.session_state['update_recorder'] = "false"
            else:
                st.write(f"{result.json()}")
                st.error(f"Recorder: {updated_recorder['friendly_name']} not created")
                st.session_state['add_recorder'] = "false"
                st.session_state['delete_recorder'] = "false"
                st.session_state['update_recorder'] = "false"
elif st.session_state['update_recorder'] == 'true':
    st.header("Update Recorder")
    try:
        with st.form(key="updaterecorder"):
            input1 = st.text_input(value=f"{recorders_filtered_df['recorder_uuid'].values[0]}", label='recorder_uuid')
            input2 = st.text_input(value=f"{recorders_filtered_df['owner_user_id'].values[0]}", label='owner_user_id')
            input3 = st.text_input(value=f"{recorders_filtered_df['friendly_name'].values[0]}", label='friendly_name')
            input4 = st.text_input(value=f"{recorders_filtered_df['owner'].values[0]}", label='owner')
            input5 = st.text_input(value=f"{recorders_filtered_df['type'].values[0]}", label='type')
            input6 = st.text_input(value=f"{recorders_filtered_df['location'].values[0]}", label='location')
            input7 = st.text_input(value=f"{recorders_filtered_df['contact'].values[0]}", label='contact')
            input8 = st.text_input(value=f"{recorders_filtered_df['uri'].values[0]}", label='uri')
            submit_button_update_recorder = st.form_submit_button()

            if submit_button_update_recorder:
                updated_recorder = {}
                updated_recorder['recorder_uuid'] = input1
                updated_recorder['owner_user_id'] = input2
                updated_recorder['friendly_name'] = input3
                updated_recorder['owner'] = input4
                updated_recorder['type'] = input5
                updated_recorder['location'] = input6
                updated_recorder['contact'] = input7
                updated_recorder['contact'] = input7
                updated_recorder['uri'] = input8
                result = update_recorder(recorders_selected_id, updated_recorder)
                if result:
                    # st.write(f"{result.json()}")
                    # st.toast("Recorder successfully updated")
                    st.success("Recorder successfully updated")
                    st.session_state['add_recorder'] = "false"
                    st.session_state['delete_recorder'] = "false"
                    st.session_state['update_recorder'] = "false"
                else:
                    st.write(f"{result.json()}")
                    st.error("Recorder not updated")
                    st.session_state['add_recorder'] = "false"
                    st.session_state['delete_recorder'] = "false"
                    st.session_state['update_recorder'] = "false"
    except:
        st.warning("Please select a recorder to update first")
        st.session_state['add_recorder'] = "false"
        st.session_state['delete_recorder'] = "false"
        st.session_state['update_recorder'] = "false"
elif st.session_state['delete_recorder'] == 'true':
    st.header("Delete Recorder")
    try:
        result = delete_recorder(recorders_selected_id)
        if result:
            st.success(f"Recorder ID:{recorders_selected_id} successfully deleted")
            st.session_state['add_recorder'] = "false"
            st.session_state['delete_recorder'] = "false"
            st.session_state['update_recorder'] = "false"
        else:
            if result.status_code == 422:
                st.warning("Please select a recorder to delete first")
                st.session_state['add_recorder'] = "false"
                st.session_state['delete_recorder'] = "false"
                st.session_state['update_recorder'] = "false"
            else:
                st.write(f"{result.status_code} - {result.json()}")
                st.error("Recorder not deleted")
                st.session_state['add_recorder'] = "false"
                st.session_state['delete_recorder'] = "false"
                st.session_state['update_recorder'] = "false"
    except:
        st.write(recorders_selected_id)
        st.warning("Please select a recorder to delete first")
        st.session_state['add_recorder'] = "false"
        st.session_state['delete_recorder'] = "false"
        st.session_state['update_recorder'] = "false"
elif st.session_state['link_recorder'] == 'true':
    st.header("Link Recorder")
    with st.expander("Users", expanded=True):
        # Fetch users data
        users = get_users_dataset()
        users_display_columns = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        users_event = st.dataframe(
            users[users_display_columns],
            # column_config=column_configuration,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        col1, col2 = st.columns(spec=[0.1, 0.9])
        with col1:
            link_recorder_user_pane = st.button("Link User to Recorder")
        users_selected_id = None
        if len(users_event.selection.rows) > 0:
            selected_user = users_event.selection.rows
            users_filtered_df = users.iloc[selected_user]
            users_selected_id = users_filtered_df['id'].values[0]
        if link_recorder_user_pane:
            st.write(f"Linking: {recorders_selected_id} to {users_selected_id}")
            result = link_recorder(recorders_selected_id, users_selected_id)
            if result:
                st.success(f"Recorder ID:{recorders_selected_id} successfully linked")
                st.session_state['add_recorder'] = "false"
                st.session_state['delete_recorder'] = "false"
                st.session_state['update_recorder'] = "false"
                st.session_state['link_recorder'] = "false"
            else:
                if result.status_code == 422:
                    st.warning("Please select a user to link first")
                    st.session_state['add_recorder'] = "false"
                    st.session_state['delete_recorder'] = "false"
                    st.session_state['update_recorder'] = "false"
                    st.session_state['link_recorder'] = "false"
                else:
                    st.write(f"{result.status_code} - {result.json()}")
                    st.error("Recorder not linked")
                    st.session_state['add_recorder'] = "false"
                    st.session_state['delete_recorder'] = "false"
                    st.session_state['update_recorder'] = "false"
                    st.session_state['link_recorder'] = "false"
        # else:
        #     st.session_state['link_recorder'] = "false"