from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, String, text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from envyaml import EnvYAML
config = EnvYAML('config.yml')

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer,primary_key=True,nullable=False)
    title = Column(String,nullable=False)
    content = Column(String,nullable=False)
    published = Column(Boolean, server_default='TRUE')
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

class Recorder(Base):
    __tablename__ = 'recorders'

    id = Column(Integer,primary_key=True,nullable=False)
    owner = Column(String,nullable=True)
    type = Column(String,nullable=True)
    uri = Column(String,nullable=False)
    location = Column(String,nullable=True)
    contact = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    channels = relationship("Channel", back_populates="recorder")

Index("idx_recorder_uri", Recorder.id, Recorder.uri)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('recorders.id'))
    channel_id = Column(String,nullable=False)
    description = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    recorder = relationship("Recorder", back_populates="channels")
    images = relationship("Image", back_populates="channel")

Index("idx_channel", Channel.id, Channel.channel_id)

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('channels.id'))
    hash = Column(String,nullable=False)
    s3_path = Column(String,nullable=False)
    content_length = Column(Integer,nullable=False)
    content_type = Column(String,nullable=False)
    recorder_status_code = Column(String,nullable=False)
    collected_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    collection_status = Column(String,nullable=False)
    ingest_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    channel = relationship("Channel", back_populates="images")
    detections = relationship("Detection", back_populates="image")


class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('images.id'))
    detections = Column(JSONB)
    detections_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    image = relationship("Image", back_populates="detections")