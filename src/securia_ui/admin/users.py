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
st.title("User management")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_users_dataset() -> pd.DataFrame:
    users_data = logic.fetch_users(token=st.session_state.token)
    if users_data:
        df = pd.DataFrame(users_data)
        return df
    else:
        return pd.DataFrame()

def create_user(updated_data):
    logger.info(f"Create user: {updated_data['username']}")
    logger.debug("Updated data:", updated_data)
    response = logic.create_user(updated_data, token=st.session_state.token)
    return response

def update_user(user_id, updated_data):
    logger.info(f"Updating user with ID: {user_id}")
    logger.debug("Updated data:", updated_data)
    response = logic.update_user(user_id, updated_data, token=st.session_state.token)
    return response

def delete_user(user_id):
    logger.info(f"Deleting user with ID: {user_id}")
    response = logic.delete_user(user_id, token=st.session_state.token)
    return response

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
    col1, col2, col3, col4, col5 = st.columns(spec=[0.2, 0.2, 0.2, 0.2, 0.6])
    with col1:
        refresh = st.button("Refresh")
    with col2:
        update_user_pane = st.button("Update User")
    with col3:
        add_user_pane = st.button("New User")
    with col4:
        delete_user_pane = st.button("Delete User")
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
    if delete_user_pane:
        st.session_state['delete_user'] = 'true'
    if add_user_pane:
        st.session_state['add_user'] = 'true'
if users_selected_id is None:
    if add_user_pane:
        st.session_state['add_user'] = 'true'
    if delete_user_pane:
        st.session_state['delete_user'] = 'true'
    if update_user_pane:
        st.session_state['update_user'] = 'true'
# st.write(f"{st.session_state['add_user']} - {st.session_state['update_user']} - {st.session_state['delete_user']}")
if st.session_state['add_user'] == 'true':
    st.header("Add User")
    with st.form(key=f"adduser"):
        input11 = st.text_input(label='Username')
        input22 = st.text_input(label='Password', type="password")
        input33 = st.text_input(label='Email')
        input44 = st.text_input(label='First Name')
        input55 = st.text_input(label='Last Name')
        input66 = st.text_input(label='Company')
        input77 = st.selectbox(
            "Role",
            ("super", "admin", "user", "guest"),
            )
        submit_button_add_user = st.form_submit_button(label='Add User')
        if submit_button_add_user:
            updated_user = {}
            updated_user['username'] = input11
            updated_user['password'] = input22
            updated_user['email'] = input33
            updated_user['first_name'] = input44
            updated_user['last_name'] = input55
            updated_user['company'] = input66
            updated_user['role'] = input77
            result = create_user(updated_user)
            if result:
                # st.write(f"{result.json()}")
                st.success(f"User: {updated_user['username']} successfully created")
                st.session_state['add_user'] = "false"
                st.session_state['delete_user'] = "false"
                st.session_state['update_user'] = "false"
            else:
                st.write(f"{result.json()}")
                st.error(f"User: {updated_user['username']} not created")
                st.session_state['add_user'] = "false"
                st.session_state['delete_user'] = "false"
                st.session_state['update_user'] = "false"
elif st.session_state['update_user'] == 'true':
    st.header("Update User")
    try:
        with st.form(key="updateuser"):
            input1 = st.text_input(value=f"{users_filtered_df['username'].values[0]}", label='username')
            input5 = st.text_input(value=f"{users_filtered_df['email'].values[0]}", label='email')
            input2 = st.text_input(value=f"{users_filtered_df['first_name'].values[0]}", label='first_name')
            input3 = st.text_input(value=f"{users_filtered_df['last_name'].values[0]}", label='last_name')
            input4 = st.text_input(value=f"{users_filtered_df['company'].values[0]}", label='company')
            input6 = st.selectbox(
                "Role",
                ("super", "admin", "user", "guest"),
                )
            submit_button_update_user = st.form_submit_button()

            if submit_button_update_user:
                updated_user = {}
                updated_user['username'] = input1
                updated_user['first_name'] = input2
                updated_user['last_name'] = input3
                updated_user['company'] = input4
                updated_user['email'] = input5
                updated_user['role'] = input6
                result = update_user(users_selected_id, updated_user)
                if result:
                    # st.write(f"{result.json()}")
                    # st.toast("User successfully updated")
                    st.success("User successfully updated")
                    st.session_state['add_user'] = "false"
                    st.session_state['delete_user'] = "false"
                    st.session_state['update_user'] = "false"
                else:
                    st.write(f"{result.json()}")
                    st.error("User not updated")
                    st.session_state['add_user'] = "false"
                    st.session_state['delete_user'] = "false"
                    st.session_state['update_user'] = "false"
    except:
        st.warning("Please select a user to update first")
        st.session_state['add_user'] = "false"
        st.session_state['delete_user'] = "false"
        st.session_state['update_user'] = "false"
elif st.session_state['delete_user'] == 'true':
    st.header("Delete User")
    try:
        result = delete_user(users_selected_id)
        if result:
            st.success(f"User ID:{users_selected_id} successfully deleted")
            st.session_state['add_user'] = "false"
            st.session_state['delete_user'] = "false"
            st.session_state['update_user'] = "false"
        else:
            if result.status_code == 422:
                st.warning("Please select a user to delete first")
                st.session_state['add_user'] = "false"
                st.session_state['delete_user'] = "false"
                st.session_state['update_user'] = "false"
            else:
                st.write(f"{result.status_code} - {result.json()}")
                st.error("User not deleted")
                st.session_state['add_user'] = "false"
                st.session_state['delete_user'] = "false"
                st.session_state['update_user'] = "false"
    except:
        st.write(users_selected_id)
        st.warning("Please select a user to delete first")
        st.session_state['add_user'] = "false"
        st.session_state['delete_user'] = "false"
        st.session_state['update_user'] = "false"