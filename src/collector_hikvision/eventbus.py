#!/bin/python3

import sys, logging
import json
from kafka import KafkaProducer, KafkaConsumer
import os, logger, traceback
from pprint import pformat
from time import sleep
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

class KafkaProducerSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if KafkaProducerSingleton._instance is None:
            KafkaProducerSingleton()
        return KafkaProducerSingleton._instance

    def __init__(self):
        if KafkaProducerSingleton._instance is not None:
            raise Exception("This class is a singleton. Use get_instance() method to get the instance.")
        else:
            params = {
              'bootstrap_servers': config['kafka']['broker_url'],
              'security_protocol': config['kafka']['security_protocol'],
              'sasl_mechanism': config['kafka']['sasl_mechanism'],
              'sasl_plain_username': config['kafka']['sasl_plain_username'],
              'sasl_plain_password': config['kafka']['sasl_plain_password'],
              }

            self.producer = KafkaProducer(**params, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

            KafkaProducerSingleton._instance = self

    def send_message(self, input_topic, key, message):
        try:
          topic = f'{config["kafka"]["topic_prefix"]}-{input_topic}'
          logger.debug(f"Producing to - {topic}")
          keyb = key.encode('utf-8') if isinstance(key, str) else key
          self.producer.send(topic, key=keyb, value=message)
          self.producer.flush()
          return True
        except:
            logger.error(f"Kafka send exception")
            logger.error(traceback.format_exc())
            return False