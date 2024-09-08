#!/bin/python3

import requests, os, time, json, hashlib, base64, traceback
from envyaml import EnvYAML
from datetime import datetime
import logger
import tempfile

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

def predict_image(image):
    from ultralytics import YOLO
    model = YOLO(config['yolo']['model'])
    results = model.predict(source=image, save=False, imgsz=(704,576), augment=config['yolo']['augment'])
    logger.debug("Predict complete")
    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug(f'created temporary directory - {tmpdirname}')
        if config['yolo']['save_predict_output']:
            results[0].save(filename="result.jpg")
        if config['yolo']['save_predict_crops']:
            results[0].save_crop(tmpdirname)
        # boxes = results[0].boxes  # Boxes object for bounding box outputs
        # logger.debug(f"BOXES: {boxes}")
        # masks = results[0].masks  # Masks object for segmentation masks outputs
        # logger.debug(f"MASKS: {boxes}")
        # logger.debug(f"Names: {results[0].names}") # Prints all class names
        image_summary = results[0].summary()
        timings = results[0].speed
        predictions = {}
        predictions["image_summary"] = image_summary
        predictions["timings"] = timings
        predictions["detections_count"] = len(image_summary)
        # predictions["detections_dict"] = detections_dict
        logger.debug(f"{predictions}")
        return predictions