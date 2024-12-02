import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Table, Button, Form, Modal, Alert } from 'react-bootstrap';
import { IImage } from './dtos/ImageModel';
import ImageItem from './components/ImageItem';

const App: React.FC = () => {
  const [images, setImages] = useState<IImage[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [currentImage, setCurrentImage] = useState<IImage | null>(null);
  const [label, setLabel] = useState('');
  const [imageMetadata, setImageMetadata] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Hàm lấy dữ liệu từ API
  const fetchImages = async () => {
    try {
      const response = await axios.get('http://localhost:8000/image_metadata');
      setImages(response.data);  // Lưu danh sách ảnh vào state
    } catch (error) {
      console.error('Error fetching images:', error);
      alert('Failed to load images');
    }
  };

  // Hàm xóa ảnh khỏi danh sách
  const handleDeleteImage = async (id: number) => {
    try {
      const response = await axios.delete(`http://localhost:8000/image_metadata/${id}`);

      if (response.status === 200) {
        // Cập nhật lại danh sách sau khi xóa
        setImages(images.filter(image => image.id !== id));
      } else {
        alert('Failed to delete image');
      }
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('Error deleting image');
    }
  };

  // Hàm tạo ảnh mới
  const handleCreateImage = async () => {
    // Kiểm tra validation trước khi gửi
    if (!label || !imageMetadata) {
      setErrorMessage('Label and Metadata are required');  // Hiển thị lỗi nếu thiếu dữ liệu
      return;
    }

    const formData = new FormData();
    formData.append('file', imageFile!);
    formData.append('label', label);
    formData.append('image_metadata', imageMetadata);

    try {
      const response = await axios.post('http://localhost:8000/image_metadata', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 200) {
        await fetchImages();  // Lấy lại danh sách ảnh sau khi thêm mới
        setShowModal(false);  // Đóng modal
        clearForm();  // Xóa form input
      } else {
        alert('Failed to create image');
      }
    } catch (error) {
      console.error('Error creating image:', error);
      alert('Error creating image');
    }
  };

  // Hàm cập nhật ảnh (không upload ảnh mới, chỉ cập nhật label và metadata)
  const handleUpdateImage = async () => {
    // Kiểm tra validation trước khi gửi
    if (!label || !imageMetadata) {
      setErrorMessage('Label and Metadata are required');  // Hiển thị lỗi nếu thiếu dữ liệu
      return;
    }

    if (!currentImage) return;

    try {
      const response = await axios.put(
        `http://localhost:8000/image_metadata/${currentImage.id}`,
        {
          label: label,
          image_metadata: imageMetadata,  // Chỉ gửi label và metadata
        }
      );

      if (response.status === 200) {
        await fetchImages();  // Lấy lại danh sách ảnh sau khi cập nhật
        setShowModal(false);  // Đóng modal
        clearForm();  // Xóa form input
      } else {
        alert('Failed to update image');
      }
    } catch (error) {
      console.error('Error updating image:', error);
      alert('Error updating image');
    }
  };

  // Hàm mở modal để tạo hoặc cập nhật ảnh
  const openModalForCreate = () => {
    setCurrentImage(null);  // Reset ảnh hiện tại
    setLabel('');
    setImageMetadata('');
    setImageFile(null);
    setShowModal(true);
    setErrorMessage(null);  // Xóa thông báo lỗi
  };

  const openModalForEdit = (image: IImage) => {
    setCurrentImage(image);  // Chọn ảnh để sửa
    setLabel(image.label);
    setImageMetadata(image.image_metadata);
    setImageFile(null);  // Không cần upload lại ảnh
    setShowModal(true);
    setErrorMessage(null);  // Xóa thông báo lỗi
  };

  // Hàm đóng modal và xóa form
  const handleCloseModal = () => {
    setShowModal(false);
    clearForm();
    setErrorMessage(null);  // Xóa thông báo lỗi khi đóng modal
  };

  const clearForm = () => {
    setLabel('');
    setImageMetadata('');
    setImageFile(null);
  };

  const exportDataH5 = async () => {
    try {
      const response = await axios.get('http://localhost:8000/image_metadata_export_h5', {
        responseType: 'blob',  // Đảm bảo nhận blob dữ liệu từ API
      });

      // Tạo URL từ dữ liệu blob
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'images_metadata_with_images.h5'); // Đặt tên file
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Failed to export data');
    }
  };

  // Lấy dữ liệu khi component được mount
  useEffect(() => {
    fetchImages();
  }, []);  // Chỉ gọi 1 lần khi component được render lần đầu

  return (
    <div className="container">
      <h1>Image Metadata</h1>
      <div className="mb-3">
        <Button variant="primary" onClick={openModalForCreate}>Add New Image</Button>
        <Button variant="secondary" className="ml-3" onClick={exportDataH5}>Export All</Button>
      </div>
      <Table striped bordered hover>
        <thead>
        <tr>
          <th>Image</th>
          <th>Label</th>
          <th>Metadata</th>
          <th>Image Path</th>
          <th>Created At</th>
          <th>Updated At</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        {images.map(image => (
          <ImageItem
            key={image.id}
            image={image}
            onDelete={handleDeleteImage}
            onEdit={() => openModalForEdit(image)}
          />
        ))}
        </tbody>
      </Table>

      {/* Modal tạo mới hoặc cập nhật ảnh */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{currentImage ? 'Edit Image' : 'Create New Image'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group controlId="formLabel">
              <Form.Label>Label</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                isInvalid={!!errorMessage}
              />
            </Form.Group>

            <Form.Group controlId="formMetadata">
              <Form.Label>Metadata</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter metadata"
                value={imageMetadata}
                onChange={(e) => setImageMetadata(e.target.value)}
                isInvalid={!!errorMessage}
              />
            </Form.Group>

            {/* Bỏ trường chọn ảnh nếu đang edit */}
            {!currentImage && (
              <Form.Group controlId="formFile">
                <Form.Label>Image File</Form.Label>
                <Form.Control
                  type="file"
                  onChange={(e) => setImageFile((e.target as HTMLInputElement).files?.[0] ?? null)}
                />
              </Form.Group>
            )}

            {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Close
          </Button>
          <Button
            variant="primary"
            onClick={currentImage ? handleUpdateImage : handleCreateImage}
          >
            {currentImage ? 'Update' : 'Create'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default App;
