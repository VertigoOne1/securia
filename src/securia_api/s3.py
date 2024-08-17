from envyaml import EnvYAML
import boto3
import os
from botocore.client import Config

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def upload_file(file_path, bucket_name, object_name, endpoint_url, port):
    # Create a custom configuration
    config = Config(
        s3={'addressing_style': 'path'},
        signature_version='s3v4',
    )

    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=f'http://{endpoint_url}:{port}',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy',
        config=config,
        use_ssl=False
    )

    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"File {file_path} uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")