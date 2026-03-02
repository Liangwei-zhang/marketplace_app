import os
import asyncio
import aiofiles
from typing import List, Optional
from PIL import Image, ImageOps
from app.core.config import settings
from app.services.storage import storage


class ImageService:
    """Image processing service with compression, thumbnails, and WebP conversion"""
    
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    def convert_to_webp(self, input_path: str, output_path: str, quality: int = 80) -> str:
        """Convert image to WebP format with compression."""
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Resize if too large
            max_width = settings.COMPRESSED_MAX_WIDTH
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as WebP
            img.save(output_path, "WEBP", quality=quality, method=6)
        
        return output_path
    
    def compress_image(self, input_path: str, output_path: str) -> str:
        """Compress image as JPEG."""
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            if img.width > settings.COMPRESSED_MAX_WIDTH:
                ratio = settings.COMPRESSED_MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((settings.COMPRESSED_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            img.save(output_path, "JPEG", quality=settings.COMPRESSED_QUALITY, optimize=True)
        
        return output_path
    
    def create_thumbnail(self, input_path: str, output_path: str, size: tuple = (200, 200)) -> str:
        """Create square thumbnail with center crop."""
        with Image.open(input_path) as img:
            # Convert to RGB
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Create square thumbnail with center crop
            img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            img.save(output_path, "JPEG", quality=70, optimize=True)
        
        return output_path
    
    async def process_upload(self, file, user_id: int) -> dict:
        """
        Process uploaded image: convert to WebP, create thumbnail.
        Returns dict with filenames for original/compressed and thumbnail.
        """
        # Read file content
        content = await file.read()
        
        # Generate filenames
        timestamp = int(asyncio.get_event_loop().time() * 1000)
        filename = f"{user_id}_{timestamp}"
        
        # Determine format
        ext = "jpg"
        if file.filename:
            original_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
            if original_ext in settings.ALLOWED_EXTENSIONS:
                ext = original_ext
        
        # Save temp file
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{filename}.{ext}")
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        # Process images
        webp_filename = f"{filename}.webp"
        thumb_filename = f"{filename}_thumb.webp"
        
        compressed_path = os.path.join(settings.UPLOAD_DIR, webp_filename)
        thumb_path = os.path.join(settings.UPLOAD_DIR, thumb_filename)
        
        # Convert to WebP (compressed)
        try:
            self.convert_to_webp(temp_path, compressed_path)
        except Exception:
            # Fallback to JPEG if WebP fails
            compressed_path = os.path.join(settings.UPLOAD_DIR, f"{filename}.jpg")
            self.compress_image(temp_path, compressed_path)
            webp_filename = f"{filename}.jpg"
        
        # Create thumbnail
        try:
            self.convert_to_webp(temp_path, thumb_path, quality=60)
        except Exception:
            # Fallback to JPEG thumbnail
            thumb_path = os.path.join(settings.UPLOAD_DIR, f"{filename}_thumb.jpg")
            self.create_thumbnail(temp_path, thumb_path)
            thumb_filename = f"{filename}_thumb.jpg"
        
        # Clean temp
        os.remove(temp_path)
        
        # Upload to S3 if enabled
        if storage.use_s3:
            # Read compressed file and upload
            async with aiofiles.open(compressed_path, 'rb') as f:
                await storage.upload_file(await f.read(), webp_filename, "uploads")
            
            async with aiofiles.open(thumb_path, 'rb') as f:
                await storage.upload_file(await f.read(), thumb_filename, "uploads")
            
            # Clean local files
            os.remove(compressed_path)
            os.remove(thumb_path)
            
            return {
                "image": webp_filename,
                "thumbnail": thumb_filename,
                "url": storage.get_image_url(webp_filename),
                "thumb_url": storage.get_thumbnail_url(thumb_filename)
            }
        
        return {
            "image": webp_filename,
            "thumbnail": thumb_filename,
            "url": f"/uploads/{webp_filename}",
            "thumb_url": f"/uploads/{thumb_filename}"
        }
    
    async def process_uploads(self, files: List, user_id: int) -> List[dict]:
        """Process multiple uploaded images concurrently."""
        tasks = [self.process_upload(file, user_id) for file in files if file.filename]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    def delete_image(self, filename: str) -> bool:
        """Delete image and its thumbnail."""
        try:
            storage.delete_file(filename)
            
            # Also delete thumbnail
            if filename.endswith('.webp'):
                thumb = filename.replace('.webp', '_thumb.webp')
            elif filename.endswith('.jpg'):
                thumb = filename.replace('.jpg', '_thumb.jpg')
            else:
                thumb = f"thumb_{filename}"
            
            storage.delete_file(thumb)
            return True
        except Exception:
            return False
    
    def get_image_url(self, filename: str) -> str:
        """Get full URL for image."""
        return storage.get_image_url(filename)
    
    def get_thumbnail_url(self, filename: str) -> str:
        """Get thumbnail URL for image."""
        if storage.use_s3:
            return f"{storage.public_url}/uploads/thumb_{filename}"
        return f"/uploads/thumb_{filename}"


image_service = ImageService()
