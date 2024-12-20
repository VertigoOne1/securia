import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Path, responses, Query, WebSocket, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from enum import Enum
from typing import Annotated, Optional, Callable
from prometheus_client import make_asgi_app
from envyaml import EnvYAML
from logger import setup_custom_logger
from starlette import status
import s3
from uuid import UUID
import threading
import signal
import sys
import faulthandler
from contextlib import contextmanager

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

# Token generation function
def create_access_token(data: dict):
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def calc_expiry():
    import datetime
    date_and_time = datetime.datetime.now()
    logger.debug(f"Original time: {date_and_time}")
    time_change = datetime.timedelta(seconds=config['api']['token_expiry_seconds'])
    new_time = date_and_time + time_change
    logger.debug(f"New Time: {new_time}")
    return int(new_time.timestamp()) #strip miliseconds

# Dependency for extracting and verifying JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    import datetime
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.trace(f"Token Payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = {"sub": payload.get("sub"),
                      "role": payload.get("role"),
                      "email": payload.get("email"),
                      "id": payload.get("id"),
                      "exp": payload.get("exp")
                    }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return token_data

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class Role(Enum):
    GUEST = 1
    USER = 2
    ADMIN = 3
    SUPER = 4

class AccessHierarchy:
    @staticmethod
    def can_access_user(accessor_role: str, target_role: str) -> bool:
        try:
            accessor = Role[accessor_role.upper()]
            target = Role[target_role.upper()]
            if accessor.value >= target.value:
                logger.debug(f"accessor_role '{accessor_role}' is greater or equal to target_role '{target_role}'")
                return True
            else:
                logger.debug(f"accessor_role '{accessor_role}' is NOT greater or equal to target_role '{target_role}'")
                return False
        except KeyError:
            return False

    def can_get_object(accessor_role: str) -> bool:
        try:
            accessor = Role[accessor_role.upper()]
            target = Role["guest".upper()]
            if accessor.value >= target.value:
                logger.debug(f"accessor_role '{accessor_role}' is greater or equal to target_role 'user'")
                return True
            else:
                logger.debug(f"accessor_role '{accessor_role}' is NOT greater or equal to target_role 'user'")
                return False
        except KeyError:
            return False

    def can_create_update_delete_object(accessor_role: str) -> bool:
        try:
            accessor = Role[accessor_role.upper()]
            target = Role["user".upper()]
            if accessor.value >= target.value:
                logger.debug(f"accessor_role '{accessor_role}' is greater or equal to target_role 'user'")
                return True
            else:
                logger.debug(f"accessor_role '{accessor_role}' is NOT greater or equal to target_role 'user'")
                return False
        except KeyError:
            return False

    @staticmethod
    def get_role_value(role: str) -> Optional[int]:
        try:
            return Role[role.upper()].value
        except KeyError:
            return None

    @staticmethod
    def is_valid_role(role: str) -> bool:
        return role.upper() in Role.__members__

    @staticmethod
    def get_all_roles() -> list[str]:
        return [role.name.lower() for role in Role]

class BackgroundTaskManager:
    def __init__(self):
        self._task_count = 0
        self._lock = threading.Lock()

    def _wrap_task(self, task: Callable, *args, **kwargs):
        """Wrapper to properly track task completion"""
        try:
            task(*args, **kwargs)
        finally:
            with self._lock:
                self._task_count -= 1
            logger.debug(f"Background task completed. Active tasks: {self._task_count}")

    def schedule_task(self, background_tasks: BackgroundTasks, task: Callable, *args, **kwargs) -> bool:
        """
        Attempts to schedule a task if no other tasks are running.
        Returns True if successfully scheduled, False otherwise.
        """
        with self._lock:
            logger.debug(f"Running tasks: {self._task_count}")
            if self._task_count > 0:
                logger.debug(f"Cannot schedule task. Running: {self._task_count}")
                return False
            else:
                self._task_count += 1
                logger.debug(f"Scheduling new task. Active tasks: {self._task_count}")
                background_tasks.add_task(self._wrap_task, task, *args, **kwargs)
                return True

# Create a global instance
task_manager = BackgroundTaskManager()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for regular routes
def get_db_dependency():
    with get_db() as db:
        yield db

# Separate db function for background tasks
def prune_data_background(older_than: int):
    with get_db() as db:
        crud.prune_all_data_older_than(db, older_than)
        logger.debug(f"Completed pruning of data older than {older_than} days")

def prune_images_background(older_than: int):
    with get_db() as db:
        crud.prune_all_images_older_than(db, older_than)
        logger.debug(f"Completed pruning of data older than {older_than} days")

db_dependency = Annotated[Session, Depends(get_db_dependency)]

logger.debug("Create system users if necessary")
admin_users = crud.create_system_users(SessionLocal())

def authenticate_user(db: db_dependency, username: str, password: str):
    logger.debug("Check if username exists")
    user = crud.get_user_by_username(db, username)
    # logger.debug(f"{user}")
    if user is None:
        logger.info("User does not exist")
        return None
    elif not user or not pwd_context.verify(password, user.password):
        return False
    return user

logger.info("Creating schemas")
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    import sys
    logger.error(f"Could not create schemas: {str(e)}")
    faulthandler.dump_traceback()
    sys.exit(1)

def start_api_server():
    uvconfig = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config['api']['default_port'],
        log_level=config['api']['debug_level']
    )
    server = uvicorn.Server(uvconfig)

    def run_server():
        server.run()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    def signal_handler(signum, frame):
        print("Received shutdown signal. Stopping server...")
        server.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            thread.join(timeout=1.0)
            if not thread.is_alive():
                break
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping server...")
        server.should_exit = True
        sys.exit(0)

@app.get("/")
def root():
    return {"message": "SecurIA - API"}

@app.get("/securia/status")
def status():
    if config['api']['maintenance_mode']:
        return {"status": "maintenance"}
    else:
        return {"status": "up"}

@app.websocket('/securia/ws')
async def websocket_endpoint(websocket: WebSocket, value: Optional[int] = Query(1)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(f"prefix: {value} - data - {data}")
            response = f"prefix: {value} - data - {data}"
            await websocket.send_text(f"{response}")
    except:
        pass

# Authentication

@app.post("/token")
async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug(f"Authenticating - {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token_expires = calc_expiry()
    token_data = {"sub": user.username, "role": user.role, "email": user.email, "id": user.id, "exp": token_expires}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/securia/token")
async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug(f"Authenticating - {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token_expires = calc_expiry()
    token_data = {"sub": user.username, "role": user.role, "email": user.email, "id": user.id, "exp": token_expires}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/securia/token_test")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Successfully Authenticated. Details: {current_user}"}

# User APIs

@app.post("/securia/user")
async def create_user(db: db_dependency, user: schemas.UserCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_access_user(current_user['role'], "super"):
        pass
    elif AccessHierarchy.can_access_user(current_user['role'], user.role):
        pass
    else:
        logger.error(f"{current_user['role']} < {user.role}")
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    logger.debug(f"{user}")
    data = crud.create_user(db, user)
    if data is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created user with id: {data.id}")
    return data

@app.get("/securia/user/{user_id}")
async def get_user_by_id(db: db_dependency, user_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    data = db.query(models.User).filter(models.User.id == user_id).first()
    if AccessHierarchy.can_access_user(current_user['role'], "super"):
        pass
    elif AccessHierarchy.can_access_user(current_user['role'], data.role):
        pass
    else:
        logger.error(f"{current_user['role']} < {data.role}")
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.get("/securia/user/username/{username}", response_model=list[schemas.User])
async def get_user_by_username(db: db_dependency, username: str, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    data = db.query(models.User).filter(models.User.username == username).all()
    if AccessHierarchy.can_access_user(current_user['role'], "super"):
        pass
    elif AccessHierarchy.can_access_user(current_user['role'], data[0].role):
        pass
    else:
        logger.error(f"{current_user['role']} < {data.role}")
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/user/{user_id}")
async def update_user_by_id(db: db_dependency, user: schemas.UserUpdate, user_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if AccessHierarchy.can_access_user(current_user['role'], "super"):
        pass
    elif AccessHierarchy.can_access_user(current_user['role'], db_user.role):
        pass
    else:
        logger.error("You cannot update users that have higher access than your own")
        raise HTTPException(status_code=403, detail="You cannot update users that have higher access than your own")
    if user.role is not None:
        if AccessHierarchy.can_access_user(current_user['role'], user.role):
            pass
        else:
            logger.error("You cannot update users to have higher access than your own")
            raise HTTPException(status_code=403, detail="You cannot update users to have higher access than your own")
    data = crud.update_user(db, id=user_id, user=user)
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.delete("/securia/user/{user_id}")
async def delete_user_by_id(db: db_dependency, user_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='User Not Found')
    if AccessHierarchy.can_access_user(current_user['role'], "super"):
        pass
    elif AccessHierarchy.can_access_user(current_user['role'], db_user.role):
        pass
    else:
        logger.error(f"{current_user['role']} < {db_user.role}")
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    delete_user = crud.delete_user(db, user_id)
    if delete_user is None:
        raise HTTPException(status_code=404, detail='User Not Found')
    logger.debug(f"Deleted user with id: {user_id}")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"User with id {user_id} deleted"}
    )

@app.get("/securia/user", response_model=list[schemas.User])
async def get_users(db: db_dependency, skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.User).offset(skip).limit(limit).all()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

# Recorder APIs

@app.post("/securia/recorder")
async def create_recorder(db: db_dependency, recorder: schemas.RecorderCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.create_recorder(db, recorder)
    if data is None:
        raise HTTPException(status_code=509, detail='CRUD issue')
    logger.debug(f"Created recorder with id: {data.id}")
    return data

@app.get("/securia/recorder/{recorder_id}")
async def get_recorder_by_id(db: db_dependency, recorder_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Recorder).filter(models.Recorder.id == recorder_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.get("/securia/recorder/uuid/{recorder_uuid}")
async def get_recorder_by_uuid(db: db_dependency, recorder_uuid: UUID = Path(..., description="The recorder's UUID4"), skip: int = 0, limit: int = 1, current_user: dict = Depends(get_current_user)):
    import uuid
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Recorder).filter(models.Recorder.recorder_uuid == recorder_uuid).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/recorder/{recorder_id}")
async def update_recorder_by_id(db: db_dependency, recorder: schemas.RecorderUpdate, recorder_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.update_recorder(db, id=recorder_id, recorder=recorder)
    if data is None:
        raise HTTPException(status_code=509, detail='Create issue')
    return data

@app.delete("/securia/recorder/{recorder_id}")
async def delete_recorder_by_id(db: db_dependency, recorder_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.delete_recorder(db, recorder_id)
    if data is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Deleted recorder with id: {recorder_id}")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Recorder with id {recorder_id} deleted"}
    )

@app.post("/securia/recorder/search")
async def search_recorder(db: db_dependency, recorder: schemas.RecorderSearch, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Recorder).filter(models.Recorder.uri == recorder.uri).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.get("/securia/recorder", response_model=list[schemas.Recorder])
async def get_recorder_by_id(db: db_dependency, skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")

    # Query to find recorders based on the user's preferences
    user_recorder_ids = db.query(models.UserRecorderPreference.recorder_id).filter_by(user_id=current_user['id']).subquery()

    # Fetching recorders that match user preferences
    data = db.query(models.Recorder).filter(models.Recorder.id.in_(user_recorder_ids)).all()

    # return recorders if recorders else []

    data = db.query(models.Recorder).offset(skip).limit(limit).all()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

# Channel APIs

@app.post("/securia/channel")
async def create_channel(db: db_dependency, channel: schemas.ChannelCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.create_channel(db, channel)
    if data is None:
        raise HTTPException(status_code=509, detail='create issue')
    return data

@app.get("/securia/channel/id/{channel_id}")
async def get_channel_by_id(db: db_dependency, channel_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/channel/{channel_id}")
async def update_channel_by_id(db: db_dependency, channel: schemas.ChannelUpdate, channel_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.update_channel(db, id=channel_id, channel=channel)
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.delete("/securia/channel/{channel_id}")
async def delete_channel_by_id(db: db_dependency, channel_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.delete_channel(db, channel_id)
    if data is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Channel with id: {channel_id} deleted")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Channel with id {channel_id} deleted"}
    )

@app.post("/securia/channel/search/")
async def search_channel(db: db_dependency, channel: schemas.ChannelSearch, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Channel).filter(models.Channel.fid == channel.fid,
                                              models.Channel.channel_id == channel.channel_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data


@app.get("/securia/channels_by_recorder/{recorder_id}", response_model=list[schemas.Channel])
async def get_channels_by_recorder(db: db_dependency, recorder_id: int = Path(gt=0), skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Channel).filter(models.Channel.fid == recorder_id).offset(skip).limit(limit).all()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return [schemas.Channel.from_orm(d) for d in data]

@app.get("/securia/channel/name/{channel_name}")
async def get_channels_by_name(db: db_dependency, channel_name: str, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Channel).filter(models.Channel.channel_id == channel_name).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

# Image APIs

@app.post("/securia/image")
async def create_image(db: db_dependency, image: schemas.ImageCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    logger.trace(f"received {image}")
    data = crud.create_image(db, image)
    if data is None:
        raise HTTPException(status_code=509, detail='create issue')
    return data

@app.get("/securia/image/{image_id}")
async def get_image_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Image).filter(models.Image.id == image_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/image/{image_id}")
async def update_image_by_id(db: db_dependency, image: schemas.ImageUpdate, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.update_image(db, id=image_id, image=image)
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.delete("/securia/image/{image_id}")
async def delete_image_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.delete_image(db, image_id)
    if data is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Image with id: {image_id} deleted")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Image with id {image_id} deleted"}
    )

@app.delete("/securia/image/recursive/{image_id}")
async def delete_image_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.prune_image(db, image_id)
    if data is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Image with id: {image_id} and all related objects pruned")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Image with id {image_id} pruned"}
    )

@app.delete("/securia/image/recursive/days/{older_than}")
async def delete_images_older_than(db: db_dependency, background_tasks: BackgroundTasks, older_than: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    logger.debug(f"Starting background task for pruning")
    if not task_manager.schedule_task(background_tasks, prune_images_background, older_than):
        raise HTTPException(
            status_code=409,
            detail="Another maintenance task is currently running. Please try again later."
        )
    # background_tasks.add_task(prune_images_background, older_than)
    logger.debug(f"Images older than: {older_than} and all related objects scheduled for pruning")
    return responses.JSONResponse(
        status_code=202,
        content={"message": f"Images older than {older_than} pruning initiated"}
    )

@app.delete("/securia/data_maintenance/recursive/{image_id}")
async def delete_image_and_metadata_by_id(db: db_dependency, background_tasks: BackgroundTasks, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.prune_all_data(db, image_id)
    if data is None:
        raise HTTPException(status_code=404, detail='Not Found')
    return responses.JSONResponse(
        status_code=202,
        content={"message": f"Image with id {image_id} pruned"}
    )

@app.delete("/securia/data_maintenance/recursive/days/{older_than}")
async def delete_images_and_metadata_older_than(db: db_dependency,
                                                background_tasks: BackgroundTasks,
                                                older_than: int = Path(gt=0),
                                                current_user: dict = Depends(get_current_user),
                                                ):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    # Try to schedule the background task
    logger.debug(f"Starting background task for pruning")
    if not task_manager.schedule_task(background_tasks, prune_data_background, older_than):
        raise HTTPException(
            status_code=409,
            detail="Another maintenance task is currently running. Please try again later."
        )
    # background_tasks.add_task(prune_data_background, older_than)
    logger.debug(f"Images older than: {older_than} and all related objects pruning background task initiated")
    return responses.JSONResponse(
        status_code=202,
        content={"message": f"Images older than {older_than} pruning initiated"}
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
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
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
        logger.error(f'Server error: {str(e)}')
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
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
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
        data = query.offset(skip).limit(limit).all()

        if data is None:
            raise HTTPException(status_code=404, detail='no data found')
        return data

        return detections
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/securia/detection/image/{fid_id}",response_model=list[schemas.DetectionObjectBase])
async def get_detections_by_image_fid(db: db_dependency,
                                   fid_id: int = Path(gt=0),
                                   skip: int = 0,
                                   limit: int = 100,
                                   sort_by: str = Query("id", description="Field to sort by"),
                                   sort_order: SortOrder = Query(SortOrder.asc, description="Sort order (asc or desc)"),
                                   current_user: dict = Depends(get_current_user)
                                   ):
    from sqlalchemy import select, join
    from sqlalchemy.orm import aliased
    import json
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    try:
        o = aliased(models.DetectionObject)
        d = aliased(models.Detection)
        i = aliased(models.Image)

        query = db.query(o).select_from(o).join(d).join(i).filter(i.id == fid_id)

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
        data = query.offset(skip).limit(limit).all()

        if data is None:
            raise HTTPException(status_code=404, detail='no data found')
        return data

        return detections
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/securia/image_file/{image_id}", responses = {200: {"content": {"image/jpeg": {}}}})
async def get_image_file_by_id(db: db_dependency, image_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    import io
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Image).filter(models.Image.id == image_id).first()
    if data is not None:
        image_path = data.s3_path.split('/')
        logger.debug(f'Bucket is {image_path[0]}, key is {image_path[1]}')
        image = s3.fetch_image(image_path[0], image_path[1])
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')  # or 'PNG'
        img_byte_arr.seek(0)
        return responses.StreamingResponse(img_byte_arr, media_type="image/jpeg")  # or "image/png"

    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

# Detection APIs CRUD

@app.post("/securia/detection")
async def create_detection(db: db_dependency, detection: schemas.DetectionCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    try:
        db_detection = crud.create_detection(db, detection)
        if db_detection is None:
            raise HTTPException(status_code=509, detail='CRUD issue')
        logger.debug(f"Created Detections with id: {db_detection.id}")
    except:
        logger.error("create issue")
    return db_detection

@app.get("/securia/detection/{detection_id}")
async def get_detection_by_id(db: db_dependency, detection_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/detection/{detection_id}")
async def update_detection_by_id(db: db_dependency, detection: schemas.DetectionUpdate, detection_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.update_detection(db, id=detection_id, detection=detection)
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.delete("/securia/detection/{detection_id}")
async def delete_detection_by_id(db: db_dependency, detection_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    db_det = crud.delete_detection(db, detection_id)
    if db_det is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Detection with id: {detection_id} deleted")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Detection with id {detection_id} deleted"}
    )

@app.get("/securia/detection/recorder_total/{recorder_id}/{days}")
async def detection_count_by_recorder_id(db: db_dependency, recorder_id: int = Path(gt=0), days: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    from datetime import datetime, timedelta
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    start_day = datetime.now() - timedelta(days=days)
    logger.debug(f"Start day - {start_day}")
    data = db.query(func.count(models.Detection.id).label('total_detections'))\
        .join(models.Image, models.Detection.fid == models.Image.id)\
        .join(models.Channel, models.Image.fid == models.Channel.id)\
        .join(models.Recorder, models.Channel.fid == models.Recorder.id)\
        .filter(models.Recorder.id == recorder_id)\
        .filter(models.Detection.detections_timestamp >= start_day)\
        .scalar()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

# Detection Objects APIs CRUD

@app.post("/securia/detection_object")
async def create_detection_object(db: db_dependency, detectionobject: schemas.DetectionObjectCreate, current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    try:
        logger.trace(f"creating - {detectionobject}")
        db_detectionobj = crud.create_detection_object(db, detectionobject)
        if db_detectionobj is None:
            raise HTTPException(status_code=509, detail='CRUD issue')
        logger.debug(f"Created Detection object with id: {db_detectionobj.id}")
    except Exception as e:
        logger.error(f"{e}")
    return db_detectionobj

@app.get("/securia/detection_object/{detectionobject_id}")
async def get_detection_object_by_id(db: db_dependency, detectionobject_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = db.query(models.DetectionObjects).filter(models.DetectionObjects.id == detectionobject_id).first()
    if data is None:
        raise HTTPException(status_code=404, detail='no data found')
    return data

@app.post("/securia/detection_object/{detectionobject_id}")
async def update_detection_object_by_id(db: db_dependency, detectionobject: schemas.DetectionObjectUpdate, detectionobject_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    data = crud.update_detection_object(db, id=detectionobject_id, detectionobject=detectionobject)
    if data is None:
        raise HTTPException(status_code=509, detail='update issue')
    return data

@app.delete("/securia/detection_object/{detectionobject_id}")
async def delete_detection_object_by_id(db: db_dependency, detectionobject_id: int = Path(gt=0), current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_create_update_delete_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    db_deto = crud.delete_detection_object(db, detectionobject_id)
    if db_deto is None:
        raise HTTPException(status_code=404, detail='Not Found')
    logger.debug(f"Detection object with id: {detectionobject_id} deleted")
    return responses.JSONResponse(
        status_code=200,
        content={"message": f"Detection object with id {detectionobject_id} deleted"}
    )

# Special requests

@app.get("/securia/summary", response_model=list[schemas.GlobalDetectionSummary])
async def get_summary(db: db_dependency,
                      skip: int = 0,
                      limit: int = 100,
                      sort_by: str = Query("collected_timestamp", description="Field to sort by"),
                      sort_order: SortOrder = Query(SortOrder.desc, description="Sort order (asc or desc)"),
                      current_user: dict = Depends(get_current_user)):
    from sqlalchemy import select, join, desc
    from sqlalchemy.orm import aliased
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    try:
        o = aliased(models.DetectionObject)
        d = aliased(models.Detection)
        i = aliased(models.Image)
        c = aliased(models.Channel)
        r = aliased(models.Recorder)

        query = (
            select(
                i.collected_timestamp,
                o.detection_name,
                o.confidence,
                i.s3_path,
                c.channel_id,
                c.friendly_name.label('channel_friendly_name'),
                c.description.label('channel_description'),
                r.friendly_name.label('recorder_friendly_name')
            )
            .select_from(o)
            .join(d, o.fid == d.id)
            .join(i, d.fid == i.id)
            .join(c, i.fid == c.id)
            .join(r, c.fid == r.id)
        )

        # Get the attribute to sort by
        sort_attribute = getattr(i, sort_by, None)
        if sort_attribute is None:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

        # Apply sorting
        if sort_order == SortOrder.desc:
            query = query.order_by(desc(sort_attribute))
        else:
            query = query.order_by(sort_attribute)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = db.execute(query)
        recent_detections_summary = result.fetchall()

        if not recent_detections_summary:
            raise HTTPException(status_code=404, detail='Detections not found')

        return recent_detections_summary
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/securia/summary/{recorder_id}", response_model=list[schemas.GlobalDetectionSummary])
async def get_summary_by_recorder(db: db_dependency,
                      recorder_id: int = Path(gt=0),
                      skip: int = 0,
                      limit: int = 100,
                      sort_by: str = Query("collected_timestamp", description="Field to sort by"),
                      sort_order: SortOrder = Query(SortOrder.desc, description="Sort order (asc or desc)"),
                      current_user: dict = Depends(get_current_user)):
    from sqlalchemy import select, join, desc
    from sqlalchemy.orm import aliased
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    if AccessHierarchy.can_get_object(current_user['role']):
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied by hierarchy")
    try:
        o = aliased(models.DetectionObject)
        d = aliased(models.Detection)
        i = aliased(models.Image)
        c = aliased(models.Channel)
        r = aliased(models.Recorder)

        query = (
            select(
                i.collected_timestamp,
                o.detection_name,
                o.confidence,
                i.s3_path,
                c.channel_id,
                c.friendly_name.label('channel_friendly_name'),
                c.description.label('channel_description'),
                r.friendly_name.label('recorder_friendly_name')
            )
            .select_from(o)
            .join(d, o.fid == d.id)
            .join(i, d.fid == i.id)
            .join(c, i.fid == c.id)
            .join(r, c.fid == r.id)
            .filter(r.id == recorder_id)
        )

        # Get the attribute to sort by
        sort_attribute = getattr(i, sort_by, None)
        if sort_attribute is None:
            raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

        # Apply sorting
        if sort_order == SortOrder.desc:
            query = query.order_by(desc(sort_attribute))
        else:
            query = query.order_by(sort_attribute)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = db.execute(query)
        recent_detections_summary = result.fetchall()

        if not recent_detections_summary:
            raise HTTPException(status_code=404, detail='Detections not found')

        return recent_detections_summary
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

# Health

@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=200,
    response_model=schemas.HealthCheck,
)
async def get_health() -> schemas.HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return schemas.HealthCheck(status="OK")