import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Annotated
from prometheus_client import make_asgi_app
from envyaml import EnvYAML
from logger import setup_custom_logger
from starlette import status

import logger, logic, models, schemas, crud
from database import engine, SessionLocal


logger = setup_custom_logger(__name__)

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)

def start_api_server():
    uvconfig = uvicorn.Config(app, host="0.0.0.0", port=config['api']['default_port'], log_level=config['api']['debug_level'])
    server = uvicorn.Server(uvconfig)
    server.run()

@app.get("/")
def root():
    return {"message": "Hello, World!"}

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
    logger.debug(f"Created new post with id: {db_post.id}")

    post = crud.get_post(db, db_post.id)
    return post

# Recorder APIs

@app.post("/securia/recorder")
async def create_recorder(db: db_dependency, recorder: schemas.RecorderCreate):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Maintenance Mode')
    db_recorder = crud.create_recorder(db, recorder)
    logger.debug(f"Created new recorder with id: {db_recorder.id}")
    return db_recorder




@app.post("/securia/recorder/search")
async def search_recorder(db: db_dependency, recorder: schemas.RecorderCreate):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    recorder = db.query(models.Recorder).filter(models.Recorder.uri == recorder.uri).first()
    if recorder is not None:
        logger.debug(f"Found recorder uri - {recorder.uri} : {recorder.id}")
        return recorder
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Recorder not found')

@app.get("/securia/recorder/{recorder_id}")
async def get_recorder_by_id(db: db_dependency, recorder_id: int = Path(gt=0)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    recorder = db.query(models.Recorder).filter(models.Recorder.id == recorder_id).first()
    if recorder is not None:
        return recorder
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Recorder not found')

# Channel APIs

@app.post("/securia/channel")
async def create_channel(db: db_dependency, channel: schemas.ChannelCreate):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_channel = crud.create_channel(db, channel)
    logger.debug(f"Created new Channel with id: {db_channel.id}")
    return db_channel

@app.post("/securia/channel/search")
async def search_channel(db: db_dependency, channel: schemas.ChannelSearch):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.fid == channel.fid,
                                              models.Channel.channel_id == channel.channel_id).first()
    if channel is not None:
        logger.debug(f"Found Channel - {channel.channel_id} : {channel.id}")
        return channel
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Channel not found')

@app.get("/securia/channel/id/{channel_id}")
async def get_channel_by_id(db: db_dependency, channel_id: int = Path(gt=0)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if channel is not None:
        return channel
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Channel not found')

@app.get("/securia/channel/name/{channel_name}")
async def get_channel_by_id(db: db_dependency, channel_name: str = Path(gt=0)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    channel = db.query(models.Channel).filter(models.Channel.channel_id == channel_name).first()
    if channel is not None:
        return channel
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Channel not found')

# Image APIs

@app.post("/securia/image")
async def create_image(db: db_dependency, image: schemas.ImageCreate):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    logger.debug(f"received {image}")
    db_image = crud.create_image(db, image)
    logger.debug(f"Created new Image with id: {db_image.id}")
    return db_image

@app.get("/securia/image/{image_id}")
async def get_image_by_id(db: db_dependency, image_id: int = Path(gt=0)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if image is not None:
        return image
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Image not found')

# Detection APIs

@app.post("/securia/detection")
async def create_detection(db: db_dependency, detection: schemas.DetectionCreate):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_detection = crud.create_detection(db, detection)
    logger.debug(f"Created new Detections with id: {db_detection.id}")
    return db_detection

@app.get("/securia/detection/{detection_id}")
async def get_detection_by_id(db: db_dependency, detection_id: int = Path(gt=0)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if detection is not None:
        return detection
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Detection not found')