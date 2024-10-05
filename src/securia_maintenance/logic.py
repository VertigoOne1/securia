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
import time
import logger, requests, jwt, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token, refresh_token_func):
        """
        token: The initial token value.
        refresh_token_func: A function to refresh the token.
        """
        self.token = token
        self.payload = jwt.decode(token, options={"verify_signature": False})
        self.expires_at: int = self.payload.get("exp")
        self.refresh_token_func = refresh_token_func  # Function to refresh token

    def is_token_expired(self):
        # Check if the token is about to expire within the next 5 minutes (300 seconds)
        return time.time() > self.expires_at - 300

    def refresh_token(self):
        # Call the refresh token function and update the token and expiration
        new_token = self.refresh_token_func()
        self.token = new_token
        self.payload = jwt.decode(new_token, options={"verify_signature": False})
        self.expires_at = self.payload.get("exp")

    def __call__(self, r):
        # Check if the token is expired or near expiry
        if self.is_token_expired():
            logger.info("Token is about to expire, refreshing token...")
            self.refresh_token()

        r.headers["authorization"] = "Bearer " + self.token
        return r

def login():
    username = config['api']['username']
    password = config['api']['password']
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "api",
        "client_id": "client_id",
        "client_secret": "client_secret"
    }
    try:
        response = requests.post(f"{config['api']['uri']}/token", data=data)

        if response.status_code == 200:
            # Successful login
            token = response.json().get("access_token")
            return token
        else:
            logger.error("Invalid username or password. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"requests - An error occurred: {e}")

auth = BearerAuth(token=login(), refresh_token_func=login())

def data_pruning_maintenance():
    logger.info("Running data pruning maintenance")
    response = requests.delete(f"{config['api']['uri']}/data_maintenance/recursive/days/{config['maintenance']['prune_data_older_than_days']}", auth=auth)
    if response.status_code == 200:
        logger.info("Pruned data")
        return response.json()
    elif response.status_code == 404:
        logger.info(f"No data to prune: {response.status_code}")
        return response
    else:
        logger.error(f"Expected response {response}")
        return None

def image_pruning_maintenance():
    logger.info("Running image pruning maintenance")
    response = requests.delete(f"{config['api']['uri']}/image/recursive/days/{config['maintenance']['prune_images_older_than_days']}", auth=auth)
    if response.status_code == 200:
        logger.info("Pruned data")
        return response.json()
    elif response.status_code == 404:
        logger.info(f"No images to prune: {response.status_code}")
        return response
    else:
        logger.error(f"Expected response {response}")
        return None
