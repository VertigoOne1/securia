from pydantic import BaseModel, Json, ValidationError
from typing import Any, List, Optional

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
    recorder_uuid: str
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

class ChannelBase(BaseModel):
    fid: int
    channel_id: str
    friendly_name = Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ChannelCreate(ChannelBase):
    class Config:
        from_attributes = True

class ImageBase(BaseModel):
    fid: int
    hash: str
    s3_path: str
    size: str
    type: str

    class Config:
        from_attributes = True

class ImageCreate(ImageBase):
    class Config:
        from_attributes = True

class DetectionBase(BaseModel):
    fid: int
    detections: Json[Any]

    class Config:
        from_attributes = True

class DetectionCreate(DetectionBase):
    class Config:
        from_attributes = True