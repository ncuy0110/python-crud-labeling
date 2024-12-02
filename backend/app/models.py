from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=False)  # Đường dẫn hình ảnh
    label = Column(String(100), nullable=False)       # Nhãn của hình ảnh
    image_metadata = Column(Text, nullable=True) 
    created_at = Column(DateTime, server_default=func.now())  # Thời gian tạo
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Thời gian cập nhật

