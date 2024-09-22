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

def load_images_as_bytes(directory):
    from pathlib import Path
    image_data = []
    # Ensure the directory path is absolute
    directory = Path(directory).resolve()
    # Loop through all files in the directory
    a = 0
    for filename in os.listdir(directory):
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            file_path = directory / filename
            # Read the file as binary data
            with open(file_path, 'rb') as file:
                byte_data = file.read()
            # Create a dictionary with file info and byte data
            image_info = {
                'filename': filename,
                'channel': a,
                'mime_type': 'image/jpeg',
                'byte_data': byte_data
            }
            image_data.append(image_info)
            a = a + 1
    return image_data

def capture_simulated_image(channel):
        directory_path = 'images'
        loaded_images = load_images_as_bytes(directory_path)
        snapshot_url = f"http://{config['collector']['recorder_fqdn']}/image_directory/{channel}/picture"
        logger.debug(f"Capturing - {snapshot_url}")
        try:
            timestamp = datetime.now().strftime(config['collector']['time_format'])
            image = loaded_images[channel]
            logger.debug(f"Filename: {image['filename']}, MIME Type: {image['mime_type']}, Size: {len(image['byte_data'])} bytes")
            content_hash = calculate_sha256(image['byte_data'])
            base64_image = base64.b64encode(image['byte_data']).decode('utf-8')
            image_data = {
                "collected_timestamp": f"{timestamp}",
                "recorder_uuid": f"{config['collector']['recorder_uuid']}",
                "uri": f"config['collector']['recorder_fqdn']",
                "friendly_name": f"{config['collector']['recorder_friendly_name']}",
                "content_type": f"image/jpeg",
                "content_length": f"{len(image['byte_data'])}",
                "channel": f"{channel}",
                "object_name": f"{config['collector']['image_filename_prefix']}_{timestamp}.json",
                "hash": f"{content_hash}",
                "image_base64": f"{base64_image}",
                "recorder_status_code":f"200",
                "status":f"simulator_ok"
            }
            if config['collector']['write_local_file']:
                output_file = os.path.join(f"{config['collector']['temp_output_folder']}", f"{config['collector']['image_filename_prefix']}_{channel}_{timestamp}.json")
                logger.debug(f"Writing - {output_file}")
                with open(output_file, "a") as json_file:
                    json.dump(image_data, json_file)
                    json_file.write('\n')  # Add newline for easier reading and appending

                logger.info(f"Image data saved for timestamp: {timestamp}")
            return image_data
        finally:
            time.sleep(config['collector']['channel_delay_time'])