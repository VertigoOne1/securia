import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Path, responses, Query, WebSocket
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from enum import Enum
from typing import Annotated, Optional
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

import logger, logic, models, schemas
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# logger.info("Creating AI related schemas")
# try:
#     models.Base.metadata.create_all(bind=engine)
# except Exception as e:
#     import sys
#     logger.error(f"Could not create schemas: {str(e)}")
#     faulthandler.dump_traceback()
#     sys.exit(1)

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

@app.get("/securia/user/{user_id}")
async def get_user_by_id(db: db_dependency, user_id: int = Path(gt=0)):# , current_user: dict = Depends(get_current_user)):
    if config['api']['maintenance_mode']:
        raise HTTPException(status_code=422, detail='Maintenance Mode')
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is not None:
        return db_user
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    raise HTTPException(status_code=500, detail='CRUD issue')


# # Authentication

# @app.post("/token")
# async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
#     logger.debug(f"Authenticating - {form_data.username}")
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=401, detail="Incorrect username or password")
#     token_expires = calc_expiry()
#     token_data = {"sub": user.username, "role": user.role, "email": user.email, "id": user.id, "exp": token_expires}
#     access_token = create_access_token(token_data)
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/securia/token")
# async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
#     logger.debug(f"Authenticating - {form_data.username}")
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=401, detail="Incorrect username or password")
#     token_expires = calc_expiry()
#     token_data = {"sub": user.username, "role": user.role, "email": user.email, "id": user.id, "exp": token_expires}
#     access_token = create_access_token(token_data)
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/securia/token_test")
# async def protected_route(current_user: dict = Depends(get_current_user)):
#     return {"message": f"Successfully Authenticated. Details: {current_user}"}

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