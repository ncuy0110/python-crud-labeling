from fastapi import FastAPI, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from . import crud, models, database, schemas
from pathlib import Path
from .database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import logging

logger = logging.getLogger("uvicorn.access")

# Khởi tạo ứng dụng FastAPI
app = FastAPI(debug = True)

# Cấu hình CORS
origins = [
    "http://localhost:5173",  # React frontend đang chạy trên port 5173
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Cho phép các domain từ `origins` truy cập
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],  # Cho phép tất cả các headers
)

def get_db():
    db = SessionLocal()
    try : 
        yield db
    finally:
        db.close()

# Tạo bảng trong cơ sở dữ liệu nếu chưa có
models.Base.metadata.create_all(bind=database.engine)

# Đảm bảo thư mục images tồn tại
UPLOAD_FOLDER = Path("app/images")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@app.post("/image_metadata/", response_model=schemas.ImageMetadataResponse)
async def upload_image(
    file: UploadFile = File(...),  
    label: str = Form(...),        
    image_metadata: str = Form(...),  
    db: Session = Depends(get_db)
):
    # Kiểm tra định dạng ảnh
    if not file.content_type.startswith("image"):
        raise HTTPException(status_code=400, detail="File phải là ảnh")

    # Lưu ảnh vào thư mục images
    file_location = UPLOAD_FOLDER / file.filename
    with open(file_location, "wb") as image_file:
        image_file.write(await file.read())

    # Tạo mới bản ghi trong cơ sở dữ liệu
    db_image = crud.create_image_metadata(
        db=db,
        image_path=file_location,
        label=label,
        image_metadata=image_metadata
    )

    return db_image

# API để lấy danh sách image metadata
@app.get("/image_metadata/")
def get_image_metadata(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_all_image_metadata(db=db, skip=skip, limit=limit)

@app.put("/image_metadata/{image_id}")
async def update_image(image_id: int, request: schemas.ImageMetadataUpdate, db: Session = Depends(get_db)):
    updated_image = crud.update_image_metadata(db=db, image_id=image_id, label=request.label, image_metadata=request.image_metadata)
    if updated_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image updated successfully", "data": updated_image}


@app.delete("/image_metadata/{image_id}")
async def delete_file(image_id: int, db: Session = Depends(get_db)):
    deleted_image = crud.delete_image_metadata(db=db, image_id=image_id)
    if deleted_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    file_path = Path(deleted_image.image_path)
    if file_path.exists():
        os.remove(file_path)
    return {"message": "Image and record deleted successfully", "image_id": deleted_image.id}

@app.get("/image_metadata/{image_id}")
async def get_image(image_id: int, db: Session = Depends(get_db)):
    # Truy vấn thông tin ảnh từ database theo ID
    image_metadata = db.query(models.ImageMetadata).filter(models.ImageMetadata.id == image_id).first()
    
    if not image_metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = image_metadata.image_path  # Đường dẫn ảnh lưu trong DB
    image_file_path = Path(image_path)  # Chuyển đổi sang Path object
    
    # Kiểm tra xem ảnh có tồn tại không
    if not image_file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    # Trả về ảnh cho client
    return FileResponse(image_file_path)

@app.get("/image_metadata_export_h5")
def export_images_h5(db: Session = Depends(get_db)):
    logging.debug("test")
    return crud.export_images_to_h5(db)