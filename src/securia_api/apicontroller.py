import uvicorn
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from envyaml import EnvYAML
from logger import setup_custom_logger

import logger, logic, models, schemas, crud
from database import get_db, engine

logger = setup_custom_logger(__name__)

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

app=FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

def start_api_server():
    uvconfig = uvicorn.Config(app, host="0.0.0.0", port=config['api']['default_port'], log_level=config['api']['debug_level'])
    server = uvicorn.Server(uvconfig)
    server.run()

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.post("/post")
def create_post():
    db = get_db()
    new_post = schemas.CreatePost(title="My New Post", content="This is the content")
    db_post = crud.create_post(db, new_post)
    print(f"Created new post with id: {db_post.id}")

    post = crud.get_post(db, db_post.id)
    return post
