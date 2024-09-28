import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd
import time

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if 'update_user' not in st.session_state:
    st.session_state['update_user'] = 'false'
if 'delete_user' not in st.session_state:
    st.session_state['delete_user'] = 'false'
if 'add_user' not in st.session_state:
    st.session_state['add_user'] = 'false'

st.set_page_config(page_title="Securia - Users", layout="wide")
st.title("Profile management")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_users_dataset() -> pd.DataFrame:
    users_data = logic.fetch_logged_in_user(st.session_state.logged_in_user, token=st.session_state.token)
    if users_data:
        df = pd.DataFrame(users_data)
        return df
    else:
        return pd.DataFrame()

def update_user(user_id, updated_data):
    logger.info(f"Updating user with ID: {user_id}")
    logger.debug("Updated data:", updated_data)
    response = logic.update_user(user_id, updated_data, token=st.session_state.token)
    return response

with st.expander("Profile", expanded=True):
    # Fetch users data
    users = get_users_dataset()
    users_display_columns = ['id', 'username', 'email', 'first_name', 'last_name', 'company']
    users_event = st.dataframe(
        users[users_display_columns],
        # column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    col1, col2 = st.columns(spec=[0.2, 0.8])
    with col1:
        refresh = st.button("Refresh")
    with col2:
        update_user_pane = st.button("Update")
    if refresh:
        st.rerun()
    users_selected_id = None
    if len(users_event.selection.rows) > 0:
        selected_user = users_event.selection.rows
        users_filtered_df = users.iloc[selected_user]
        users_selected_id = users_filtered_df['id'].values[0]
# This is done because the state of the buttons is "sticky", which results in multiple edit panes
if users_selected_id is not None:
    if update_user_pane:
        st.session_state['update_user'] = 'true'
if users_selected_id is None:
    if update_user_pane:
        st.session_state['update_user'] = 'true'
# st.write(f"{st.session_state['add_user']} - {st.session_state['update_user']} - {st.session_state['delete_user']}")
if st.session_state['update_user'] == 'true':
    st.header("Update Profile")
    try:
        with st.form(key="updateuser"):
            input1 = st.text_input(value=f"{users_filtered_df['username'].values[0]}", label='username')
            input5 = st.text_input(value=f"{users_filtered_df['email'].values[0]}", label='email')
            input2 = st.text_input(value=f"{users_filtered_df['first_name'].values[0]}", label='first_name')
            input3 = st.text_input(value=f"{users_filtered_df['last_name'].values[0]}", label='last_name')
            input4 = st.text_input(value=f"{users_filtered_df['company'].values[0]}", label='company')
            submit_button_update_user = st.form_submit_button()

            if submit_button_update_user:
                updated_user = {}
                updated_user['username'] = input1
                updated_user['first_name'] = input2
                updated_user['last_name'] = input3
                updated_user['company'] = input4
                updated_user['email'] = input5
                result = update_user(users_selected_id, updated_user)
                if result:
                    st.success("User successfully updated")
                    st.session_state['update_user'] = "false"
                else:
                    st.write(f"{result.json()}")
                    st.error("User not updated")
                    st.session_state['update_user'] = "false"
    except:
        st.warning("Please select a user to update first")
        st.session_state['update_user'] = "false"
