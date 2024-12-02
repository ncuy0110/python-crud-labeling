from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from . import models
from sqlalchemy import update
import os
from pathlib import Path
import h5py
from PIL import Image
import io
from fastapi import HTTPException
import json
import numpy as np
import base64


# Thêm mới dữ liệu vào bảng image_metadata
def create_image_metadata(
    db: Session, image_path: str, label: str, image_metadata: str
):
    db_image = models.ImageMetadata(
        image_path=image_path, label=label, image_metadata=image_metadata
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


# Lấy tất cả thông tin từ bảng image_metadata
def get_all_image_metadata(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.ImageMetadata).offset(skip).limit(limit).all()


# Cập nhật thông tin của ảnh (chỉ label và metadata)
def update_image_metadata(
    db: Session, image_id: int, label: str = None, image_metadata: str = None
):
    # Tìm ảnh theo image_id
    db_image = (
        db.query(models.ImageMetadata)
        .filter(models.ImageMetadata.id == image_id)
        .first()
    )
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
    db_image = (
        db.query(models.ImageMetadata)
        .filter(models.ImageMetadata.id == image_id)
        .first()
    )
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


def image_to_base64(image_path: str):
    try:
        with open(image_path, "rb") as image_file:
            # Read the image as a binary file
            image_binary = image_file.read()
            # Encode the binary image as base64
            encoded_image = base64.b64encode(image_binary).decode("utf-8")
            return encoded_image
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
            image_data = []

            for image in images:
                # Lưu dữ liệu ảnh dưới dạng nhị phân
                image_data.append(
                    {
                        "id": image.id,
                        "image_path": image.image_path,
                        "label": image.label,
                        "image_metadata": image.image_metadata,
                        "created_at": str(image.created_at),
                        "updated_at": str(image.updated_at),
                        "image_content": image_to_base64(image.image_path),
                    }
                )
            hf.create_dataset(
                "my_objects",
                data=json.dumps(image_data).encode("utf-8"),
                dtype=h5py.string_dtype(),
            )

        # Chuyển lại con trỏ của BytesIO về đầu file trước khi gửi
        byte_io.seek(0)

        # Trả về file HDF5 dưới dạng StreamingResponse để client có thể download
        return StreamingResponse(
            byte_io,
            media_type="application/x-hdf5",
            headers={"Content-Disposition": "attachment; filename=images_data.h5"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting to HDF5: {str(e)}"
        )
