#!/usr/bin/env python3

# This is the main loop and functions to check internal cluster certs
# Sites are SSL checked, and the result of the analysis, sent to a prometheus exporter

from curses.ascii import isdigit
import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import json, requests, socket
from time import sleep
import os, fnmatch, traceback
from pprint import pformat
import urllib3
from time import sleep
import image_preprocessor as image_preprocessor
import time, datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from eventbus import KafkaClientSingleton

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

kafka_client = KafkaClientSingleton.get_instance()

def collect_raw_images():
    if config['preprocessor']['write_local_file']:
        os.makedirs(config['preprocessor']['temp_output_folder'], exist_ok=True)
    while True:
        # Consume messages
        try:
            for message in kafka_client.consume_messages(f'{config["kafka"]["topic_prefix"]}', f'{config["kafka"]["consumer_group"]}',config["kafka"]["auto_offset_reset"]):
                if message is not None:
                    status = image_preprocessor.preprocess_image(message)
                    if status == None:
                        kafka_client.close()
                        exit(130)
                else:
                    logger.debug("Message was None, closing channel")
                    kafka_client.close()
                    break  # Exit if there was an error
        except KeyboardInterrupt:
            logger.info("Quitting")
            kafka_client.close()
            exit(130)