import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

st.set_page_config(page_title="Securia - Users", layout="wide")
st.title("User management")

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_users_dataset() -> pd.DataFrame:
    recorders_data = logic.fetch_users(token=st.session_state.token)
    if recorders_data:
        df = pd.DataFrame(recorders_data)
        return df
    else:
        return pd.DataFrame()

def update_user(user_id, updated_data):
    # Your existing function to update user data via API
    st.write(f"Updating user with ID: {user_id}")
    st.write("Updated data:", updated_data)
    user = logic.update_user(user_id, updated_data, token=st.session_state.token)
    return user

def data_editor_changed():
    if 'ed' in st.session_state and 'edited_rows' in st.session_state.ed:
        edited_rows = st.session_state.ed['edited_rows']
        successful_updates = []
        failed_updates = []

        for row_index, changed_fields in edited_rows.items():
            user_id = st.session_state.original_df.iloc[row_index]['id']
            response = update_user(user_id, changed_fields)

            if response.status_code == 200:
                successful_updates.append(row_index)
            else:
                failed_updates.append((row_index, response.status_code, response.json()))

        # Update the dataframe with successful changes
        print(st.session_state.ed)
        for row_index in successful_updates:
            st.session_state.users_df.iloc[row_index] = next(iter(st.session_state.ed['edited_rows']))

        # Report successful updates
        if successful_updates:
            st.success(f"Successfully updated {len(successful_updates)} user(s)")

        # Report and rollback failed updates
        if failed_updates:
            for row_index, status_code, error_message in failed_updates:
                st.error(f"Failed to update user at row {row_index}. Status Code: {status_code} - {error_message}")
                # Rollback this specific row
                st.session_state.ed['edited_rows'].iloc[row_index] = st.session_state.original_df.iloc[row_index]

        # If there were any failed updates, we need to reset the data_editor
        if failed_updates:
            st.rerun()

with st.expander("Users", expanded=True):
    # Fetch users data
    if 'original_df' not in st.session_state:
        users = get_users_dataset()
        users_display_columns = ['id', 'username', 'email', 'first_name', 'last_name', 'company', 'role']
        st.session_state.original_df = users[users_display_columns].copy()
        st.session_state.users_df = st.session_state.original_df.copy()

    edited_df = st.data_editor(
        st.session_state.users_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn(
                "ID",
                disabled=True,
            ),
        },
        on_change=data_editor_changed,
        key='ed'
    )

    # Update the users_df in session_state with the latest edits
    st.session_state.users_df = edited_df