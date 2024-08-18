#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
from time import sleep
from pprint import pformat
from scheduler import start_schedules
from apicontroller import start_api_server

import logger, models
# from database import get_db, engine

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if __name__ == '__main__':
    logger.info(f"Start - {config['general']['app_name']}")
    scheduling = start_schedules()
    apiserver = start_api_server()