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
from kafka.structs import TopicPartition

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

kafka_client = KafkaClientSingleton.get_instance()

def collect_raw_images():
    if config['preprocessor']['write_local_file']:
        os.makedirs(config['preprocessor']['temp_output_folder'], exist_ok=True)
    while True:
        # Consume messages
        try:
            for message in kafka_client.consume_messages(f'{config["kafka"]["subscribe_topic_prefix"]}',
                                                            f'{config["kafka"]["consumer_group"]}',
                                                            config["kafka"]["auto_offset_reset"]):
                logger.debug("- Message loop start -")
                if message is None:
                    continue
                if message is not None:
                    logger.debug(f"Received message from: {message.topic} partition: {message.partition} at offset: {message.offset}")
                    logger.debug(f"Message: {message}")
                    status = image_preprocessor.preprocess_image(message.value)
                    if status is None:
                        logger.error("Could not successfully complete message processing, send to DLQ and sleep for 2 seconds")
                        logger.debug(f"Partition - {message.partition}")
                        logger.debug(f"Offset - {message.offset}")
                        topic = f'{config["kafka"]["dlq_topic_prefix"]}process'
                        send_result = kafka_client.send_message(topic, "NA", message.value)
                    else:
                        logger.info("Processed message, ID: {status} - notifying upstreams")
                        topic = f'{config["kafka"]["produce_topic_prefix"]}image'
                        output = {}
                        output["image_id"] = status
                        send_result = kafka_client.send_message(topic, "NA", output)
                        if send_result:
                            logger.debug(f"Notify success - {output}")
                        else:
                            logger.error(f"Could not send notice of successful processing to my topic {topic}")
                else:
                    logger.debug("Message was None, closing channel")
                    kafka_client.close()
                    break  # Exit if there was an error
                logger.debug("- Message loop end -")
        except KeyboardInterrupt:
            logger.info("Quitting by request of user")
            kafka_client.close()
            exit(130)
        except:
            logger.info("Exception")
            kafka_client.close()
            logger.error(traceback.format_exc())
            exit(1)