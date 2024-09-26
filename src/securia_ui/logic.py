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

def fetch_users(token=None):
    response = requests.get(f"{config['api']['uri']}/user", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

def update_user(user_id, updated_user, token=None):
    # Send POST request to update user data
    response = requests.post(f"{config['api']['uri']}/user/{user_id}", json=updated_user, auth=BearerAuth(token))
    return response

def fetch_recorders(token=None):
    response = requests.get(f"{config['api']['uri']}/recorder", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

def fetch_channels(recorder_id, token=None):
    response = requests.get(f"{config['api']['uri']}/channels_by_recorder/{recorder_id}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None

def fetch_images_by_channel(channel_id, limit, sort, token=None):
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

def fetch_detections_by_channel(channel_id, limit, sort, token=None):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/detection/channel/{channel_id}?{urlencode(params)}", auth=BearerAuth(token))
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None