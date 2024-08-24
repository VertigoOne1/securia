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
import image_predict
import time, datetime, tempfile
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from eventbus import KafkaClientSingleton
from kafka.structs import TopicPartition
import s3

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

def fetch_image_key(id):
    logger.debug(f"Fetching key for {id}")
    try:
        url = f"{config['api']['uri']}/image/{id['image_id']}"
        resp = requests.get(url)
        data = resp.json()
        logger.debug(f"{data}")
        if resp.status_code == 200:
            if data["s3_path"] is None:
                logger.error("Did not receive an s3_path")
                logger.error(f"Response is {data}")
                return None
            else:
                image_key = data['s3_path'].split('/')
                logger.debug(f'Bucket is {image_key[0]}, key is {image_key[1]}')
                return image_key
        else:
            logger.error(f"status_code is not 200, it is {resp.status_code}")
            return None
    except:
        logger.error("API is in a mode that is not 'up', retry")
        return None

def fetch_image_s3(bucket, key):
    from PIL import Image
    s3_context = s3.create_s3_context(config['storage']['endpoint_hostname'],
                                      config['storage']['endpoint_method'],
                                      config['storage']['port'],
                                      config['storage']['access_key'],
                                      config['storage']['secret_access_key'])
    response = s3_context.get_object(
        Bucket=bucket,
        Key=key,
    )
    logger.debug(f"{response}")
    file_stream = response['Body']
    im = Image.open(file_stream)
    return im

# db_detection = models.Detection(fid=detection.fid,
#                                 detections=detection.detections,
#                                 processing_time_ms=detection.processing_time_ms,
#                                 detections_timestamp=detection.detections_timestamp
def predictions_process(predictions, image_id, processing_time, time_collected):
    if predictions is not None and image_id is not None:
        try:
            url = f"{config['api']['uri']}/detection"
            request_body = {'fid': image_id,
                            'detections': json.dumps(predictions),
                            'processing_time_ms': json.dumps(processing_time),
                            'detections_timestamp': time_collected
                            }
            logger.debug(f"Sending - {request_body}")
            resp = requests.post(url, json = request_body)
            data = resp.json()
            if resp.status_code == 200:
                logger.debug(f"detection post resp - {data}")
                return data['id']
            else:
                logger.error(f"Response: {resp.status_code} - {resp.json()}")
                return None
        except:
            logger.error("detection post request exception")
            logger.error(traceback.format_exc())
            return None
    else:
        logger.error("Did not receive a valid channel_id or uuid")
        return None

def process_images():
    if config['yolo']['write_local_file']:
        os.makedirs(config['yolo']['temp_output_folder'], exist_ok=True)
    while True:
        # Consume messages
        try:
            for message in kafka_client.consume_messages(f'{config["kafka"]["subscribe_topic_prefix"]}',
                                                            f'{config["kafka"]["consumer_group"]}',
                                                            config["kafka"]["auto_offset_reset"]):
                logger.debug("- Message loop start -")
                message_collected_time = datetime.datetime.now().strftime(config['yolo']['time_format'])
                if message is None:
                    continue
                if message is not None:
                    logger.debug(f"Received message from: {message.topic} partition: {message.partition} at offset: {message.offset}")
                    key = fetch_image_key(message.value)
                    if key is None:
                        logger.error("Could not successfully complete message processing, send to DLQ and sleep for 2 seconds")
                        logger.debug(f"Partition - {message.partition}")
                        logger.debug(f"Offset - {message.offset}")
                        topic = f'{config["kafka"]["dlq_topic_prefix"]}collect'
                        send_result = kafka_client.send_message(topic, "NA", message.value)
                        sleep(2)
                    else:
                        logger.debug(f"Retrieving image {key}")
                        image = fetch_image_s3(key[0], key[1])
                        predictions = image_predict.predict_image(image)
                        predict_id = predictions_process(predictions["image_summary"], message.value['image_id'], predictions["timings"], message_collected_time)
                        if predict_id is None:
                            logger.error("Could not commit predictions")
                            logger.error("Send to DLQ")
                            topic = f'{config["kafka"]["dlq_topic_prefix"]}commit'
                            send_result = kafka_client.send_message(topic, "NA", message.value)
                        else:
                            logger.info("Successfully committed predictions")
                        logger.info("Processed message, Predictions: {predictions} - notifying upstreams")
                        # topic = f'{config["kafka"]["produce_topic_prefix"]}image'
                        # output = {}
                        # output["image_id"] = status
                        # send_result = kafka_client.send_message(topic, "NA", output)
                        # if send_result:
                        #     logger.debug(f"Notify success - {output}")
                        # else:
                        #     logger.error(f"Could not send notice of successful processing to my topic {topic}")
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

def send_s3(image_dict):
    import base64
    logger.debug("Send to S3")
    s3_context = s3.create_s3_context(config['storage']['endpoint_hostname'],
                                      config['storage']['endpoint_method'],
                                      config['storage']['port'],
                                      config['storage']['access_key'],
                                      config['storage']['secret_access_key'])
    import uuid
    object_name = uuid.uuid4()
    logger.debug(f"Image key: {object_name}")
    image = base64.b64decode(image_dict['image_base64'])
    try:
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(image)
            fp.seek(0)
            s3_context.upload_fileobj(fp, config['storage']['bucket_name'], str(object_name))
            logger.debug(f"Sent to S3 - {config['storage']['bucket_name']}/{str(object_name)}")
            fp.close()
            return object_name
    except:
        logger.error("Sending to S3 crapped out")
        logger.error(traceback.format_exc())
        return None