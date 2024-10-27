from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time, sys
import faulthandler

from envyaml import EnvYAML

import logger, metrics

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

SQLALCHEMY_DATABASE_URL = config["database"]["uri"]

engine_pool_settings = {
        'pool_size': 10,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 60
    }

def create_engine_with_retry(url, max_retries=3, retry_interval=2):
    for attempt in range(max_retries):
        try:
            engine = create_engine(url, connect_args={'connect_timeout': 2}, **engine_pool_settings)
            engine.connect()
            return engine
        except OperationalError as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                logger.error("Max retries reached. Exiting.")
                faulthandler.dump_traceback()
                sys.exit(1)

engine = create_engine_with_retry(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
