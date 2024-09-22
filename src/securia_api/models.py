from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, String, text, ForeignKey, Index, Double
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from envyaml import EnvYAML
config = EnvYAML('config.yml')

class User(Base):
    __tablename__ = 'securia_users'
    id = Column(Integer,primary_key=True,nullable=False)
    username = Column(String,nullable=False)
    password = Column(String,nullable=False)
    first_name = Column(String,nullable=True)
    last_name = Column(String,nullable=True)
    company = Column(String,nullable=True)
    email = Column(String,nullable=False)
    role = Column(String,nullable=False)

Index("idx_users_email", User.id, User.email)
Index("idx_users_username", User.id, User.username)

class Recorder(Base):
    __tablename__ = 'recorders'

    id = Column(Integer,primary_key=True,nullable=False)
    friendly_name = Column(String,nullable=True)
    owner = Column(String,nullable=True)
    type = Column(String,nullable=True)
    uri = Column(String,nullable=False)
    location = Column(String,nullable=True)
    contact = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    owner_user_id = Column(Integer,nullable=True)

    channels = relationship("Channel", back_populates="recorder")

Index("idx_recorder_uri", Recorder.id, Recorder.uri)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('recorders.id'))
    channel_id = Column(String,nullable=False)
    friendly_name = Column(String,nullable=True)
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
    recorder_status_data = Column(String,nullable=True)
    collected_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    collection_status = Column(String,nullable=False)
    notes = Column(String,nullable=True)
    tags = Column(JSONB,nullable=True)
    ingest_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    channel = relationship("Channel", back_populates="images")
    detections = relationship("Detection", back_populates="image")

Index("idx_image", Image.id, Image.fid)

class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('images.id'))
    detections = Column(JSONB)
    detections_count = Column(Integer, nullable=True)
    processing_time_ms = Column(JSONB)
    detections_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    image = relationship("Image", back_populates="detections")
    detectionobjects = relationship("DetectionObject", back_populates="detection_rel")

Index("idx_detection", Detection.id, Detection.fid)

class DetectionObject(Base):
    __tablename__ = 'detections_objects'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('detections.id'))
    detection_class = Column(String,nullable=False)
    detection_name = Column(String,nullable=False)
    confidence = Column(Double, nullable=False)
    xyxy = Column(JSONB)
    crop_s3_path = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    detection_rel = relationship("Detection", back_populates="detectionobjects")

Index("idx_detectionObj", DetectionObject.id, DetectionObject.fid, DetectionObject.detection_class)