from sqlalchemy.orm import Session
import models, schemas
from typing import Annotated, Optional
import logger, bcrypt
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

# Users

def create_initial_super_user(db: Session):
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
            initial_password = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(18))
            hashed_password = bcrypt.hashpw(initial_password.encode('utf-8'), salt)

            db_user = models.User(
                email="securia_admin@marnus.com",
                username="admin",
                role="super",
                password=hashed_password.decode('utf-8')  # Store the hash as a string
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"----- RECORD THE BELOW INFORMATION -----")
            logger.info(f"Created initial super user account")
            logger.info(f"Initial Superuser is: {db_user}")
            logger.info(f"Initial Password is : {initial_password}")
            logger.info(f"----- RECORD THE ABOVE INFORMATION -----")
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

def update_user(db: Session, id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == id).first()

    if db_user is None:
        logger.debug(f"User - {id} not found")
        return None  # or raise an exception if you prefer

    # Update the attributes
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_user)

    return db_user

def delete_user(db: Session, id: int):
    db_user = db.query(models.User).filter(models.User.id == id).first()
    if db_user is None:
        return None
    try:
        db.delete(db_user)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting User: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

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

# Recorders

def update_recorder(db: Session, id: int, recorder: schemas.RecorderUpdate):
    db_recorder = db.query(models.Recorder).filter(models.Recorder.id == id).first()

    if db_recorder is None:
        logger.debug(f"Recorder - {id} not found")
        return None

    # Update the attributes
    recorder_data = recorder.dict(exclude_unset=True)
    for key, value in recorder_data.items():
        setattr(db_recorder, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_recorder)

    return db_recorder

def delete_recorder(db: Session, id: int):
    db_recorder = db.query(models.Recorder).filter(models.Recorder.id == id).first()
    if db_recorder is None:
        return None
    try:
        db.delete(db_recorder)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting Recorder: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

# Channels

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
    db_channel = db.query(models.Channel).filter(models.Channel.id == id).first()

    if db_channel is None:
        logger.debug(f"Channel - {id} not found")
        return None

    # Update the attributes
    channel_data = channel.dict(exclude_unset=True)
    for key, value in channel_data.items():
        setattr(db_channel, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_channel)

    return db_channel

def delete_channel(db: Session, id: int):
    db_channel = db.query(models.Channel).filter(models.Channel.id == id).first()
    if db_channel is None:
        return None
    try:
        db.delete(db_channel)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting channel: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

# Images

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

def update_image(db: Session, id: int, image: schemas.ImageUpdate):
    # Query the existing channel by id
    db_image = db.query(models.Image).filter(models.Image.id == id).first()

    if db_image is None:
        logger.debug(f"Image - {id} not found")
        return None

    # Update the attributes
    image_data = image.dict(exclude_unset=True)
    for key, value in image_data.items():
        setattr(db_image, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_image)

    return db_image

def delete_image(db: Session, id: int):
    db_image = db.query(models.Image).filter(models.Image.id == id).first()
    if db_image is None:
        return None
    try:
        db.delete(db_image)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

# Detections

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

def update_detection(db: Session, id: int, detection: schemas.DetectionUpdate):
    db_det = db.query(models.Detection).filter(models.Detection.id == id).first()

    if db_det is None:
        logger.debug(f"detection - {id} not found")
        return None

    # Update the attributes
    det_data = detection.dict(exclude_unset=True)
    for key, value in det_data.items():
        setattr(db_det, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_det)

    return db_det

def delete_detection(db: Session, id: int):
    db_det = db.query(models.Detection).filter(models.Detection.id == id).first()
    if db_det is None:
        return None
    try:
        db.delete(db_det)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting detection: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

# Detection Objects

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

def update_detection_object(db: Session, id: int, detection_object: schemas.DetectionObjectUpdate):
    db_deto = db.query(models.DetectionObjects).filter(models.DetectionObjects.id == id).first()

    if db_deto is None:
        logger.debug(f"Detection object - {id} not found")
        return None

    # Update the attributes
    deto_data = detection_object.dict(exclude_unset=True)
    for key, value in deto_data.items():
        setattr(db_deto, key, value)

    # Commit the changes
    db.commit()

    # Refresh the object
    db.refresh(db_deto)

    return db_deto

def delete_detection_object(db: Session, id: int):
    db_deto = db.query(models.DetectionObjects).filter(models.DetectionObjects.id == id).first()
    if db_deto is None:
        return None
    try:
        db.delete(db_deto)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting detection object: {str(e)}")
        db.rollback()  # Rollback the transaction in case of error
        return None

# Add other CRUD operations as needed
