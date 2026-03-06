FROM python:3.11-slim

LABEL maintainer="Neuroviai"
LABEL description="Neuroviai Bg Remover - AI-Powered Background Removal"

WORKDIR /app

# Install system deps needed by onnxruntime / Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the best quality model so first request is fast
RUN python -c "from rembg import new_session; new_session('isnet-general-use')"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
