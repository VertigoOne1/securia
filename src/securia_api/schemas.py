from pydantic import BaseModel, Json, ValidationError, validator, field_validator, computed_field
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional
import json

from envyaml import EnvYAML
config = EnvYAML('config.yml')

class UserBase(BaseModel):
    username: str
    password: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class RecorderBase(BaseModel):
    recorder_uuid: str
    uri: str
    owner_user_id: Optional[int] = None
    friendly_name: Optional[str] = None
    owner: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None

    class Config:
        from_attributes = True

class RecorderCreate(RecorderBase):
    class Config:
        from_attributes = True

class RecorderUpdate(BaseModel):
    recorder_uuid: Optional[str] = None
    uri: Optional[str] = None
    owner_user_id: Optional[int] = None
    friendly_name: Optional[str] = None
    owner: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None

    class Config:
        from_attributes = True

class Recorder(RecorderBase):
    id: int

    class Config:
        from_attributes = True

class ChannelBase(BaseModel):
    fid: int
    channel_id: str
    friendly_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ChannelCreate(ChannelBase):
    class Config:
        from_attributes = True

class ChannelUpdate(BaseModel):
    fid: Optional[int] = None
    channel_id: Optional[str] = None
    friendly_name: Optional[str] = None
    description: Optional[str] = None

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
    notes: str = None
    tags: Json[Any] = None
    ingest_timestamp: datetime = None

    @field_validator('collected_timestamp', 'ingest_timestamp', mode="before")
    @classmethod
    def parse_datetime(cls, value: Any)-> datetime:
        # Define the format according to your input string
        if isinstance(value, str):
           time_format = config['api']['time_format']
           return datetime.strptime(value, time_format)
        return value

    @field_validator('tags', mode="before")
    @classmethod
    def parse_tags(cls, value: Any)-> str:
        if value is not None:
            return "{}"
        return "{}"

    @field_validator('notes', mode="before")
    @classmethod
    def parse_notes(cls, value: Any)-> str:
        if value is None:
            return "None"
        return value

    # @computed_field
    # @property
    # def full_s3_path(self) -> str:
    #     return f"{s3_base_path.rstrip('/')}/{self.s3_path.lstrip('/')}"

    class Config:
        from_attributes = True

class ImageCreate(ImageBase):

    class Config:
        from_attributes = True

class ImageUpdate(BaseModel):
    fid: Optional[int] = None
    hash: Optional[str] = None
    s3_path: Optional[str] = None
    content_length: Optional[int] = None
    content_type: Optional[str] = None
    recorder_status_code: Optional[str] = None
    recorder_status_data: Optional[str] = None
    collection_status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[Json[Any]] = None

class Image(ImageBase):
    id: int

    class Config:
        from_attributes = True

class DetectionBase(BaseModel):
    fid: int
    detections: Json[Any]
    detections_count: int = None
    processing_time_ms: Json[Any]
    detections_timestamp: datetime = None

    @field_validator('detections_timestamp', mode="before")
    @classmethod
    def parse_datetime(cls, value: Any)-> datetime:
        # Define the format according to your input string
        if isinstance(value, str):
           time_format = config['api']['time_format']
           return datetime.strptime(value, time_format)
        return value

    @field_validator('detections_count', mode="before")
    @classmethod
    def parse_detections_count(cls, value: Any)-> str:
        if value is None:
            return str(0)
        return value

    class Config:
        from_attributes = True

class DetectionCreate(DetectionBase):
    class Config:
        from_attributes = True

class DetectionUpdate(BaseModel):
    fid: Optional[int] = None
    detections: Optional[Json[Any]] = None
    detections_count: Optional[int] = None
    processing_time_ms: Optional[Json[Any]] = None

class Detection(DetectionBase):
    id: int

    @field_validator('processing_time_ms', mode="before")
    @classmethod
    def parse_processing_time_ms(cls, value: Any)-> str:
        if value is not None:
            total = 0.0
            for key, value in value.items():
                total = total + float(value)
            return str(total)
        return str(0.0)

    @field_validator('detections', mode="before")
    @classmethod
    def parse_detections(cls, value: Any)-> str:
        if value is not None:
            return "{}"
        return "{}"

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

class DetectionObjectUpdate(BaseModel):
    fid: Optional[int] = None
    detection_class: Optional[str] = None
    detection_name: Optional[str] = None
    confidence: Optional[float] = None
    xyxy: Optional[Json[Any]] = None
    crop_s3_path: Optional[str] = None