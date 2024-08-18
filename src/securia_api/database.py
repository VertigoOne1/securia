from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from envyaml import EnvYAML

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

SQLALCHEMY_DATABASE_URL = config["database"]["uri"]

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         return db
#     finally:
#         db.close()

