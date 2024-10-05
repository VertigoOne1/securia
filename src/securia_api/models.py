from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, String, text, ForeignKey, Index, Double
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

from envyaml import EnvYAML
config = EnvYAML('config.yml')

class User(Base):
    __tablename__ = 'securia_users'
    id = Column(Integer, primary_key=True, nullable=False, comment="Unique identifier for the user")
    username = Column(String, nullable=False, comment="User login name")
    password = Column(String, nullable=False, comment="Hashed password for the user")
    first_name = Column(String, nullable=True,comment="User first name")
    last_name = Column(String, nullable=True, comment="User last name")
    company = Column(String, nullable=True, comment="Company the user is associated with")
    email = Column(String, nullable=False, comment="User email address")
    role = Column(String, nullable=False, comment="User role in the system")

Index("idx_users_email", User.id, User.email)
Index("idx_users_username", User.id, User.username)

class Recorder(Base):
    __tablename__ = 'recorders'

    id = Column(Integer,primary_key=True,nullable=False)
    recorder_uuid = Column(UUID(as_uuid=True), nullable=False, comment="recorder unique identifier")
    friendly_name = Column(String,nullable=True, comment="user defined friendly name of recorder")
    owner = Column(String,nullable=True, comment="the legal owner of the recorder")
    type = Column(String,nullable=True, comment="the type of recorder, such as hikvision")
    uri = Column(String,nullable=False, comment="the URI where images are collected")
    location = Column(String,nullable=True, comment="the physical location of the recorder")
    contact = Column(String,nullable=True, comment="contact info for this recorder")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="")
    owner_user_id = Column(Integer,nullable=True, comment="the id of the user this recorder belongs to")

    channels = relationship("Channel", back_populates="recorder")

Index("idx_recorder_uri", Recorder.id, Recorder.uri)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, nullable=False, comment="Unique identifier for the channel")
    fid = Column(Integer, ForeignKey('recorders.id'), comment="Foreign key referencing the related recorder")
    channel_id = Column(String, nullable=False, comment="Identifier for the channel defined by the recorder")
    friendly_name = Column(String, nullable=True, comment="User-defined friendly name of the channel")
    description = Column(String, nullable=True, comment="User-defined description of the channel")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="Timestamp for when the channel was created")

    # Relationship to the Recorder model
    recorder = relationship("Recorder", back_populates="channels")

    # Relationship to the Image model
    images = relationship("Image", back_populates="channel")

Index("idx_channel", Channel.id, Channel.channel_id)

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer,primary_key=True,nullable=False, comment="")
    fid = Column(Integer, ForeignKey('channels.id'), comment="the recorder channel relationship")
    hash = Column(String,nullable=False, comment="SHA256 hash of the image")
    s3_path = Column(String,nullable=False, comment="image bucket location, or NO_IMAGE if no image collected")
    content_length = Column(Integer,nullable=False, comment="size of the image or body if error")
    content_type = Column(String,nullable=False, comment="MIME content type of the collection")
    recorder_status_code = Column(String,nullable=False, comment="http status code reported by the recorder during collection")
    recorder_status_data = Column(String,nullable=True, comment="any non-image status information during collection")
    collected_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="")
    collection_status = Column(String,nullable=False, comment="if the collection was successful or not")
    notes = Column(String,nullable=True, comment="any user added notes for this image")
    tags = Column(JSONB,nullable=True, comment="any user defined tags for this image")
    ingest_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="")

    channel = relationship("Channel", back_populates="images")
    detections = relationship("Detection", back_populates="image")

Index("idx_image", Image.id, Image.fid)

class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer,primary_key=True,nullable=False, comment="unique id for this detection process")
    fid = Column(Integer, ForeignKey('images.id'), comment="the image this detection process was run against")
    detections = Column(JSONB, comment="yolo summary json output")
    detections_count = Column(Integer, nullable=True, comment="number of objects detected")
    processing_time_ms = Column(JSONB, comment="miliseconds elapsed for detection")
    detections_timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="when the detection was completed")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="detection inserted datetime")

    image = relationship("Image", back_populates="detections")
    detectionobjects = relationship("DetectionObject", back_populates="detection_rel")

Index("idx_detection", Detection.id, Detection.fid)

class DetectionObject(Base):
    __tablename__ = 'detections_objects'

    id = Column(Integer,primary_key=True,nullable=False, comment="unique id for this detection object")
    fid = Column(Integer, ForeignKey('detections.id'), comment="the detection process this object belonged to")
    detection_class = Column(String,nullable=False, comment="the class number of the detection")
    detection_name = Column(String,nullable=False, comment="the english name of the detection")
    confidence = Column(Double, nullable=False, comment="YOLO prediction confidence percentage")
    xyxy = Column(JSONB, comment="box coordinates of the detection")
    crop_s3_path = Column(String,nullable=True, comment="the s3 bucket path where this detection is stored")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), comment="object inserted datetime")

    detection_rel = relationship("Detection", back_populates="detectionobjects")

Index("idx_detectionObj", DetectionObject.id, DetectionObject.fid, DetectionObject.detection_class)