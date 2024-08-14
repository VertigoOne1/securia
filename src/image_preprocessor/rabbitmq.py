#!/usr/bin/env python3

# This is the main loop and functions to check internal cluster certs
# Sites are SSL checked, and the result of the analysis, sent to a prometheus exporter

from curses.ascii import isdigit
import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import json, requests, socket
from time import sleep
import kubernetes
import os, fnmatch, traceback
from pprint import pformat
import urllib3
from time import sleep
import time, datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

# rabbitmq_url = https://host:15672
def collect_large_queues(rabbitmq_url, username, password, queue_size_limit):
    # RabbitMQ API endpoint
    rabbitmq_api_url = f"{rabbitmq_url}/api/queues"

    # RabbitMQ username and password
    rabbitmq_username = username
    rabbitmq_password = password
    logger.debug(f"{rabbitmq_api_url}")
    # Fetch queue information from RabbitMQ API
    try:
        response = requests.get(rabbitmq_api_url, auth=(rabbitmq_username, rabbitmq_password), verify=False)
    except:
        logger.error(traceback.format_exc())
        logger.error(f"Error fetching information from rabbit: {response.status_code} - {response.text}")
        response = ()
        response.status = 500

    # Check if the request was successful
    if response.status_code == 200:
        queues = json.loads(response.text)
        logger.debug(f"{queues}")

        # Filter queues with ready messages > queue_size_limit
        try:
            queues_with_high_ready = [queue for queue in queues if queue["messages_ready"] > queue_size_limit]
        except:
            logger.error(traceback.format_exc())
            logger.error(f"Error fetching queue information: {response.status_code} - {response.text}")
            error_json = {}
            error_json["error"] = response.text
            return error_json
        # Print the list of queues with high ready messages
        if queues_with_high_ready:
            logger.debug(f"Queues with ready messages higher than {queue_size_limit}:")
            for queue in queues_with_high_ready:
                logger.info(f"- {queue['name']} (Ready messages: {queue['messages_ready']})")
                return queues_with_high_ready
        else:
            logger.info(f"No queues found with ready messages higher than {queue_size_limit}.")
            return {}
    else:
        logger.error(f"Error fetching queue information: {response.status_code} - {response.text}")
        error_json = {}
        error_json["error"] = response.text
        return error_json

def purge_queue(rabbitmq_url, username, password, vhost, queue_name):
    """Purge all messages from a specified queue."""
    encoded_vhost = requests.utils.quote(vhost, safe='')
    url = f"{rabbitmq_url}/api/queues/{encoded_vhost}/{queue_name}/contents"
    logger.debug(f"{rabbitmq_url}")
    response = requests.delete(url, auth=(username, password), verify=False)
    if response.status_code == 204:
        logger.info(f"Successfully purged queue: {queue_name}")
        return True
    else:
        logger.error(f"Error purging queue {queue_name}: {response.status_code} - {response.text}")
        return False