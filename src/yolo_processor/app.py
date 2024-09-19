#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import json, requests, socket
from time import sleep
import os, fnmatch, traceback
from pprint import pformat
from apicontroller import FlaskThread
from scheduler import start_schedules

import logger, logic

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

def startApiServer():
    server = FlaskThread()
    server.daemon = True
    server.start()

def get_token():

    data = {
        "grant_type": "password",
        "username": f"{config['api']['username']}",
        "password": f"{config['api']['password']}",
        "scope": "api",
        "client_id": "client_id",
        "client_secret": "client_secret"
    }

    try:
        response = requests.post(f"{config['api']['uri']}/token", data=data)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':
    apiserver = startApiServer()
    logger.info(f"Start - {config['general']['app_name']}")
    # logic.predict()
    token = None
    token_response = get_token()
    token = token_response["access_token"]
    if token is not None:
        logger.debug(f"Token received: {token_response}")
        logger.info(f"API Auth OK")
        logic.process_images(token)
    else:
        logger.error(f"API Auth ERR")
        exit(1)