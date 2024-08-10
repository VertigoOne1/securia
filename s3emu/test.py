#!/bin/python3

import boto3
import os
from botocore.client import Config

def upload_file(file_path, bucket_name, object_name, endpoint_hostname, port, access_key, secret_access_key):
    # Create a custom configuration
    config = Config(
        s3={'addressing_style': 'path'},
        signature_version='s3v4',
    )

    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=f'http://{endpoint_hostname}:{port}',
        aws_access_key_id=f'{access_key}',
        aws_secret_access_key=f'{secret_access_key}',
        config=config,
        use_ssl=False
    )
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"File {file_path} uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")

if __name__ == "__main__":
    file_path = 'testfile.txt'
    bucket_name = 'test'
    object_name = 'testfile.txt'
    endpoint_hostname = 'localhost'  # Change this to your emulated S3 endpoint
    port = 32650  # Change this to the port your emulated S3 is running on
    access_key = 'AKIAIOSFODNN7EXAMPLE'
    secret_access_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

    upload_file(file_path, bucket_name, object_name, endpoint_hostname, port, access_key, secret_access_key)