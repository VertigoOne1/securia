from sqlalchemy.orm import Session
from sqlalchemy import inspect
import models, schemas
from typing import Annotated, Optional
import logger, bcrypt
from envyaml import EnvYAML

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

# Users

def create_system_users(db: Session):
    try:
        for system_user in config['system_users']:
            # Check if we already have an admin user
            user = get_user_by_username(db, system_user['username'])
            if user is not None:
                logger.debug(f"{system_user['username']} already exists, skipping create")
            else:
                # Need an initial user, generate a salt and hash the password
                salt = bcrypt.gensalt()
                initial_password = system_user['password']
                hashed_password = bcrypt.hashpw(initial_password.encode('utf-8'), salt)

                db_user = models.User(
                    email=f"{system_user['username']}@marnus.com",
                    username=system_user['username'],
                    role=system_user['role'],
                    password=hashed_password.decode('utf-8')  # Store the hash as a string
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                logger.info(f"----- RECORD THE BELOW INFORMATION -----")
                logger.info(f"Created initial system user")
                logger.info(f"Initial user is: {db_user.username}")
                logger.info(f"Initial password is : {initial_password}")
                logger.info(f"----- RECORD THE ABOVE INFORMATION -----")
    except Exception as e:
        logger.error(f"Error creating system users: {str(e)}")
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
    logger.debug(f"Finding user: {username} from db")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is not None:
        logger.debug("User Found")
        return schemas.User.from_orm(user)
    else:
        logger.debug(f"User not found - {username}")
    return None

def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
    logger.debug("Finding user by email: {email} from db")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is not None:
        logger.debug("User Found")
        return schemas.User.from_orm(user)
    else:
        logger.debug(f"User not found - {email}")
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

# Recorders

def create_recorder(db: Session,
                 recorder: schemas.RecorderCreate,
                 ):
    try:
        recorder_data = recorder.dict()
        recorder_columns = inspect(models.Recorder).columns.keys()
        filtered_data = {k: v for k, v in recorder_data.items() if k in recorder_columns}
        db_recorder = models.Recorder(**filtered_data)
        logger.debug(f"New recorder UUID - {recorder.recorder_uuid}")
        db.add(db_recorder)
        db.commit()
        db.refresh(db_recorder)
        return db_recorder
    except Exception as e:
        logger.error(f"Error creating recorder: {e}")
        db.rollback()
        return None

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
    try:
        channel_data = channel.dict()
        channel_columns = inspect(models.Channel).columns.keys()
        filtered_data = {k: v for k, v in channel_data.items() if k in channel_columns}
        db_channel = models.Channel(**filtered_data)
        db.add(db_channel)
        db.commit()
        db.refresh(db_channel)
        return db_channel
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        db.rollback()
        return None

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
    try:
        image_data = image.dict()
        image_columns = inspect(models.Image).columns.keys()
        filtered_data = {k: v for k, v in image_data.items() if k in image_columns}
        db_image = models.Image(**filtered_data)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
    except Exception as e:
        logger.error(f"Error creating image: {e}")
        db.rollback()
        return None

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

    try:
        detection_data = detection.dict()
        detection_columns = inspect(models.Detection).columns.keys()
        filtered_data = {k: v for k, v in detection_data.items() if k in detection_columns}
        db_detection = models.Detection(**filtered_data)
        db.add(db_detection)
        db.commit()
        db.refresh(db_detection)
        return db_detection
    except Exception as e:
        logger.error(f"Error creating detection: {e}")
        db.rollback()
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
    try:
        detection_object_data = detectionobj.dict()
        detection_object_columns = inspect(models.DetectionObject).columns.keys()
        filtered_data = {k: v for k, v in detection_object_data.items() if k in detection_object_columns}
        db_detectionobj = models.DetectionObject(**filtered_data)
        db.add(db_detectionobj)
        db.commit()
        db.refresh(db_detectionobj)
        return db_detectionobj
    except:
        return None

def update_detection_object(db: Session, id: int, detection_object: schemas.DetectionObjectUpdate):
    db_deto = db.query(models.DetectionObject).filter(models.DetectionObject.id == id).first()

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
    db_deto = db.query(models.DetectionObject).filter(models.DetectionObject.id == id).first()
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
