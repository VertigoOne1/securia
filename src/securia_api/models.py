from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, String, text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

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

    channels = relationship("Channel", back_populates="recorder")

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('recorders.id'))
    channel_id = Column(String,nullable=False)
    description = Column(String,nullable=True)

    recorder = relationship("Recorder", back_populates="channels")
    images = relationship("Image", back_populates="channel")

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('channels.id'))
    hash = Column(String,nullable=False)
    s3_path = Column(String,nullable=False)
    size = Column(Integer,nullable=False)
    type = Column(String,nullable=False)

    channel = relationship("Channel", back_populates="images")
    detections = relationship("Detection", back_populates="image")

class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer,primary_key=True,nullable=False)
    fid = Column(Integer, ForeignKey('images.id'))
    detections = Column(JSONB)

    image = relationship("Image", back_populates="detections")