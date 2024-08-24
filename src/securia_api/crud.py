from sqlalchemy.orm import Session
import models, schemas
import logger
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def create_recorder(db: Session,
                 recorder: schemas.RecorderCreate,
                 ):
    try:
        db_recorder = models.Recorder(uri=recorder.uri)
        logger.debug(f"New recorder URI - {recorder.uri}")
        logger.debug(f"{db_recorder}")
        db.add(db_recorder)
        db.commit()
        db.refresh(db_recorder)
        return db_recorder
    except:
        return None

def create_channel(db: Session,
                 channel: schemas.ChannelCreate,
                 ):
    db_channel = models.Channel(channel_id=channel.channel_id,
                                 fid=channel.fid)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def create_image(db: Session,
                 image: schemas.ImageCreate,
                 ):
    db_image = models.Image(fid=image.fid,
                            hash=image.hash,
                            s3_path=image.s3_path,
                            content_length=image.content_length,
                            content_type=image.content_type,
                            recorder_status_code=image.recorder_status_code,
                            collection_status=image.collection_status,
                            collected_timestamp=image.collected_timestamp
                            )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

def create_detection(db: Session,
                 detection: schemas.DetectionCreate,
                 ):
    db_detection = models.Detection(fid=detection.fid,
                                    detections=detection.detections,
                                    detections_count=detection.detections_count,
                                    processing_time_ms=detection.processing_time_ms,
                                    detections_timestamp=detection.detections_timestamp
                                    )
    try:
        db.add(db_detection)
        db.commit()
        db.refresh(db_detection)
        return db_detection
    except:
        return None

def create_detection_object(db: Session,
                 detectionobj: schemas.DetectionObjectCreate,
                 ):
    db_detectionobj = models.DetectionObjects(fid=detectionobj.fid,
                                                 detection_class=detectionobj.detection_class,
                                                 confidence=detectionobj.confidence,
                                                 xyxy=detectionobj.xyxy,
                                                 crop_s3_path=detectionobj.crop_s3_path
                                                 )
    try:
        db.add(db_detectionobj)
        db.commit()
        db.refresh(db_detectionobj)
        return db_detectionobj
    except:
        return None

# Add other CRUD operations as needed


# Message Format
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