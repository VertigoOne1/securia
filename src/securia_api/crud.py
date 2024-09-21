from sqlalchemy.orm import Session
import models, schemas
from typing import Annotated, Optional
import logger, bcrypt
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def create_initial_user(db: Session):
    import string, random
    try:
        # Check if we already have an admin user
        user = get_user_by_username(db, "admin")
        if user is not None:
            logger.debug("Admin user already exists, skipping create")
            return user
        else:
            # Need an initial user, generate a salt and hash the password
            salt = bcrypt.gensalt()
            initial_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(18))
            hashed_password = bcrypt.hashpw(initial_password.encode('utf-8'), salt)

            db_user = models.User(
                email="securia_admin@marnus.com",
                username="admin",
                role="super",
                password=hashed_password.decode('utf-8')  # Store the hash as a string
            )

            logger.debug(f"{db_user}")

            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"Initial Password is : {initial_password}")
            logger.debug("Created initial admin account")
            return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

def create_user(db: Session, user: schemas.UserCreate):
    try:
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt)

        db_user = models.User(
            email=user.email,
            username=user.username,
            role=user.role,
            password=hashed_password.decode('utf-8')  # Store the hash as a string
        )

        logger.debug(f"New User - {user.email}")
        logger.debug(f"{db_user}")

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

def get_user_by_username(db: Session, username: str) -> Optional[schemas.User]:
    logger.debug("Fetching user from model.User")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is not None:
        return schemas.User.from_orm(user)
    else:
        logger.debug(f"User not found - {username}")
    return None

def get_user_by_email(db: Session, email):
    users = db.query(models.User).filter(models.User.email == email).first()
    if users is not None:
        return [schemas.Recorder.from_orm(user) for user in users]
    return None

def verify_user_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

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

def update_recorder(db: Session, id: int, recorder: schemas.RecorderUpdate):
    # Query the existing channel by id
    db_recorder = db.query(models.Recorder).filter(models.Recorder.id == id).first()

    if db_recorder is None:
        return None  # or raise an exception if you prefer

    # Update the attributes
    recorder_data = recorder.dict(exclude_unset=True)
    for key, value in recorder_data.items():
        setattr(db_recorder, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
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

def update_channel(db: Session, id: int, channel: schemas.ChannelUpdate):
    # Query the existing channel by id
    db_channel = db.query(models.Channel).filter(models.Channel.id == id).first()

    if db_channel is None:
        return None  # or raise an exception if you prefer

    # Update the attributes
    channel_data = channel.dict(exclude_unset=True)
    for key, value in channel_data.items():
        setattr(db_channel, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
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
                            recorder_status_data=image.recorder_status_data,
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
                                                 detection_name=detectionobj.detection_name,
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