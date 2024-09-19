import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Path, responses, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import desc
from enum import Enum
from typing import Annotated
from prometheus_client import make_asgi_app
from envyaml import EnvYAML
from logger import setup_custom_logger
from starlette import status
import s3, tempfile

import logger, logic, models, schemas, crud
from database import engine, SessionLocal


logger = setup_custom_logger(__name__)

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Secret key for signing JWT tokens
SECRET_KEY = config["api"]["secret_key"]

# Algorithm used for JWT token encoding
ALGORITHM = "HS256"

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer flow for token retrieval
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API users ( to be moved to psql)
api_users_db = {
    f"{config['api']['username']}": {
        "username": f"{config['api']['username']}",
        "password": f"{config['api']['password']}",
    }
}

# Authentication function
def authenticate_user(username: str, password: str):
    user = api_users_db.get(username)
    if not user or not pwd_context.verify(password, user["password"]):
        return False
    return user

# Token generation function
def create_access_token(data: dict):
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency for extracting and verifying JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = {"username": username}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return token_data

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

logger.error("Creating schemas")
models.Base.metadata.create_all(bind=engine)

def start_api_server():
    models.Base.metadata.create_all(bind=engine)
    uvconfig = uvicorn.Config(app, host="0.0.0.0", port=config['api']['default_port'], log_level=config['api']['debug_level'])
    server = uvicorn.Server(uvconfig)
    server.run()

@app.get("/")
def root():
    return {"message": "SecurIA"}

# Implement the token endpoint for token generation
@app.post("/securia/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token_data = {"sub": user["username"]}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Implement a protected endpoint that requires authentication using JWT tokens
@app.get("/securia/token_test")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"{current_user['username']} authenticated."}

@app.get("/securia/status")
def status():
    if config['api']['maintenance_mode']:
        return {"status": "maintenance"}
    else:
        return {"status": "up"}

@app.post("/post")
async def create_post(db: db_dependency, post: schemas.CreatePost):
    logger.debug(f"{post.content}")
    # logger.debug(f"{dump}")
    new_post = schemas.CreatePost(title="My New Post", content="This is the content")
    db_post = crud.create_post(db, new_post)
    if db_post is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created new post with id: {db_post.id}")

    post = crud.get_post(db, db_post.id)
    return post

# Recorder APIs

@app.post("/securia/recorder")
async def create_recorder(db: db_dependency, recorder: schemas.RecorderCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_recorder = crud.create_recorder(db, recorder)
    if db_recorder is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created new recorder with id: {db_recorder.id}")
    return db_recorder

@app.post("/securia/recorder/search")
async def search_recorder(db: db_dependency, recorder: schemas.RecorderCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    recorder = db.query(models.Recorder).filter(models.Recorder.uri == recorder.uri).first()
    if recorder is not None:
        logger.debug(f"Found recorder uri - {recorder.uri} : {recorder.id}")
        return recorder
    if recorder is None:
        logger.debug(f"Recorder not found")
        raise HTTPException(status_code=404, detail='Recorder not found')
    raise HTTPException(status_code=509, detail='CRUD issue')

@app.get("/securia/recorder", response_model=list[schemas.Recorder])
async def get_recorder_by_id(db: db_dependency, skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    recorders = db.query(models.Recorder).offset(skip).limit(limit).all()
    if recorders is not None:
        return [schemas.Recorder.from_orm(recorder) for recorder in recorders]
    if recorders is None:
        raise HTTPException(status_code=404, detail='Recorders not found')
    raise HTTPException(status_code=500, detail='CRUD issue')

@app.get("/securia/recorder/{recorder_id}")
async def get_recorder_by_id(db: db_dependency, recorder_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    recorder = db.query(models.Recorder).filter(models.Recorder.id == recorder_id).first()
    if recorder is not None:
        return recorder
    if recorder is None:
        raise HTTPException(status_code=404, detail='Recorder not found')
    raise HTTPException(status_code=500, detail='CRUD issue')

# Channel APIs

@app.post("/securia/channel")
async def create_channel(db: db_dependency, channel: schemas.ChannelCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_channel = crud.create_channel(db, channel)
    if db_channel is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created new Channel with id: {db_channel.id}")
    return db_channel

@app.post("/securia/channel/search")
async def search_channel(db: db_dependency, channel: schemas.ChannelSearch, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.fid == channel.fid,
                                              models.Channel.channel_id == channel.channel_id).first()
    if channel is not None:
        logger.debug(f"Found Channel - {channel.channel_id} : {channel.id}")
        return channel
    if channel is None:
        raise HTTPException(status_code=404, detail='Channel not found')
    raise HTTPException(status_code=500, detail='CRUD issue')

@app.get("/securia/channel/id/{channel_id}")
async def get_channel_by_id(db: db_dependency, channel_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if channel is not None:
        return channel
    if channel is None:
        raise HTTPException(status_code=404, detail='Channel not found')
    raise HTTPException(status_code=509, detail='CRUD issue')

@app.get("/securia/channels_by_recorder/{recorder_id}", response_model=list[schemas.Channel])
async def get_channel_by_id(db: db_dependency, recorder_id: int = Path(gt=0), skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channels = db.query(models.Channel).filter(models.Channel.fid == recorder_id).offset(skip).limit(limit).all()
    if channels is not None:
        return [schemas.Channel.from_orm(channel) for channel in channels]
    if channels is None:
        raise HTTPException(status_code=404, detail='Channels not found')
    raise HTTPException(status_code=509, detail='CRUD issue')

@app.get("/securia/channel/name/{channel_name}")
async def get_channel_by_id(db: db_dependency, channel_name: str = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.channel_id == channel_name).first()
    if channel is not None:
        return channel
    if channel is None:
        raise HTTPException(status_code=404, detail='Channel not found')
    raise HTTPException(status_code=509, detail='CRUD issue')

# Image APIs

@app.post("/securia/image")
async def create_image(db: db_dependency, image: schemas.ImageCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    logger.debug(f"received {image}")
    db_image = crud.create_image(db, image)
    if db_image is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created new Image with id: {db_image.id}")
    return db_image

@app.get("/securia/image/{image_id}")
async def get_image_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if image is not None:
        return image
    if image is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    raise HTTPException(status_code=404, detail='Image not found')

@app.get("/securia/image_file/{image_id}",
    responses = {
        200: {
            "content": {"image/jpeg": {}}
        }
    }
)

@app.get("/securia/image/channel/{fid_id}",response_model=list[schemas.Image])
async def get_image_by_channel_fid(db: db_dependency,
                                   fid_id: int = Path(gt=0),
                                   skip: int = 0,
                                   limit: int = 100,
                                   sort_by: str = Query("id", description="Field to sort by"),
                                   sort_order: SortOrder = Query(SortOrder.asc, description="Sort order (asc or desc)"),
                                   current_user: dict = Depends(get_current_user)
                                   ):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    try:
        query = db.query(models.Image).filter(models.Image.fid == fid_id)

        # Get the attribute to sort by
        sort_attribute = getattr(models.Image, sort_by, None)
        if sort_attribute is None:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

        # Apply sorting
        if sort_order == SortOrder.desc:
            query = query.order_by(desc(sort_attribute))
        else:
            query = query.order_by(sort_attribute)

        # Apply pagination
        images = query.offset(skip).limit(limit).all()

        if not images:
            raise HTTPException(status_code=404, detail='Images not found')

        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/securia/detection/channel/{fid_id}",response_model=list[schemas.Detection])
async def get_detection_by_channel_fid(db: db_dependency,
                                   fid_id: int = Path(gt=0),
                                   skip: int = 0,
                                   limit: int = 100,
                                   sort_by: str = Query("id", description="Field to sort by"),
                                   sort_order: SortOrder = Query(SortOrder.asc, description="Sort order (asc or desc)"),
                                   current_user: dict = Depends(get_current_user)
                                   ):
    from sqlalchemy import select, join
    from sqlalchemy.orm import aliased
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    try:
        d = aliased(models.Detection)
        i = aliased(models.Image)
        c = aliased(models.Channel)

        query = db.query(d).select_from(d).join(i).join(c).filter(c.id == fid_id)

        # Get the attribute to sort by
        sort_attribute = getattr(d, sort_by, None)
        if sort_attribute is None:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

        # Apply sorting
        if sort_order == SortOrder.desc:
            query = query.order_by(desc(sort_attribute))
        else:
            query = query.order_by(sort_attribute)

        # Apply pagination
        detections = query.offset(skip).limit(limit).all()

        if not detections:
            raise HTTPException(status_code=404, detail='Detections not found')

        return detections
    except Exception as e:
        logger.debug(f"{e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

async def get_image_file_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    import io
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if image is not None:
        image_path = image.s3_path.split('/')
        logger.debug(f'Bucket is {image_path[0]}, key is {image_path[1]}')
        image = s3.fetch_image(image_path[0], image_path[1])
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')  # or 'PNG'
        img_byte_arr.seek(0)
        return responses.StreamingResponse(img_byte_arr, media_type="image/jpeg")  # or "image/png"

    if image is None:
        raise HTTPException(status_code=509, detail='Image issue')
    raise HTTPException(status_code=404, detail='Image not found')

# Detection APIs

@app.post("/securia/detection")
async def create_detection(db: db_dependency, detection: schemas.DetectionCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    try:
        db_detection = crud.create_detection(db, detection)
        if db_detection is None:
            raise HTTPException(status_code=509, detail='CRUD issue')
    except:
        logger.error("Issue somewhere")
    logger.debug(f"Created new Detections with id: {db_detection.id}")
    return db_detection

@app.get("/securia/detection/{detection_id}")
async def get_detection_by_id(db: db_dependency, detection_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if detection is not None:
        return detection
    if detection is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    raise HTTPException(status_code=404, detail='Detection not found')

@app.post("/securia/detection_objects")
async def create_detection(db: db_dependency, detectionobject: schemas.DetectionObjectCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    try:
        db_detectionobj = crud.create_detection_object(db, detectionobject)
        if db_detectionobj is None:
            raise HTTPException(status_code=509, detail='CRUD issue')
    except:
        logger.error("Issue somewhere")
    logger.debug(f"Created new Detections with id: {db_detectionobj.id}")
    return db_detectionobj

@app.get("/securia/detection_objects/{detectionobject_id}")
async def get_detection_by_id(db: db_dependency, detectionobject_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    detection = db.query(models.DetectionObjects).filter(models.DetectionObjects.id == detectionobject_id).first()
    if detection is not None:
        return detection
    if detection is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    raise HTTPException(status_code=404, detail='Detection not found')