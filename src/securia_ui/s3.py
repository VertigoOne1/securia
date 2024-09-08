from envyaml import EnvYAML
import boto3
import os
from botocore.client import Config

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

from envyaml import EnvYAML
import boto3
import os
from botocore.client import Config

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def create_s3_context(endpoint_url, method, port, access_key, access_secret_key):
    config = Config(
        s3={'addressing_style': 'path'},
        signature_version='s3v4',
    retries = {
      'max_attempts': 20,
      'mode': 'standard'
   }
    )

    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=f'{method}://{endpoint_url}:{port}',
        aws_access_key_id=f'{access_key}',
        aws_secret_access_key=f'{access_secret_key}',
        config=config,
        use_ssl=False
    )
    return s3_client

# TODO - If the image does not exist?
# TODO - convert everything to PNG
def fetch_image(bucket, key):
    from PIL import Image
    s3_context = create_s3_context(config['storage']['endpoint_hostname'],
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