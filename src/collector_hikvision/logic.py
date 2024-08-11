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
import hikvision_collector
import time, datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from eventbus import KafkaProducerSingleton

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

producer = KafkaProducerSingleton.get_instance()

def hikvision_collection():
    while True:
        os.makedirs(config['collector']['temp_output_folder'], exist_ok=True)
        for channel in config['collector']['channels']:
            image_dict = hikvision_collector.capture_hikvision_image(channel)
            if image_dict is not None:
                logger.debug(f"Received - Channel - {image_dict['channel']} | Size - {image_dict['content_length']}")
                metrics.p_image_collect_success.labels(config['collector']['camera_fqdn'],channel).inc()
                partition_key=f"{config['collector']['camera_fqdn']}-{channel}"
                topic = partition_key
                send_result = producer.send_message(topic, partition_key, image_dict)
                if send_result:
                    logger.debug(f"send success - {partition_key}")
                    metrics.p_image_transmit_success.labels(config['collector']['camera_fqdn'],channel).inc()
                else:
                    logger.debug(f"send failure - {partition_key}")
                    metrics.p_image_transmit_fail.labels(config['collector']['camera_fqdn'],channel).inc()
            else:
                metrics.p_image_collect_fail.labels(config['collector']['camera_fqdn'],channel).inc()
                logger.error(f"No image received")
        time.sleep(config['collector']['capture_interval'])