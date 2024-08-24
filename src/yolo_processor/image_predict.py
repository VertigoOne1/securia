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
    results = model.predict(source=image, save=False, imgsz=(704,576), augment=True)
    logger.debug("Predict complete")
    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug(f'created temporary directory - {tmpdirname}')
        if config['yolo']['save_predict_output']:
            results[0].save(filename="result.jpg")
        if config['yolo']['save_predict_crops']:
            results[0].save_crop(tmpdirname)
        boxes = results[0].boxes  # Boxes object for bounding box outputs
        masks = results[0].masks  # Masks object for segmentation masks outputs
        image_summary = results[0].summary()
        timings = results[0].speed
        logger.debug(f'Prediction Summary - {image_summary}')
        logger.debug(f'Prediction Speeds - {timings}')
        predictions = {}
        predictions["image_summary"] = image_summary
        predictions["timings"] = timings
        return predictions

    # for result in results:
    #     # result.save_crop("crops")
    #     # logger.debug(result.summary())
    #     boxes = result.boxes  # Boxes object for bounding box outputs
    #     masks = result.masks  # Masks object for segmentation masks outputs
    #     keypoints = result.keypoints  # Keypoints object for pose outputs
    #     probs = result.probs  # Probs object for classification outputs
    #     obb = result.obb  # Oriented boxes object for OBB outputs
    #     # result.show()  # display to screen
    #     result.save(filename="result.jpg")  # save to disk
    # logger.debug("Boxes")
    # for box in boxes:
    #     logger.debug(box.xyxy)
    # for r in results:
    #     logger.debug(r.boxes)  # print the Boxes object containing the detection bounding boxes

    # # from ndarray
    # im2 = cv2.imread("bus.jpg")
    # results = model.predict(source=im2, save=True, save_txt=True)  # save predictions as labels

    # from list of PIL/ndarray
    # results = model.predict(source=[im1, im2])

# def preprocess_image(image_dict):
#     try:
#         logger.debug(f"Received data from {image_dict['uri']} | Channel: {image_dict['channel']} | Status: {image_dict['status'] or 'None'}")
#         image_dict["preproc_ingest_time"] = datetime.now().strftime(config['preprocessor']['time_format'])
#         if image_dict is None:
#             logger.error("Message was not JSON parsible")
#         else:
#             logger.debug("Persisting to DSIT")
#             if config['preprocessor']['write_local_file']:
#                 output_file = os.path.join(f"{config['preprocessor']['temp_output_folder']}",
#                                         f"{config['preprocessor']['image_filename_prefix']}_{image_dict['channel']}_{image_dict['collected_timestamp']}.json")
#                 logger.debug(f"Writing - {output_file}")
#                 with open(output_file, "a") as json_file:
#                     json.dump(image_dict, json_file)
#             if checkhash(image_dict):
#                 linking = {}
#                 # Submit to S3
#                 object_name = send_s3(image_dict)
#                 if object_name is not None:
#                     logger.info(f"Sent to S3 - {config['storage']['bucket_name']}/{object_name}")
#                     # Submit to API
#                     # resolve recorder uri to id -> recorder_id
#                     linking['recorder_id'] = recorder_process(image_dict)
#                     # resolve channel id via recorder id and channel name
#                     linking['channel_id'] = channel_process(image_dict, linking['recorder_id'])
#                     # insert image via channel_id
#                     linking['image_id'] = image_process(image_dict, linking['channel_id'], object_name)
#                     if linking['image_id'] is not None:
#                         logger.debug("Processes completed successfully")
#                         return linking['image_id']
#                     else:
#                         logger.error("Processes did not complete successfully")
#                         return None
#                 else:
#                     logger.error("Object submission to S3 failed")
#                     return None
#             else:
#                 logger.error("IMAGE MANIPULATION DETECTED")
#                 return None
#     except KeyboardInterrupt:
#         logger.info("Quitting")
#         return None
#     except:
#         logger.error("bad packet")
#         logger.debug(f"{image_dict}")