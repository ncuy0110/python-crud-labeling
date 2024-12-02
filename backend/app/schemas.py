from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageMetadataCreate(BaseModel):
    image_path: str
    label: str
    image_metadata: str

    class Config:
        orm_mode = True  # Giúp Pydantic hiểu được đối tượng trả về từ SQLAlchemy

class ImageMetadataResponse(BaseModel):
    id: int
    image_path: str
    label: str
    image_metadata: Optional[str] = None  # Metadata có thể là None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 


class ImageMetadataUpdate(BaseModel):
    label: str
    image_metadata: str
