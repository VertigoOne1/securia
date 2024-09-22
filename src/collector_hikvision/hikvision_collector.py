#!/bin/python3

import requests, os, time, json, hashlib, base64, traceback
from envyaml import EnvYAML
from datetime import datetime
from requests.auth import HTTPDigestAuth
import logger

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

def calculate_sha256(content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

def capture_hikvision_image(channel):
        snapshot_url = f"http://{config['collector']['recorder_fqdn']}/ISAPI/Streaming/channels/{channel}/picture"
        logger.debug(f"Capturing - {snapshot_url}")
        try:
            response = requests.get(snapshot_url, auth=HTTPDigestAuth(config['collector']['recorder_username'], config['collector']['recorder_username']), timeout=config['collector']['collection_timeout'])
            timestamp = datetime.now().strftime(config['collector']['time_format'])
            if response.status_code == 200:
                logger.debug(f"Headers - {response.headers}")
                logger.debug(f"Cookies - {response.cookies}")
                logger.debug(f"Encoding - {response.encoding}")
                content_hash = calculate_sha256(response.content)
                base64_image = base64.b64encode(response.content).decode('utf-8')
                image_data = {
                    "collected_timestamp": f"{timestamp}",
                    "recorder_uuid": f"{config['collector']['recorder_uuid']}",
                    "uri": f"{config['collector']['recorder_fqdn']}",
                    "friendly_name": f"{config['collector']['recorder_friendly_name']}",
                    "content_type": f"{response.headers.get('Content-Type', None)}",
                    "content_length": f"{response.headers.get('Content-Length', None)}",
                    "channel": f"{channel}",
                    "object_name": f"{config['collector']['image_filename_prefix']}_{timestamp}.json",
                    "hash": f"{content_hash}",
                    "image_base64": f"{base64_image}",
                    "recorder_status_code":f"{response.status_code or None}",
                    "status":f"ok"
                }
                if config['collector']['write_local_file']:
                    output_file = os.path.join(f"{config['collector']['temp_output_folder']}", f"{config['collector']['image_filename_prefix']}_{channel}_{timestamp}.json")
                    logger.debug(f"Writing - {output_file}")
                    with open(output_file, "a") as json_file:
                        json.dump(image_data, json_file)
                        json_file.write('\n')  # Add newline for easier reading and appending

                    logger.info(f"Image data saved for timestamp: {timestamp}")
                return image_data
            else:
                logger.error(f"Failed to capture image. Status code: {response.status_code}")
                image_data = {
                    "collected_timestamp": f"{timestamp}",
                    "recorder_uuid": f"{config['collector']['recorder_uuid']}",
                    "uri": f"{config['collector']['recorder_fqdn']}",
                    "friendly_name": f"{config['collector']['recorder_friendly_name']}",
                    "content_type": f"{response.headers.get('Content-Type', None)}",
                    "content_length": f"{response.headers.get('Content-Length', None)}",
                    "hash": f"{None}",
                    "channel": f"{channel}",
                    "recorder_status_code":f"{response.status_code or None}",
                    "recorder_status_data":f"{response.text or None}",
                    "status":f"recorder_error_response"
                }
                logger.debug(f"Returning: {image_data}")
                return image_data
        except requests.RequestException as e:
            logger.error(f"Request Exception - Error capturing image: {e}")
            image_data = {
                "collected_timestamp": f"{timestamp}",
                "recorder_uuid": f"{config['collector']['recorder_uuid']}",
                "uri": f"{config['collector']['recorder_fqdn']}",
                "friendly_name": f"{config['collector']['recorder_friendly_name']}",
                "content_type": f"{response.headers.get('Content-Type', None)}",
                "content_length": f"{response.headers.get('Content-Length', None)}",
                "channel": f"{channel}",
                "recorder_status_code":f"{response.status_code or None}",
                "recorder_status_data":f"{response.text or None}",
                "status":f"recorder_request_exception"
            }
            return image_data
        except:
            logger.error(f"General Exception")
            logger.error(traceback.format_exc())
            image_data = {
                "collected_timestamp": f"{timestamp}",
                "recorder_uuid": f"{config['collector']['recorder_uuid']}",
                "uri": f"{config['collector']['recorder_fqdn']}",
                "friendly_name": f"{config['collector']['recorder_friendly_name']}",
                "content_type": f"{response.headers.get('Content-Type', None)}",
                "content_length": f"{response.headers.get('Content-Length', None)}",
                "channel": f"{channel}",
                "recorder_status_code":f"{response.status_code or None}",
                "recorder_status_data":f"{response.text or None}",
                "status":f"general_exception"
            }
            return image_data
        finally:
            time.sleep(config['collector']['channel_delay_time'])