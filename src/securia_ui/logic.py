#!/usr/bin/env python3

# This is the main loop and functions to check internal cluster certs
# Sites are SSL checked, and the result of the analysis, sent to a prometheus exporter

from curses.ascii import isdigit
import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import requests
from time import sleep
from pprint import pformat
import urllib3
from time import sleep
from functools import wraps
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

class TokenManager:
    def __init__(self, config):
        self.config = config
        self.token = None
        self.expiry_time = 0

    def get_token(self):
        import time
        if self.token is None or time.time() > self.expiry_time:
            self._fetch_new_token()
        return self.token

    def _fetch_new_token(self):
        import time
        data = {
            "grant_type": "password",
            "username": self.config['api']['username'],
            "password": self.config['api']['password'],
            "scope": "api",
            "client_id": "client_id",
            "client_secret": "client_secret"
        }
        try:
            response = requests.post(f"{self.config['api']['uri']}/token", data=data)
            response.raise_for_status()
            token_response = response.json()
            self.token = token_response["access_token"]
            # Assuming the token expires in 3600 seconds (1 hour)
            self.expiry_time = time.time() + token_response.get("expires_in", 3600) - 300  # Refresh 5 minutes before expiry
        except requests.RequestException as e:
            logger.error(f"An error occurred while fetching token: {e}")
            self.token = None
            self.expiry_time = 0

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token_manager):
        self.token_manager = token_manager

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token_manager.get_token()}"
        return r

def with_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'auth' not in kwargs:
            kwargs['auth'] = BearerAuth(token_manager)
        return func(*args, **kwargs)
    return wrapper

# Initialize the TokenManager
token_manager = TokenManager(config)

@with_auth
def fetch_recorders(auth=None):
    response = requests.get(f"{config['api']['uri']}/recorder", auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch data: {response.status_code}")
        return None

@with_auth
def fetch_channels(recorder_id, auth=None):
    response = requests.get(f"{config['api']['uri']}/channels_by_recorder/{recorder_id}", auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None

@with_auth
def fetch_images_by_channel(channel_id, limit, sort, auth=None):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/image/channel/{channel_id}?{urlencode(params)}", auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None

@with_auth
def fetch_detections_by_channel(channel_id, limit, sort, auth=None):
    from urllib.parse import urlencode
    params = {
            "sort_by": 'id',
            "sort_order": sort,
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/detection/channel/{channel_id}?{urlencode(params)}", auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch details: {response.status_code}")
        return None