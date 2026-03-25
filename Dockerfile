FROM python:3.11-slim

LABEL maintainer="Neuroviai"
LABEL description="Neuroviai Bg Remover - AI-Powered Background Removal with auto image format conversion"

WORKDIR /app

# Install system deps needed by onnxruntime / Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the best quality model so first request is fast
# This can take 5-10 minutes but only happens once during image build
RUN python -c "from rembg import new_session; new_session('isnet-general-use')" || echo "Model pre-download skipped (will download on first request)"

EXPOSE 8000 8001

# Use run_app.py for automatic port management and fallback
CMD ["python", "run_app.py"]
