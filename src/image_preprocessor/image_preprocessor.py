#!/bin/python3

import requests, os, time, json, hashlib, base64, traceback
from envyaml import EnvYAML
from datetime import datetime
import logger
import s3, tempfile

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

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
    try:
        s3_context = s3.create_s3_context(config['storage']['endpoint_hostname'],
                                        config['storage']['endpoint_method'],
                                        config['storage']['port'],
                                        config['storage']['access_key'],
                                        config['storage']['secret_access_key'])
    except:
        logger.error("Issue creating s3 context")
        logger.error(traceback.format_exc())
        return None
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

def fetch_recorder_by_uuid(uuid, limit=1, token=None):
    from urllib.parse import urlencode
    params = {
            "limit": limit,
            "skip": 0
        }
    response = requests.get(f"{config['api']['uri']}/recorder/uuid/{uuid}?{urlencode(params)}", auth=BearerAuth(token))
    if response.status_code >= 200:
        return response
    else:
        logger.error(f"Failed to fetch anything from API")
        return None

def recorder_process(token, image_dict):
    try:
        if image_dict['recorder_uuid'] is None:
            logger.info("No recorder UUID present, skipping")
            return None
        resp = fetch_recorder_by_uuid(image_dict['recorder_uuid'], auth=BearerAuth(token))
        if resp is not None:
            if resp.status_code == 404: ## Create it
                logger.debug("Recorder not found, creating it")
                url = f"{config['api']['uri']}/recorder"
                request_body = {
                    'uri': image_dict['uri'],
                    'uuid': image_dict['recorder_uuid'],
                    'friendly_name': f"{image_dict.get('friendly_name') or None}",
                    'owner': f"{image_dict.get('owner') or None}",
                    'type': f"{image_dict.get('type') or None}",
                    'location': f"{image_dict.get('location') or None}",
                    'contact': f"{image_dict.get('contact') or None}",
                    }
                resp = requests.post(url, json = request_body, auth=BearerAuth(token))
                data = resp.json()
                logger.debug(f"Create Recorder Response - {data}")
                logger.debug(f"Recorder ID is {data['id']}")
                return data['id']
            elif resp.status_code == 200:
                data = resp.json()
                logger.debug(f"Recorder ID is {data['id']}")
                return data['id']
            else:
                logger.error(f"Response status: {resp.status_code} - {resp.json()}")
                return None
        else:
            logger.error(f"No response status (None)")
            return None
    except:
        logger.error("recorder search/insert request exception")
        logger.error(traceback.format_exc())
        return None

def channel_process(token, image_dict, recorder_id):
    if recorder_id is not None:
        try:
            url = f"{config['api']['uri']}/channel/search/"
            request_body = {'fid': recorder_id, 'channel_id': image_dict['channel']}
            logger.debug(f"Finding channel and recorder - {request_body}")
            resp = requests.post(url, json = request_body, auth=BearerAuth(token))
            data = resp.json()
            logger.debug(f"Channel search resp - {data}")
            if resp.status_code == 404: ## Create it
                logger.debug("Channel not found, creating it")
                url = f"{config['api']['uri']}/channel"
                request_body = {
                    'fid': recorder_id,
                    'channel_id': image_dict['channel'],
                    'friendly_name': f"{image_dict.get('friendly_name') or None}",
                    'description': f"{image_dict.get('description') or None}"
                    }
                logger.debug(f"Request Body - {request_body}")
                resp = requests.post(url, json = request_body, auth=BearerAuth(token))
                data = resp.json()
                logger.debug(f"Create Channnel Response - {data}")
                logger.debug(f"Channel ID is {data['id']}")
            elif resp.status_code == 200:
                return data['id']
            else:
                logger.error(f"Respose status: {resp.status_code}")
                return None
        except:
            logger.error("channel search request exception")
            logger.error(traceback.format_exc())
            return None
    else:
        logger.error("Did not receive a valid recorder_id")
        return None

def image_process(token, image_dict, channel_id, object_name):
    if channel_id is not None and object_name is not None:
        try:
            url = f"{config['api']['uri']}/image"
            request_body = {'fid': channel_id,
                            'hash': image_dict['hash'],
                            's3_path': f"{config['storage']['bucket_name']}/{object_name}",
                            'content_length': image_dict['content_length'],
                            'content_type': image_dict['content_type'],
                            'recorder_status_code': f"{image_dict.get('recorder_status_code') or None}",
                            'recorder_status_data': f"{image_dict.get('recorder_status_data') or None}",
                            'collected_timestamp': image_dict['collected_timestamp'],
                            'collection_status': f"{image_dict.get('status') or None}",
                            'ingest_timestamp': image_dict['preproc_ingest_time']
                            }
            logger.debug(f"Sending - {request_body}")
            resp = requests.post(url, json = request_body, auth=BearerAuth(token))
            data = resp.json()
            if resp.status_code == 200:
                logger.debug(f"Image post resp - {data}")
                return data['id']
            else:
                logger.error(f"Respose status: {resp.status_code}")
                return None
        except:
            logger.error("image post request exception")
            logger.error(traceback.format_exc())
            return None
    else:
        logger.error("Did not receive a valid channel_id or uuid")
        return None

def preprocess_image(token, image_dict):
    try:
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
                    json.dump(image_dict, json_file)
            logger.debug(f"Recorder Status Code : {image_dict['recorder_status_code']}")
            if image_dict["recorder_status_code"] != "200":
                logger.debug("Collector failed to retrieve image, skipping S3 portion, registering NO_IMAGE event")
                linking = {}
                linking['recorder_id'] = recorder_process(token, image_dict)
                if linking['recorder_id'] is None:
                    logger.info("No recorder_id received, cannot do anything")
                    return None
                linking['channel_id'] = channel_process(token, image_dict, linking['recorder_id'])
                linking['image_id'] = image_process(token, image_dict, linking['channel_id'], "NO_IMAGE")
                if linking['image_id'] is not None:
                    logger.debug("Processes completed successfully")
                    return linking['image_id']
                else:
                    logger.error("Processes did not complete successfully")
                    return None
            else:
                if checkhash(image_dict):
                    linking = {}
                    # Submit to S3
                    object_name = send_s3(image_dict)
                    if object_name is not None:
                        logger.info(f"Sent to S3 - {config['storage']['bucket_name']}/{object_name}")
                        # Submit to API
                        # resolve recorder uri to id -> recorder_id
                        linking['recorder_id'] = recorder_process(token, image_dict)
                        # resolve channel id via recorder id and channel name
                        linking['channel_id'] = channel_process(token, image_dict, linking['recorder_id'])
                        # insert image via channel_id
                        linking['image_id'] = image_process(token, image_dict, linking['channel_id'], object_name)
                        if linking['image_id'] is not None:
                            logger.debug("Processes completed successfully")
                            return linking['image_id']
                        else:
                            logger.error("Processes did not complete successfully")
                            return None
                    else:
                        logger.error("Object submission to S3 failed")
                        return None
                else:
                    logger.error("IMAGE MANIPULATION DETECTED")
                    return None
    except KeyboardInterrupt:
        logger.info("Quitting")
        return None
    except:
        logger.error("bad packet")
        logger.debug(f"{image_dict}")