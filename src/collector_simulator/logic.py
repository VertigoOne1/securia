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
import simulator_collector
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

def simulated_collection():
    while True:
        os.makedirs(config['collector']['temp_output_folder'], exist_ok=True)
        logger.debug(f"Collecting the following channels {config['collector']['channels']}")
        for channel in config['collector']['channels']:
            logger.debug(f"Collecting channel : {channel}")
            image_dict = simulator_collector.capture_simulated_image(channel)
            if image_dict is not None:
                logger.debug(f"Received - Channel - {image_dict['channel'] or None} | Size - {image_dict['content_length'] or None} | StatusCode - {image_dict['recorder_status_code'] or None}")
                if image_dict['content_length'] == "ok":
                    metrics.p_image_collect_success.labels(config['collector']['camera_fqdn'],channel).inc()
                else:
                    metrics.p_image_collect_fail.labels(config['collector']['camera_fqdn'],channel).inc()
                partition_key=f"{config['collector']['camera_fqdn']}.{channel}"
                topic = f'{config["kafka"]["produce_topic_prefix"]}{partition_key}'
                send_result = kafka_client.send_message(topic, partition_key, image_dict)
                if send_result:
                    logger.debug(f"send success - {topic} - {partition_key}")
                    metrics.p_image_transmit_success.labels(config['collector']['camera_fqdn'],channel).inc()
                else:
                    logger.debug(f"send failure - {topic} - {partition_key}")
                    metrics.p_image_transmit_fail.labels(config['collector']['camera_fqdn'],channel).inc()
            else:
                metrics.p_image_collect_fail.labels(config['collector']['camera_fqdn'],channel).inc()
                logger.error(f"No image received, this is functionally impossible")
        time.sleep(config['collector']['capture_interval'])