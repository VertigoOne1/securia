#!/bin/python3

import requests, os, time, json, hashlib, base64, traceback
from envyaml import EnvYAML
from datetime import datetime
import logger
import s3, tempfile

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

def calculate_sha256(content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

def checkhash(image_dict):
    image = base64.b64decode(image_dict['image_base64'])
    image_hash = calculate_sha256(image)
    if image_hash == image_dict['hash']:
        logger.info(f"Image not manipulated")
        return True
    else:
        logger.info(f"IMAGE MANIPULATED!!!")
        return False

def send_s3(image_dict):
    logger.debug("Send to S3")
    s3_context = s3.create_s3_context(config['storage']['endpoint_hostname'],
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

def preprocess_image(message):
    try:
        image_dict = message
        logger.debug(f"Received data from {image_dict['uri']} | Channel: {image_dict['channel']} | Status: {image_dict['status'] or 'None'}")
        image_dict["preproc_ingest_time"] = datetime.now().strftime(config['preprocessor']['time_format'])
        if image_dict is None:
            logger.error("Message was not JSON parsible")
        else:
            logger.debug("Persisting to DSIT")
            if config['preprocessor']['write_local_file']:
                output_file = os.path.join(f"{config['preprocessor']['temp_output_folder']}",
                                        f"{config['preprocessor']['image_filename_prefix']}_{image_dict['channel']}_{image_dict['collected_timestamp']}.json")
                logger.debug(f"Writing - {output_file}")
                with open(output_file, "a") as json_file:
                    json.dump(message, json_file)
            if checkhash(image_dict):
                linking = {}
                # Submit to S3
                object_name = send_s3(image_dict)
                if object_name is not None:
                    logger.info(f"Sent to S3 - {config['storage']['bucket_name']}/{object_name}")
                    # Submit to API
                    # resolve recorder uri to id -> recorder_id
                    try:
                        url = f"{config['api']['uri']}/recorder/search"
                        request_body = {'uri': image_dict['uri']}
                        resp = requests.post(url, json = request_body)
                        data = resp.json()
                        logger.debug(f"Recorder search resp - {data}")
                        if resp.status_code == 404: ## Create it
                            logger.debug("Recorder not found, creating it")
                            url = f"{config['api']['uri']}/recorder"
                            request_body = {'uri': image_dict['uri']}
                            resp = requests.post(url, json = request_body)
                            data = resp.json()
                            logger.debug(f"Create Recorder Response - {data}")
                            logger.debug(f"Recorder ID is {data['id']}")
                            linking['recorder_id'] = data['id']
                        else:
                            linking['recorder_id'] = data['id']
                    except:
                        logger.error("recorder search request exception")
                        logger.error(traceback.format_exc())
                    logger.debug("Ingest Status:")
                    logger.debug(f"{linking}")
                    # resolve channel by name to channel_id for channels in recorder_id
                    try:
                        url = f"{config['api']['uri']}/channel/search"
                        request_body = {'fid': linking['recorder_id'], 'channel_id': image_dict['channel']}
                        resp = requests.post(url, json = request_body)
                        data = resp.json()
                        logger.debug(f"Channel search resp - {data}")
                        if resp.status_code == 404: ## Create it
                            logger.debug("Channel not found, creating it")
                            url = f"{config['api']['uri']}/channel"
                            request_body = {'fid': linking['recorder_id'], 'channel_id': image_dict['channel']}
                            logger.debug(f"Request Body - {request_body}")
                            resp = requests.post(url, json = request_body)
                            data = resp.json()
                            logger.debug(f"Create Channnel Response - {data}")
                            logger.debug(f"Channel ID is {data['id']}")
                            linking['channel_id'] = data['id']
                        else:
                            linking['channel_id'] = data['id']
                    except:
                        logger.error("channel search request exception")
                        logger.error(traceback.format_exc())
                    logger.debug("Ingest Status:")
                    logger.debug(f"{linking}")
                    # insert image -> image_id -> channel_id
                    try:
                        url = f"{config['api']['uri']}/image"
                        request_body = {'fid': linking['channel_id'],
                                        'hash': image_dict['hash'],
                                        's3_path': f"{config['storage']['bucket_name']}/{object_name}",
                                        'content_length': image_dict['content_length'],
                                        'content_type': image_dict['content_type'],
                                        'recorder_status_code': f"{image_dict.get('recorder_status_code') or None}",
                                        'collected_timestamp': image_dict['collected_timestamp'],
                                        'collection_status': f"{image_dict.get('status') or None}",
                                        'ingest_timestamp': image_dict['preproc_ingest_time']
                                        }
                        logger.debug(f"Sending - {request_body}")
                        resp = requests.post(url, json = request_body)
                        data = resp.json()
                        logger.debug(f"Image post resp - {data}")
                    except:
                        logger.error("image post request exception")
                        logger.error(traceback.format_exc())
                    logger.debug("Ingest Status:")
                    logger.debug(f"{linking}")
                else:
                    logger.error("Object submission to S3 conked out")
                    return False
            else:
                logger.error("IMAGE MANIPULATION DETECTED")
                exit(1)
            logger.info(f"Image data saved for image received at timestamp: {image_dict['collected_timestamp']}")
    except KeyboardInterrupt:
        logger.info("Quitting")
        return None
    return True