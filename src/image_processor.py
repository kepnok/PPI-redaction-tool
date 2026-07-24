import shutil
import zipfile
import tempfile
import os
from pathlib import Path
from PIL import Image, ImageDraw
import io
import cv2
import numpy as np

from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine

class ImageProcessor:
    """Processes images embedded in a docx file using presidio-image-redactor and OpenCV."""
    
    def __init__(self, analyzer_engine=None):
        if analyzer_engine:
            # Inject our custom text analyzer into the image redactor
            image_analyzer = ImageAnalyzerEngine(analyzer_engine=analyzer_engine)
            self.engine = ImageRedactorEngine(image_analyzer_engine=image_analyzer)
        else:
            self.engine = ImageRedactorEngine()
            
        # Initialize OpenCV Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def redact_faces(self, img: Image.Image) -> Image.Image:
        """Detects faces using OpenCV and draws black bounding boxes over them."""
        # Convert PIL image to numpy array for OpenCV
        img_np = np.array(img)
        
        # Convert to grayscale for face detection
        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        elif len(img_np.shape) == 3 and img_np.shape[2] == 4:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY)
        else:
            gray = img_np
            
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Draw black boxes over detected faces
        if len(faces) > 0:
            draw = ImageDraw.Draw(img)
            for (x, y, w, h) in faces:
                # Add a 10% padding around the detected face
                pad_x = int(w * 0.1)
                pad_y = int(h * 0.1)
                draw.rectangle(
                    [x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y],
                    fill="black"
                )
                
        return img

    def process_images_in_docx(self, docx_path: str):
        """Extracts images from a docx file, redacts faces/text, and replaces them."""
        temp_dir = tempfile.mkdtemp()
        temp_docx = Path(temp_dir) / "temp.docx"
        
        with zipfile.ZipFile(docx_path, 'r') as zin:
            with zipfile.ZipFile(temp_docx, 'w') as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    
                    if item.filename.startswith("word/media/") and item.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            img = Image.open(io.BytesIO(data))
                            
                            img = self.redact_faces(img)
                            
                            redacted_img = self.engine.redact(img, (0, 0, 0))
                            
                            img_byte_arr = io.BytesIO()
                            format = 'PNG' if item.filename.lower().endswith('.png') else 'JPEG'
                            redacted_img.save(img_byte_arr, format=format)
                            data = img_byte_arr.getvalue()
                        except Exception as e:
                            print(f"Failed to process image {item.filename}: {e}")
                    
                    zout.writestr(item, data)
                    
        shutil.move(str(temp_docx), docx_path)
        shutil.rmtree(temp_dir)
