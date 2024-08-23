#!/bin/python3

import requests, os, time, json, hashlib, base64, traceback
from envyaml import EnvYAML
from datetime import datetime
import logger
import s3, tempfile

logger = logger.setup_custom_logger(__name__)
config = EnvYAML('config.yml')

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
    s3_context = s3.create_s3_context(config['storage']['endpoint_hostname'],
                                      config['storage']['endpoint_method'],
                                      config['storage']['port'],
                                      config['storage']['access_key'],
                                      config['storage']['secret_access_key'])
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

def predict_image():
    # import cv2
    from PIL import Image

    from ultralytics import YOLO

    model = YOLO("yolov8l.pt")
    # # accepts all formats - image/dir/Path/URL/video/PIL/ndarray. 0 for webcam
    # results = model.predict(source="0")
    # results = model.predict(source="folder", show=True)  # Display preds. Accepts all YOLO predict arguments
    # from PIL
    im1 = Image.open("image2.jpg")
    results = model.predict(source=im1, save=True, imgsz=(1920,1088), augment=True)
    logger.debug("Predict complete")
    results[0].save_crop("crops")
    summary = results[0].summary()
    logger.debug(json.dumps(summary))
    
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

def predict_process(image_dict, channel_id, object_name):
    if channel_id is not None and object_name is not None:
        try:
            url = f"{config['api']['uri']}/image"
            request_body = {'fid': channel_id,
                            'hash': image_dict['hash'],
                            's3_path': f"{config['storage']['bucket_name']}/{object_name}",
                            'content_length': image_dict['content_length'],
                            'content_type': image_dict['content_type'],
                            'recorder_status_code': f"{image_dict.get('recorder_status_code') or None}",
                            'collected_timestamp': image_dict['collected_timestamp'],
                            'collection_status': f"{image_dict.get('status') or None}",
                            'ingest_timestamp': image_dict['preproc_ingest_time']
                            }
            logger.debug(f"Sending - {request_body}")
            resp = requests.post(url, json = request_body)
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

# def check_api_available(): # Stupid Idea
#     logger.info("Check if API service is available")
#     try:
#         url = f"{config['api']['uri']}/status"
#         resp = requests.get(url)
#         data = resp.json()
#         if resp.status_code == 200:
#             logger.debug("200 OK at least")
#             if data["status"] != "up":
#                 logger.error("API is in a mode that is not 'up', retry")
#                 logger.error(f"Response is {data}")
#                 return False
#             else:
#                 logger.debug("API available - continuing in 2 seconds")
#                 return True
#         else:
#             logger.error("status_code is not 200, retry")
#             return False
#     except:
#         logger.error("API is in a mode that is not 'up', retry")
#         return False

def preprocess_image(image_dict):
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
            if checkhash(image_dict):
                linking = {}
                # Submit to S3
                object_name = send_s3(image_dict)
                if object_name is not None:
                    logger.info(f"Sent to S3 - {config['storage']['bucket_name']}/{object_name}")
                    # Submit to API
                    # resolve recorder uri to id -> recorder_id
                    linking['recorder_id'] = recorder_process(image_dict)
                    # resolve channel id via recorder id and channel name
                    linking['channel_id'] = channel_process(image_dict, linking['recorder_id'])
                    # insert image via channel_id
                    linking['image_id'] = image_process(image_dict, linking['channel_id'], object_name)
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