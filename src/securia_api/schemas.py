from pydantic import BaseModel, Json, ValidationError, validator, field_validator
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional
import json

from envyaml import EnvYAML
config = EnvYAML('config.yml')

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    tax: float | None = None

class PostBase(BaseModel):
    content: str
    title: str

    class Config:
        from_attributes = True

class CreatePost(PostBase):
    class Config:
        from_attributes = True

class RecorderBase(BaseModel):
    uri: str
    owner: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None

    class Config:
        from_attributes = True

class RecorderCreate(RecorderBase):
    class Config:
        from_attributes = True

class Recorder(RecorderBase):
    id: int

    class Config:
        from_attributes = True

class ChannelBase(BaseModel):
    fid: int
    channel_id: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ChannelCreate(ChannelBase):
    class Config:
        from_attributes = True

class ChannelSearch(BaseModel):
    fid: int
    channel_id: str

    class Config:
        from_attributes = True

class Channel(ChannelBase):
    id: int

    class Config:
        from_attributes = True

class ImageBase(BaseModel):
    fid: int
    hash: str
    s3_path: str
    content_length: int
    content_type: str
    recorder_status_code: str
    recorder_status_data: str
    collected_timestamp: datetime = None
    collection_status: str
    ingest_timestamp: datetime = None

    @field_validator('collected_timestamp', 'ingest_timestamp', mode="before")
    @classmethod
    def parse_datetime(cls, value: Any)-> datetime:
        # Define the format according to your input string
        time_format = config['api']['time_format']
        return datetime.strptime(value, time_format)

    class Config:
        from_attributes = True

class ImageCreate(ImageBase):

    class Config:
        from_attributes = True

class DetectionBase(BaseModel):
    fid: int
    detections: Json[Any]
    detections_count: int
    processing_time_ms: Json[Any]
    detections_timestamp: datetime = None

    @field_validator('detections_timestamp', mode="before")
    @classmethod
    def parse_datetime(cls, value: Any)-> datetime:
        # Define the format according to your input string
        time_format = config['api']['time_format']
        return datetime.strptime(value, time_format)

    class Config:
        from_attributes = True

class DetectionCreate(DetectionBase):
    class Config:
        from_attributes = True

class DetectionObjectBase(BaseModel):
    fid: int
    detection_class: str
    detection_name: str
    confidence: float
    xyxy: Json[Any]
    crop_s3_path: str

    class Config:
        from_attributes = True

class DetectionObjectCreate(DetectionObjectBase):
    class Config:
        from_attributes = True