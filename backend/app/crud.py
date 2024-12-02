from sqlalchemy.orm import Session
from . import models
from sqlalchemy import update
import os
from pathlib import Path
import h5py
from PIL import Image
import io
from fastapi import HTTPException
import logging
import numpy as np


logger = logging.getLogger("uvicorn.access")



# Thêm mới dữ liệu vào bảng image_metadata
def create_image_metadata(db: Session, image_path: str, label: str, image_metadata: str):
    db_image = models.ImageMetadata(image_path=image_path, label=label, image_metadata=image_metadata)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

# Lấy tất cả thông tin từ bảng image_metadata
def get_all_image_metadata(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.ImageMetadata).offset(skip).limit(limit).all()

# Cập nhật thông tin của ảnh (chỉ label và metadata)
def update_image_metadata(db: Session, image_id: int, label: str = None, image_metadata: str = None):
    # Tìm ảnh theo image_id
    db_image = db.query(models.ImageMetadata).filter(models.ImageMetadata.id == image_id).first()
    if db_image is None:
        return None
    
    db_image.label = label
    db_image.image_metadata = image_metadata

    # Cập nhật thời gian sửa đổi
    db.commit()
    db.refresh(db_image)

    return db_image

# Xóa ảnh và bản ghi trong cơ sở dữ liệu
def delete_image_metadata(db: Session, image_id: int):
    # Tìm ảnh theo image_id
    db_image = db.query(models.ImageMetadata).filter(models.ImageMetadata.id == image_id).first()
    if db_image is None:
        return None

    # Xóa file từ hệ thống (nếu có)
    file_path = Path(db_image.image_path)
    if file_path.exists():
        os.remove(file_path)

    # Xóa bản ghi trong cơ sở dữ liệu
    db.delete(db_image)
    db.commit()

    return db_image

def image_to_binary(image_path: str):
    try:
        full_image_path = Path(image_path)        
        if not full_image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image not found: {full_image_path}")
        
        with Image.open(full_image_path) as img:
            img = img.convert("RGB")  # Đảm bảo ảnh là RGB
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')  # Lưu ảnh vào bộ nhớ dưới dạng PNG
            return byte_arr.getvalue()  # Trả về dữ liệu nhị phân
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading image: {str(e)}")

def export_images_to_h5(db: Session):
    # Lấy tất cả dữ liệu từ cơ sở dữ liệu
    images = db.query(models.ImageMetadata).all()

    if not images:
        raise HTTPException(status_code=404, detail="No image data found")

    # Tạo file H5 trong bộ nhớ
    try:
        # Sử dụng BytesIO để tạo file trong bộ nhớ
        byte_io = io.BytesIO()

        with h5py.File(byte_io, "w") as hf:
            metadata_group = hf.create_group("metadata")
            images_group = hf.create_group("images")  # Group cho dữ liệu hình ảnh

            for i, image in enumerate(images):
                # Lưu dữ liệu ảnh dưới dạng nhị phân
                image_data = image_to_binary(image.image_path)

                # Lưu metadata của ảnh vào group "metadata"
                metadata_group.create_dataset(f"image_{image.id}_metadata", data={
                    'label': np.bytes_(image.label.encode()),  # Chuyển thành bytes
                    'image_metadata': np.bytes_(image.image_metadata.encode()),  # Chuyển thành bytes
                    'image_path': np.bytes_(image.image_path.encode()),  # Chuyển thành bytes
                    'created_at': np.bytes_(str(image.created_at).encode()),  # Sử dụng string thay vì bytes
                    'updated_at': np.bytes_(str(image.updated_at).encode())  # Sử dụng string thay vì bytes
                })

                # Lưu dữ liệu ảnh vào group "images"
                images_group.create_dataset(f"image_{image.id}", data=image_data)
        
        # Chuyển lại con trỏ của BytesIO về đầu file trước khi gửi
        byte_io.seek(0)
        
        # Trả về file HDF5 dưới dạng StreamingResponse để client có thể download
        return StreamingResponse(byte_io, media_type="application/x-hdf5", headers={"Content-Disposition": "attachment; filename=images_data.h5"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to HDF5: {str(e)}")