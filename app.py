import io
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from rembg import remove, new_session
from PIL import Image
import numpy as np

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
async def remove_background(
    file: UploadFile = File(...),
    model: str = Form(default="isnet-general-use"),
    alpha_matting: bool = Form(default=False),
    alpha_matting_foreground_threshold: int = Form(default=240),
    alpha_matting_background_threshold: int = Form(default=10),
    alpha_matting_erode_size: int = Form(default=10),
    post_process_mask: bool = Form(default=True),
    bg_color: Optional[str] = Form(default=None),  # Optional: hex color like "#ffffff"
):
    """
    Remove background from image with full resolution preservation.
    
    - model: AI model to use for segmentation
    - alpha_matting: Enable for better edge refinement (hair, fur, etc.)
    - post_process_mask: Clean up the mask edges
    - bg_color: Optional replacement background color (hex), None for transparent
    """
    input_bytes = await file.read()

    # Open with PIL to get original properties
    input_image = Image.open(io.BytesIO(input_bytes))
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
        output_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size,
            post_process_mask=post_process_mask,
        )
    except Exception:
        # pymatting can fail on certain images (Cholesky decomposition) — retry without it
        output_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=False,
            post_process_mask=post_process_mask,
        )

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
        except:
            pass  # Invalid color, keep transparent
    
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


@app.post("/remove-bg-webp")
async def remove_background_webp(
    file: UploadFile = File(...),
    model: str = Form(default="isnet-general-use"),
    alpha_matting: bool = Form(default=False),
    quality: int = Form(default=95),
):
    """
    Remove background and return as WebP (smaller file size, supports transparency).
    """
    input_bytes = await file.read()
    input_image = Image.open(io.BytesIO(input_bytes))
    original_size = input_image.size

    if model not in MODELS:
        model = "isnet-general-use"
    
    session = get_session(model)

    try:
        output_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=alpha_matting,
            post_process_mask=True,
        )
    except Exception:
        output_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=False,
            post_process_mask=True,
        )

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
