#!/bin/python3

import sys, logging
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.structs import TopicPartition
from kafka.errors import KafkaError
import os, logger, traceback
from pprint import pformat
from time import sleep
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

logger = logging.getLogger('kafka')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

logger = logging.getLogger('kafka')

class KafkaClientSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if KafkaClientSingleton._instance is None:
            KafkaClientSingleton()
        return KafkaClientSingleton._instance

    def __init__(self):
        if KafkaClientSingleton._instance is not None:
            raise Exception("This class is a singleton. Use get_instance() method to get the instance.")
        else:
            self.params = {
                'bootstrap_servers': config['kafka']['broker_url'],
                'security_protocol': config['kafka']['security_protocol'],
                'sasl_mechanism': config['kafka']['sasl_mechanism'],
                'sasl_plain_username': config['kafka']['sasl_plain_username'],
                'sasl_plain_password': config['kafka']['sasl_plain_password'],
                'reconnect_backoff_ms': 1000,
                'metadata_max_age_ms': 30000 # detect new topics faster
            }

            self.producer = KafkaProducer(**self.params, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
            self.consumer = None  # Will be initialized when needed

            KafkaClientSingleton._instance = self

    def consume_messages(self, topic_pattern, group_id, auto_offset_reset='earliest'):
        try:
            if self.consumer is None:
                self.consumer = KafkaConsumer(
                    **self.params,
                    group_id=group_id,
                    auto_offset_reset=auto_offset_reset,
                    enable_auto_commit=config["kafka"]["enable_auto_commit"],
                    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
                )
            self.consumer.subscribe(topics=(),pattern=f"^{topic_pattern}.*")
            logger.debug(f"Consuming from - {self.consumer.subscription()}")
            for message in self.consumer:
                yield message

        except KafkaError as e:
            logger.error(f"Kafka consume exception: {str(e)}")
            logger.error(traceback.format_exc())
            yield None
        except:
            logger.error(f"Likely configuration error")
            logger.error(traceback.format_exc())
            exit(1)

    def send_message(self, topic, key, message):
        try:
            logger.debug(f"Producing to - {topic}")
            keyb = key.encode('utf-8') if isinstance(key, str) else key
            self.producer.send(topic, key=keyb, value=message)
            self.producer.flush()
            return True
        except KafkaError as e:
            logger.error(f"Kafka send exception: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        except:
            logger.error(f"Likely configuration error")
            logger.error(traceback.format_exc())
            exit(1)

    def commit_offset(self, topic_partition, offset):
        logger.debug(f"Commiting - {topic_partition} - {offset}")
        if self.consumer:
            self.consumer.commit({topic_partition: offset})
            logger.debug(f"Committed offset {offset} for partition {topic_partition}")
        else:
            logger.warning("Consumer not initialized. Cannot commit offset.")

    def close(self):
        logger.debug("Received close signal")
        if self.consumer:
            self.consumer.close()
        logger.debug("Closed consumer")
        if self.producer:
            self.producer.close(timeout=5)
        logger.debug("Closed Producer")
        return None
