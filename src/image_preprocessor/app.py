#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
from time import sleep
from pprint import pformat
from apicontroller import FlaskThread
import requests, time, jwt

import logger, logic

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

def startApiServer():
    server = FlaskThread()
    server.daemon = True
    server.start()

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

if __name__ == '__main__':
    apiserver = startApiServer()
    logger.info(f"Start - {config['general']['app_name']}")
    logic.collect_raw_images()