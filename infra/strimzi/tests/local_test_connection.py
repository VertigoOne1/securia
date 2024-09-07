#!/bin/python3

import sys, logging
import json
from kafka import KafkaProducer, KafkaConsumer
import os
from pprint import pformat
from time import sleep
from envyaml import EnvYAML
config = EnvYAML('local_config_secrets.yaml')

BROKER_URL = config["kafka_broker_url"]

logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

params = {
  'bootstrap_servers': BROKER_URL,
  'security_protocol': 'SASL_PLAINTEXT',
  'sasl_mechanism': 'SCRAM-SHA-512',
  'sasl_plain_username': config["sasl_plain_username"],
  'sasl_plain_password': config["sasl_plain_password"],
}

producer = KafkaProducer(**params, value_serializer=lambda x:json.dumps(x).encode('utf-8'))

def emit(topic, msg):
    print(pformat(msg))
    producer.send(topic,value=msg)
    producer.flush()

a = 0
while True:
    a = a + 1
    msg = '{"TEST": "' + f"{a}" + '"}'
    emit("marnus.test_source_topic",msg)
    sleep(1)