"""Quick test: hit the running server with a real image upload."""
import urllib.request, io
from PIL import Image

# Create a test PNG in memory
img = Image.new("RGB", (200, 200), "red")
buf = io.BytesIO()
img.save(buf, format="PNG")
png = buf.getvalue()
print(f"Test image size: {len(png)} bytes")

# Build a proper multipart/form-data body
boundary = b"----TestBoundary123"
parts = []
# file part
parts.append(
    b"------TestBoundary123\r\n"
    b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + png
)
# model part
parts.append(
    b"------TestBoundary123\r\n"
    b'Content-Disposition: form-data; name="model"\r\n\r\n'
    b"isnet-general-use"
)
body = b"\r\n".join(parts) + b"\r\n------TestBoundary123--\r\n"

req = urllib.request.Request(
    "http://127.0.0.1:8000/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----TestBoundary123"},
)

try:
    res = urllib.request.urlopen(req, timeout=30)
    print(f"SUCCESS — status {res.status}, response {len(res.read())} bytes")
except urllib.error.HTTPError as e:
    print(f"FAILED — status {e.code}")
    print(e.read().decode(errors="replace")[:500])
except Exception as e:
    print(f"ERROR — {e}")
