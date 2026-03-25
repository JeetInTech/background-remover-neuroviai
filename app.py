import io
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from rembg import remove, new_session
from PIL import Image, ImageOps
import numpy as np

logger = logging.getLogger(__name__)

app = FastAPI(title="Neuroviai Bg Remover")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Pre-load sessions for different models (better quality options)
MODELS = {
    "isnet-general-use": "Best quality - General purpose (recommended)",
    "u2net": "High quality - General objects",
    "u2net_human_seg": "Optimized for humans/portraits",
    "silueta": "Fast processing - Good quality",
    "isnet-anime": "Optimized for anime/illustrations",
}

# Cache sessions for performance
_sessions = {}

def get_session(model_name: str):
    """Get or create a rembg session for the specified model."""
    if model_name not in _sessions:
        _sessions[model_name] = new_session(model_name)
    return _sessions[model_name]


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("templates/index.html").read_text(encoding="utf-8")


@app.get("/models")
async def get_models():
    """Return available models for the frontend."""
    return MODELS


@app.post("/remove-bg")
async def remove_background(request: Request):
    """
    Remove background from image with full resolution preservation.
    
    - model: AI model to use for segmentation
    - alpha_matting: Enable for better edge refinement (hair, fur, etc.)
    - post_process_mask: Clean up the mask edges
    - bg_color: Optional replacement background color (hex), None for transparent
    """
    try:
        try:
            form = await request.form()
        except Exception as e:
            logger.error(f"Form parsing error: {e}")
            raise HTTPException(status_code=400, detail=f"Form parsing error: {str(e)[:100]}")

        # Extract file
        file = form.get("file")
        if file is None:
            logger.error(f"No file in form. Available keys: {list(form.keys())}")
            raise HTTPException(status_code=400, detail="No file uploaded")

        input_bytes = await file.read()
        if not input_bytes:
            logger.error("Uploaded file is empty")
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        logger.info(f"Received file: {file.filename}, size: {len(input_bytes)} bytes, first bytes: {input_bytes[:20].hex()}")
        
        # Convert image to PNG if needed (for AVIF, WebP, etc.)
        try:
            input_image_temp = Image.open(io.BytesIO(input_bytes))
            # If successful, convert to PNG for rembg
            if input_image_temp.format and input_image_temp.format.upper() not in ('PNG', 'JPEG', 'JPG'):
                logger.info(f"Converting {input_image_temp.format} to PNG for processing")
                png_buffer = io.BytesIO()
                input_image_temp.convert('RGB').save(png_buffer, format='PNG')
                input_bytes = png_buffer.getvalue()
                logger.info(f"Converted to PNG: {len(input_bytes)} bytes")
        except Exception as convert_err:
            logger.warning(f"Could not detect format for conversion: {convert_err}")

        # Extract form fields with defaults
        try:
            model = form.get("model", "isnet-general-use")
            alpha_matting = str(form.get("alpha_matting", "false")).lower() in ("true", "1", "yes")
            alpha_matting_foreground_threshold = int(form.get("alpha_matting_foreground_threshold", 240))
            alpha_matting_background_threshold = int(form.get("alpha_matting_background_threshold", 10))
            alpha_matting_erode_size = int(form.get("alpha_matting_erode_size", 10))
            post_process_mask = str(form.get("post_process_mask", "true")).lower() in ("true", "1", "yes")
            bg_color = form.get("bg_color", None)
            logger.info(f"Form params - model: {model}, alpha_matting: {alpha_matting}")
        except Exception as e:
            logger.error(f"Error parsing form fields: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid form fields: {str(e)[:100]}")

        # Open with PIL to get original properties
        try:
            input_image = Image.open(io.BytesIO(input_bytes))
        except Exception as e:
            logger.error(f"Invalid image file: {e}")
            logger.error(f"Image bytes info - total: {len(input_bytes)} bytes, first 20 bytes (hex): {input_bytes[:20].hex()}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        input_image = ImageOps.exif_transpose(input_image)
        original_size = input_image.size  # (width, height)
        original_mode = input_image.mode
        
        # Get ICC profile if present (for color accuracy)
        icc_profile = input_image.info.get('icc_profile')
        
        # Get EXIF data if present
        exif_data = input_image.info.get('exif')

        # Validate model selection
        if model not in MODELS:
            model = "isnet-general-use"
        
        # Get the session for selected model
        session = get_session(model)

        # Remove background with enhanced settings; fall back to no alpha matting if pymatting fails
        try:
            logger.info(f"Processing image with model: {model}, alpha_matting: {alpha_matting}")
            output_bytes = remove(
                input_bytes,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size,
                post_process_mask=post_process_mask,
            )
            logger.info(f"Background removal successful. Output size: {len(output_bytes)} bytes")
        except Exception as e:
            # pymatting can fail on certain images (Cholesky decomposition) — retry without it
            logger.warning(f"Alpha matting failed: {e}. Retrying without alpha matting...")
            try:
                output_bytes = remove(
                    input_bytes,
                    session=session,
                    alpha_matting=False,
                    post_process_mask=post_process_mask,
                )
                logger.info("Retry successful")
            except Exception as retry_error:
                logger.error(f"Background removal failed completely: {retry_error}")
                raise HTTPException(status_code=500, detail=f"Background removal failed: {str(retry_error)[:100]}")

        # Re-open result
        output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        
        # Ensure exact original resolution is preserved
        if output_image.size != original_size:
            output_image = output_image.resize(original_size, Image.LANCZOS)

        # Apply background color if specified
        if bg_color:
            try:
                # Parse hex color
                bg_color = bg_color.lstrip('#')
                r, g, b = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
                
                # Create background layer
                background = Image.new('RGBA', original_size, (r, g, b, 255))
                background.paste(output_image, (0, 0), output_image)
                output_image = background.convert('RGB')
                output_format = "PNG"
                media_type = "image/png"
            except Exception as color_err:
                logger.warning(f"Invalid background color {bg_color}: {color_err}")
                # Keep transparent
        
        output_format = "PNG"
        media_type = "image/png"

        # Optimize the output
        output_buffer = io.BytesIO()
        
        # Save with optimization - preserve quality while minimizing file size
        save_kwargs = {
            "format": output_format,
            "optimize": True,
        }
        
        # Preserve ICC profile for color accuracy
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        
        output_image.save(output_buffer, **save_kwargs)
        output_buffer.seek(0)
        
        # Calculate compression info
        original_size_bytes = len(input_bytes)
        output_size_bytes = output_buffer.getbuffer().nbytes
        
        # Return as streaming response with size headers
        return StreamingResponse(
            output_buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": "attachment; filename=neuroviai-nobg.png",
                "X-Original-Size": str(original_size_bytes),
                "X-Output-Size": str(output_size_bytes),
                "X-Resolution": f"{original_size[0]}x{original_size[1]}",
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected error
        logger.exception(f"Unexpected error in /remove-bg endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:100]}")


@app.post("/remove-bg-webp")
async def remove_background_webp(request: Request):
    """
    Remove background and return as WebP (smaller file size, supports transparency).
    """
    try:
        form = await request.form()

        file = form.get("file")
        if file is None:
            raise HTTPException(status_code=400, detail="No file uploaded")

        input_bytes = await file.read()
        if not input_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        model = form.get("model", "isnet-general-use")
        alpha_matting = str(form.get("alpha_matting", "false")).lower() in ("true", "1", "yes")
        quality = int(form.get("quality", 95))
        logger.info(f"WebP: Received file: {file.filename}, size: {len(input_bytes)} bytes")
        
        # Convert image to PNG if needed (for AVIF, WebP, etc.)
        try:
            input_image_temp = Image.open(io.BytesIO(input_bytes))
            if input_image_temp.format and input_image_temp.format.upper() not in ('PNG', 'JPEG', 'JPG'):
                logger.info(f"WebP: Converting {input_image_temp.format} to PNG")
                png_buffer = io.BytesIO()
                input_image_temp.convert('RGB').save(png_buffer, format='PNG')
                input_bytes = png_buffer.getvalue()
        except Exception as convert_err:
            logger.warning(f"WebP: Could not convert format: {convert_err}")

        try:
            input_image = Image.open(io.BytesIO(input_bytes))
        except Exception as e:
            logger.error(f"WebP: Invalid image file: {e}")
            logger.error(f"WebP: Image bytes info - total: {len(input_bytes)} bytes, first 20 bytes (hex): {input_bytes[:20].hex()}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        input_image = ImageOps.exif_transpose(input_image)
        original_size = input_image.size

        if model not in MODELS:
            model = "isnet-general-use"
        
        session = get_session(model)

        try:
            logger.info(f"Processing WebP with model: {model}")
            output_bytes = remove(
                input_bytes,
                session=session,
                alpha_matting=alpha_matting,
                post_process_mask=True,
            )
            logger.info("WebP background removal successful")
        except Exception as e:
            logger.warning(f"WebP alpha matting failed: {e}. Retrying without alpha matting...")
            try:
                output_bytes = remove(
                    input_bytes,
                    session=session,
                    alpha_matting=False,
                    post_process_mask=True,
                )
                logger.info("WebP retry successful")
            except Exception as retry_error:
                logger.error(f"WebP background removal failed: {retry_error}")
                raise HTTPException(status_code=500, detail=f"Background removal failed: {str(retry_error)[:100]}")

        output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        
        if output_image.size != original_size:
            output_image = output_image.resize(original_size, Image.LANCZOS)

        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="WEBP", quality=quality, lossless=False)
        output_buffer.seek(0)

        return StreamingResponse(
            output_buffer,
            media_type="image/webp",
            headers={
                "Content-Disposition": "attachment; filename=neuroviai-nobg.webp",
                "X-Resolution": f"{original_size[0]}x{original_size[1]}",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in /remove-bg-webp endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:100]}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
