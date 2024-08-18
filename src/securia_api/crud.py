from sqlalchemy.orm import Session
import models, schemas
import logger
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def create_post(db: Session, post: schemas.CreatePost):
    db_post = models.Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()

def create_recorder(db: Session,
                 recorder: schemas.RecorderCreate,
                 ):
    db_recorder = models.Recorder(uri=recorder.uri)
    logger.debug(f"New recorder URI - {recorder.uri}")
    logger.debug(f"{db_recorder}")
    db.add(db_recorder)
    db.commit()
    db.refresh(db_recorder)
    return db_recorder

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
                 image_id
                 ):
    db_detection = models.Detection(fid=image_id, detections=detection.detections)
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

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