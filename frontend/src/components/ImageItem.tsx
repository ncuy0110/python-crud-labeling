import React from 'react';
import { Button } from 'react-bootstrap';
import { IImage } from "../dtos/ImageModel";

interface ImageItemProps {
  image: IImage;
  onDelete: (image: IImage) => void;
  onEdit: (image: IImage) => void;
}

const ImageItem: React.FC<ImageItemProps> = ({ image, onDelete, onEdit }) => {
  return (
    <tr>
      <td>
        <img src={`http://localhost:8000/image_metadata/${image.id}`} alt={image.label} width={50} />
      </td>
      <td>{image.label}</td>
      <td>{image.image_metadata}</td>
      <td>{image.image_path}</td>
      <td>{image.created_at}</td>
      <td>{image.updated_at}</td>
      <td>
        <Button variant="warning" onClick={() => onEdit(image)}>
          Edit
        </Button>
        <Button variant="danger" onClick={() => onDelete(image)}>
          Delete
        </Button>
      </td>
    </tr>
  );
};

export default ImageItem;
