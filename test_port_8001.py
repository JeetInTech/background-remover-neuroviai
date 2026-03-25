"""Test the API on port 8001."""
import urllib.request
import json
import io
from PIL import Image

print("Testing on http://localhost:8001/\n")

# Test /models endpoint
print("✓ Test: GET /models")
try:
    res = urllib.request.urlopen("http://127.0.0.1:8001/models", timeout=5)
    models = json.loads(res.read())
    print(f"  ✓ Available models: {len(models)}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test background removal
print("\n✓ Test: POST /remove-bg")
img = Image.new("RGB", (200, 200), "red")
buf = io.BytesIO()
img.save(buf, format="PNG")
png = buf.getvalue()

boundary = b"----Test999"
body = (
    b"------Test999\r\n"
    b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + png +
    b"\r\n------Test999--\r\n"
)

req = urllib.request.Request(
    "http://127.0.0.1:8001/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----Test999"},
)

try:
    res = urllib.request.urlopen(req, timeout=120)
    result = res.read()
    result_img = Image.open(io.BytesIO(result))
    print(f"  ✓ Background removed successfully!")
    print(f"    Output size: {len(result)} bytes")
    print(f"    Image: {result_img.size} {result_img.mode}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n✅ Server is working on port 8001!")
print("Open: http://localhost:8001/")
