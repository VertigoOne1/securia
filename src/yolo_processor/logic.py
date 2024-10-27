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
from app import BearerAuth, login

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

auth = BearerAuth(token=login(), refresh_token_func=login)

def login():
    username = config['api']['username']
    password = config['api']['password']
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "api",
        "client_id": "client_id",
        "client_secret": "client_secret"
    }
    try:
        response = requests.post(f"{config['api']['uri']}/token", data=data)

        if response.status_code == 200:
            # Successful login
            token = response.json().get("access_token")
            return token
        else:
            logger.error("Invalid username or password. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"requests - An error occurred: {e}")

kafka_client = KafkaClientSingleton.get_instance()

def fetch_image_key(id):
    logger.debug(f"Fetching key for {id}")
    try:
        url = f"{config['api']['uri']}/image/{id['image_id']}"
        resp = requests.get(url, auth=auth)
        data = resp.json()
        logger.debug(f"{data}")
        if resp.status_code == 200:
            if data["s3_path"] is None:
                logger.error("Did not receive an s3_path")
                logger.error(f"Response is {data}")
                return None
            elif "NO_IMAGE" in data["s3_path"]:
                logger.error("Image not available")
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

def predictions_process(predictions, image_id, processing_time, time_collected, detections_count):
    if predictions is not None and image_id is not None:
        try:
            url = f"{config['api']['uri']}/detection"
            request_body = {'fid': image_id,
                            'detections': json.dumps(predictions),
                            'detections_count': detections_count,
                            'processing_time_ms': json.dumps(processing_time),
                            'detections_timestamp': time_collected
                            }
            logger.debug(f"Sending - {request_body}")
            resp = requests.post(url, json = request_body, auth=auth)
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
        logger.error("Did not receive a valid image_id or predictions")
        return None

def detections_process(detections_dict, detections_id):
    if detections_dict is not None and detections_id is not None:
        detection_ids = []
        for detection in detections_dict:
            try:
                url = f"{config['api']['uri']}/detection_object"
                request_body = {'fid': detections_id,
                                'detection_class': str(detection["class"]),
                                'detection_name': detection["name"],
                                'confidence': detection["confidence"],
                                'xyxy': json.dumps(detection["box"]),
                                'crop_s3_path': "NOT_IMPLEMENTED_YET"
                                }
                logger.debug(f"Sending - {request_body}")
                resp = requests.post(url, json = request_body, auth=auth)
                data = resp.json()
                if resp.status_code == 200:
                    logger.debug(f"detection objects post resp - {data}")
                    detection_ids.append(data['id'])
                else:
                    logger.error(f"Response: {resp.status_code} - {resp.json()}")
                    return None
            except:
                logger.error("detection objects post request exception")
                logger.error(traceback.format_exc())
                return None
        if detection_ids is not None:
            logger.debug(f"Processed all detection ids - {detection_ids}")
            return detection_ids
    else:
        logger.error("Did not receive a valid detection_id or detection_dict")
        return None

async def process_images():
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
                        logger.debug("Key is NONE")
                        logger.error("Could not successfully complete message processing, send to DLQ")
                        logger.debug(f"Partition - {message.partition}")
                        logger.debug(f"Offset - {message.offset}")
                        topic = f'{config["kafka"]["dlq_topic_prefix"]}collect'
                        send_result = kafka_client.send_message(topic, "NA", message.value)
                    else:
                        logger.debug("Retrieved image info from API")
                        logger.debug(f"Retrieving image for {key}")
                        image = fetch_image_s3(key[0], key[1])
                        predictions = image_predict.predict_image(image)
                        predict_id = predictions_process(predictions["image_summary"], message.value['image_id'], predictions["timings"], message_collected_time, predictions["detections_count"])
                        if predict_id is None:
                            logger.error("Could not commit predictions summary")
                            logger.error("Send to DLQ")
                            topic = f'{config["kafka"]["dlq_topic_prefix"]}commit'
                            send_result = kafka_client.send_message(topic, "NA", message.value)
                        else:
                            detection_id = detections_process(predictions["image_summary"], predict_id)
                            if detection_id is None:
                                logger.error("Could not commit prediction objects")
                                logger.error("Send to DLQ")
                                topic = f'{config["kafka"]["dlq_topic_prefix"]}commit'
                                send_result = kafka_client.send_message(topic, "NA", message.value)
                            else:
                                logger.info("Successfully committed detection objects")
                        logger.info(f"Processed message, Predictions Count: {predictions['detections_count']} - notifying upstreams")
                        # kafka_client.commit_offset(TopicPartition(message.topic, message.partition), message.offset + 1)
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