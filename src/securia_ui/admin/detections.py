import streamlit as st
import logic, logger
from envyaml import EnvYAML
import pandas as pd
import time, s3fs

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if 'update_channel' not in st.session_state:
    st.session_state['update_channel'] = 'false'
if 'delete_channel' not in st.session_state:
    st.session_state['delete_channel'] = 'false'
if 'add_channel' not in st.session_state:
    st.session_state['add_channel'] = 'false'

st.set_page_config(page_title="Securia - Detection Explorer", layout="wide")
st.title("Detection Explorer")

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

# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_images_dataset(id, limit) -> pd.DataFrame:
    images_data = logic.fetch_images(id, limit, token=st.session_state.token)
    if images_data:
        df = pd.DataFrame(images_data)
        return df
    else:
        return pd.DataFrame()


# @st.cache_data(ttl=config['general']['dataframe_cache_expire_seconds'])
def get_detections_dataset(id) -> pd.DataFrame:
    detections_data = logic.fetch_detections(id, token=st.session_state.token)
    if detections_data:
        df = pd.DataFrame(detections_data)
        return df
    else:
        return pd.DataFrame()

def update_image(image_id, updated_data):
    logger.info(f"Updating image with ID: {image_id}")
    logger.debug("Updated data:", updated_data)
    response = logic.update_image(image_id, updated_data, token=st.session_state.token)
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
        channels_selected_id = None
        if len(channels_event.selection.rows) > 0:
            selected_channel = channels_event.selection.rows
            channels_filtered_df = channels.iloc[selected_channel]
            channels_selected_id = channels_filtered_df['id'].values[0]
    else:
      channels_selected_id = None

with st.expander("Images", expanded=True):
    if channels_selected_id is not None:
        # Fetch images data
        images = get_images_dataset(channels_selected_id, limit=5)
        if not images.empty:
            images_display_columns = ['id', 's3_path', 'content_length','collected_timestamp']
            images_event = st.dataframe(
                images[images_display_columns],
                # column_config=column_configuration,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )
        else:
            images_event = st.dataframe(pd.DataFrame(),selection_mode="single-row", on_select="rerun")
        images_selected_id = None
        if len(images_event.selection.rows) > 0:
            selected_image = images_event.selection.rows
            images_filtered_df = images.iloc[selected_channel]
            images_selected_id = images_filtered_df['id'].values[0]
            selected_image_index = list(images_event.selection.rows)[0]
            images_selected_row = images.iloc[selected_image_index]
            images_selected_id = images_selected_row['id']
    else:
      images_selected_id = None

with st.expander("Detections", expanded=True):
  if images_selected_id is not None:
    col1, col2 = st.columns(2)

    with col1:
      # Fetch images data
      detections = get_detections_dataset(images_selected_id)
      if not detections.empty:
          detections_display_columns = ['detection_name', 'confidence','xyxy']
          detections_event = st.dataframe(
              detections[detections_display_columns],
              # column_config=column_configuration,
              use_container_width=True,
              hide_index=True,
              on_select="rerun",
              selection_mode="single-row",
          )
      else:
          detections_event = st.dataframe(pd.DataFrame(),selection_mode="single-row", on_select="rerun")

    with col2:
      if images_selected_id is not None:
        s3_path = images_selected_row['s3_path']
        endpoint_url = f"{config['storage']['endpoint_method']}://{config['storage']['endpoint_hostname']}:{config['storage']['port']}"
        fs = s3fs.S3FileSystem(anon=False, key=config['storage']['access_key'], secret=config['storage']['secret_access_key'], endpoint_url=endpoint_url)
        if "NO_IMAGE" in images_selected_row['s3_path']:
            st.image(f"{config['api']['static_content_root']}/no_image.png")
        else:
            st.image(fs.open(images_selected_row['s3_path'], mode='rb').read())
      else:
          pass

            # # This is done because the state of the buttons is "sticky", which results in multiple edit panes
            # if channels_selected_id is not None:
            #     if update_channel_pane:
            #         st.session_state['update_channel'] = 'true'
            #     if delete_channel_pane:
            #         st.session_state['delete_channel'] = 'true'
            #     if add_channel_pane:
            #         st.session_state['add_channel'] = 'true'
            # if channels_selected_id is None:
            #     if add_channel_pane:
            #         st.session_state['add_channel'] = 'true'
            #     if delete_channel_pane:
            #         st.session_state['delete_channel'] = 'true'
            #     if update_channel_pane:
            #         st.session_state['update_channel'] = 'true'
            # st.write(f"{st.session_state['add_channel']} - {st.session_state['update_channel']} - {st.session_state['delete_channel']}")
            # if st.session_state['add_channel'] == 'true':
            #     st.header("Add Channel")
            #     with st.form(key=f"addchannel"):
            #         input11 = st.text_input(label='channel_id')
            #         input22 = st.text_input(label='friendly_name')
            #         input33 = st.text_input(label='description')
            #         submit_button_add_channel = st.form_submit_button(label='Add Channel')
            #         if submit_button_add_channel:
            #             updated_channel = {}
            #             updated_channel['channel_id'] = input11
            #             updated_channel['friendly_name'] = input22
            #             updated_channel['description'] = input33
            #             updated_channel['fid'] = str(recorders_selected_id)
            #             result = create_channel(updated_channel)
            #             if result:
            #                 # st.write(f"{result.json()}")
            #                 st.success(f"Channel: {updated_channel['channel_id']} successfully created")
            #                 st.session_state['add_channel'] = "false"
            #                 st.session_state['delete_channel'] = "false"
            #                 st.session_state['update_channel'] = "false"
            #             else:
            #                 st.write(f"{result.json()}")
            #                 st.error(f"Channel: {updated_channel['channel_id']} not created")
            #                 st.session_state['add_channel'] = "false"
            #                 st.session_state['delete_channel'] = "false"
            #                 st.session_state['update_channel'] = "false"
            # elif st.session_state['update_channel'] == 'true':
            #     st.header("Update Channel")
            #     try:
            #         with st.form(key="updatechannel"):
            #             input1 = st.text_input(value=f"{channels_filtered_df['channel_id'].values[0]}", label='channel_id')
            #             input2 = st.text_input(value=f"{channels_filtered_df['friendly_name'].values[0]}", label='friendly_name')
            #             input3 = st.text_input(value=f"{channels_filtered_df['description'].values[0]}", label='description')
            #             input4 = st.text_input(value=f"{channels_filtered_df['fid'].values[0]}", label='fid')
            #             submit_button_update_channel = st.form_submit_button()

            #             if submit_button_update_channel:
            #                 updated_channel = {}
            #                 updated_channel['channel_id'] = input1
            #                 updated_channel['friendly_name'] = input2
            #                 updated_channel['description'] = input3
            #                 updated_channel['fid'] = input4
            #                 result = update_channel(channels_selected_id, updated_channel)
            #                 if result:
            #                     # st.write(f"{result.json()}")
            #                     # st.toast("Channel successfully updated")
            #                     st.success("Channel successfully updated")
            #                     st.session_state['add_channel'] = "false"
            #                     st.session_state['delete_channel'] = "false"
            #                     st.session_state['update_channel'] = "false"
            #                 else:
            #                     st.write(f"{result.json()}")
            #                     st.error("Channel not updated")
            #                     st.session_state['add_channel'] = "false"
            #                     st.session_state['delete_channel'] = "false"
            #                     st.session_state['update_channel'] = "false"
            #     except:
            #         st.warning("Please select a channel to update first")
            #         st.session_state['add_channel'] = "false"
            #         st.session_state['delete_channel'] = "false"
            #         st.session_state['update_channel'] = "false"
            # elif st.session_state['delete_channel'] == 'true':
            #     st.header("Delete Channel")
            #     try:
            #         result = delete_channel(channels_selected_id)
            #         if result:
            #             st.success(f"Channel ID:{channels_selected_id} successfully deleted")
            #             st.session_state['add_channel'] = "false"
            #             st.session_state['delete_channel'] = "false"
            #             st.session_state['update_channel'] = "false"
            #         else:
            #             if result.status_code == 422:
            #                 st.warning("Please select a channel to delete first")
            #                 st.session_state['add_channel'] = "false"
            #                 st.session_state['delete_channel'] = "false"
            #                 st.session_state['update_channel'] = "false"
            #             else:
            #                 st.write(f"{result.status_code} - {result.json()}")
            #                 st.error("Channel not deleted")
            #                 st.session_state['add_channel'] = "false"
            #                 st.session_state['delete_channel'] = "false"
            #                 st.session_state['update_channel'] = "false"
            #     except:
            #         st.write(channels_selected_id)
            #         st.warning("Please select a channel to delete first")
            #         st.session_state['add_channel'] = "false"
            #         st.session_state['delete_channel'] = "false"
            #         st.session_state['update_channel'] = "false"