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

if __name__ == '__main__':
    apiserver = startApiServer()
    logger.info(f"Start - {config['general']['app_name']}")
    # scheduling = start_schedules()
    logic.predict()
    # logic.collect_raw_images()