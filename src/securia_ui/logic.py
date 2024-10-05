from envyaml import EnvYAML
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

## User Management

def fetch_users(token=None):
    response = requests.get(f"{config['api']['uri']}/user", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

def fetch_logged_in_user(username, token=None):
    response = requests.get(f"{config['api']['uri']}/user/username/{username}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

def create_user(updated_user, token=None):
    logger.debug(f"Creating user - {updated_user}")
    response = requests.post(f"{config['api']['uri']}/user", json=updated_user, auth=BearerAuth(token))
    return response

def update_user(user_id, updated_user, token=None):
    response = requests.post(f"{config['api']['uri']}/user/{user_id}", json=updated_user, auth=BearerAuth(token))
    return response

def delete_user(user_id, token=None):
    response = requests.delete(f"{config['api']['uri']}/user/{user_id}", auth=BearerAuth(token))
    return response

## Recorder Management

def fetch_recorders(token=None):
    response = requests.get(f"{config['api']['uri']}/recorder", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

def create_recorder(updated_recorder, token=None):
    logger.debug(f"Creating recorder - {updated_recorder}")
    response = requests.post(f"{config['api']['uri']}/recorder", json=updated_recorder, auth=BearerAuth(token))
    return response

def update_recorder(recorder_id, updated_recorder, token=None):
    response = requests.post(f"{config['api']['uri']}/recorder/{recorder_id}", json=updated_recorder, auth=BearerAuth(token))
    return response

def delete_recorder(recorder_id, token=None):
    response = requests.delete(f"{config['api']['uri']}/recorder/{recorder_id}", auth=BearerAuth(token))
    return response

## Channel Management

def fetch_channels(recorder_id, token=None):
    response = requests.get(f"{config['api']['uri']}/channels_by_recorder/{recorder_id}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None

def create_channel(updated_data, token=None):
    logger.debug(f"Creating channel - {updated_data}")
    response = requests.post(f"{config['api']['uri']}/channel", json=updated_data, auth=BearerAuth(token))
    return response

def update_channel(id, updated_data, token=None):
    response = requests.post(f"{config['api']['uri']}/channel/{id}", json=updated_data, auth=BearerAuth(token))
    return response

def delete_channel(id, token=None):
    response = requests.delete(f"{config['api']['uri']}/channel/{id}", auth=BearerAuth(token))
    return response


## Images Management

def fetch_images(channel_id, limit=100, sort="desc", token=None):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/image/channel/{channel_id}?{urlencode(params)}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None

## Detections

def fetch_detections(image_id, limit=100, sort="desc", token=None):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/detection/image/{image_id}?{urlencode(params)}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None