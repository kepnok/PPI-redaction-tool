import zipfile
import tempfile
import os
from pathlib import Path
from PIL import Image
import io

from presidio_image_redactor import ImageRedactorEngine

class ImageProcessor:
    """Processes images embedded in a docx file using presidio-image-redactor."""
    
    def __init__(self):
        self.engine = ImageRedactorEngine()

    def process_images_in_docx(self, docx_path: str):
        """Extracts images from a docx file, redacts them, and replaces them."""
        # A docx file is essentially a ZIP archive
        temp_dir = tempfile.mkdtemp()
        temp_docx = Path(temp_dir) / "temp.docx"
        
        with zipfile.ZipFile(docx_path, 'r') as zin:
            with zipfile.ZipFile(temp_docx, 'w') as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    
                    # Check if the file is an image in the media directory
                    if item.filename.startswith("word/media/") and item.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            # Load image from bytes
                            img = Image.open(io.BytesIO(data))
                            
                            # Redact image (draws black bars)
                            # Using default color (black)
                            redacted_img = self.engine.redact(img, (0, 0, 0))
                            
                            # Save back to bytes
                            img_byte_arr = io.BytesIO()
                            format = 'PNG' if item.filename.lower().endswith('.png') else 'JPEG'
                            redacted_img.save(img_byte_arr, format=format)
                            data = img_byte_arr.getvalue()
                        except Exception as e:
                            print(f"Failed to process image {item.filename}: {e}")
                    
                    # Write back to new zip (either original or redacted data)
                    zout.writestr(item, data)
                    
        # Replace original docx with the redacted one
        import shutil
        shutil.move(str(temp_docx), docx_path)
        shutil.rmtree(temp_dir)
