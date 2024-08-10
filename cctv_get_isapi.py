#!/bin/python3

import requests
import time
from datetime import datetime
import os
from requests.auth import HTTPDigestAuth

# Camera settings
CAMERA_IP = "10.0.0.61"
USERNAME = "view"
PASSWORD = "asdf1234"

# Image capture settings
CAPTURE_INTERVAL = 5  # seconds
OUTPUT_FOLDER = "pics_http"

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ISAPI URL for snapshot
snapshot_url = f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/picture"

def capture_image():
    try:
        response = requests.get(snapshot_url, auth=HTTPDigestAuth(USERNAME, PASSWORD), timeout=10)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_FOLDER, f"image_{timestamp}.jpg")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Image saved: {filename}")
        else:
            print(f"Failed to capture image. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error capturing image: {e}")

def main():
    print("Starting image capture. Press Ctrl+C to stop.")
    try:
        while True:
            capture_image()
            time.sleep(CAPTURE_INTERVAL)
    except KeyboardInterrupt:
        print("Image capture stopped.")

if __name__ == "__main__":
    main()