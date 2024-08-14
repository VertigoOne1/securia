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


                # image_data = {
                #     "collected_timestamp": f"{timestamp}",
                #     "uri": f"{snapshot_url}",
                #     "content_type": f"{response.headers.get('Content-Type', None)}",
                #     "content_length": f"{response.headers.get('Content-Length', None)}",
                #     "channel": f"{channel}",
                #     "object_name": f"{config['collector']['image_filename_prefix']}_{timestamp}.json",
                #     "hash": f"{content_hash}",
                #     "image_base64": f"{base64_image}",
                #     "recorder_status_code":f"{response.status_code or None}",
                #     "status":f"ok"
                # }

def preprocess_image(message):
    try:
        image_dict = message
        logger.debug(f"Received data from {image_dict['uri']} | Channel: {image_dict['channel']} | Status: {image_dict['status']}")
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
                    json_file.write('\n')  # Add newline for easier reading and appending

            logger.info(f"Image data saved for image received at timestamp: {image_dict['collected_timestamp']}")
    except KeyboardInterrupt:
        logger.info("Quitting")
        return None
    return True
        # 
        # for channel in config['collector']['channels']:
        #     image_dict = image_preprocessor.capture_hikvision_image(channel)
        #     if image_dict is not None:
        #         logger.debug(f"Received - Channel - {image_dict['channel'] or None} | Size - {image_dict['content_length'] or None} | StatusCode - {image_dict['recorder_status_code'] or None}")
        #         if image_dict['content_length'] == "ok":
        #             metrics.p_image_collect_success.labels(config['collector']['camera_fqdn'],channel).inc()
        #         else:
        #             metrics.p_image_collect_fail.labels(config['collector']['camera_fqdn'],channel).inc()
        #         partition_key=f"{config['collector']['camera_fqdn']}-{channel}"
        #         topic = partition_key
        #         send_result = kafka_client.send_message(topic, partition_key, image_dict)
        #         if send_result:
        #             logger.debug(f"send success - {partition_key}")
        #             metrics.p_image_transmit_success.labels(config['collector']['camera_fqdn'],channel).inc()
        #         else:
        #             logger.debug(f"send failure - {partition_key}")
        #             metrics.p_image_transmit_fail.labels(config['collector']['camera_fqdn'],channel).inc()
        #     else:
        #         metrics.p_image_collect_fail.labels(config['collector']['camera_fqdn'],channel).inc()
        #         logger.error(f"No image received, this is functionally impossible")
        # time.sleep(config['collector']['capture_interval'])