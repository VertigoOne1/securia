#!/usr/bin/env python3
from envyaml import EnvYAML
from time import sleep
from pprint import pformat
from scheduler import start_schedules
from apicontroller import start_api_server

import logger, logic

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

if __name__ == '__main__':
    logger.info(f"Start - {config['general']['app_name']}")
    continuous_thread, stop_run_continuously = start_schedules()
    apiserver = start_api_server()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if stop_run_continuously:
            stop_run_continuously.set()
            continuous_thread.join()