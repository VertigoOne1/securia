#!/usr/bin/env python3

import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
from time import sleep
from pprint import pformat
import scheduler
from apicontroller import start_api_server

import logger
# from database import get_db, engine

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if __name__ == '__main__':
    logger.info(f"Start - {config['general']['app_name']}")
    continuous_thread, stop_run_continuously = scheduler.start_schedules()
    try:
        while True:
            apiserver = start_api_server()
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if stop_run_continuously:
            stop_run_continuously.set()
            continuous_thread.join()