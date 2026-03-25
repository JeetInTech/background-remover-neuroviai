"""Test the API with detailed error reporting."""
import urllib.request
import json
import io
from PIL import Image

# Create a test PNG
img = Image.new("RGB", (200, 200), "red")
buf = io.BytesIO()
img.save(buf, format="PNG")
png = buf.getvalue()

# Test 1: Normal request with all fields
print("Test 1: Normal request with all form fields")
boundary = b"----TestBoundary123"
parts = []
parts.append(
    b"------TestBoundary123\r\n"
    b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + png
)
parts.append(
    b"------TestBoundary123\r\n"
    b'Content-Disposition: form-data; name="model"\r\n\r\n'
    b"isnet-general-use"
)
parts.append(
    b"------TestBoundary123\r\n"
    b'Content-Disposition: form-data; name="alpha_matting"\r\n\r\n'
    b"false"
)
body = b"\r\n".join(parts) + b"\r\n------TestBoundary123--\r\n"

req = urllib.request.Request(
    "http://127.0.0.1:8000/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----TestBoundary123"},
)

try:
    res = urllib.request.urlopen(req, timeout=60)
    print(f"✓ SUCCESS — status {res.status}")
except urllib.error.HTTPError as e:
    print(f"✗ FAILED — status {e.code}")
    try:
        error_data = json.loads(e.read())
        print(f"Error: {json.dumps(error_data, indent=2)}")
    except:
        print(e.read().decode(errors="replace")[:500])
except Exception as e:
    print(f"✗ ERROR — {e}")

print("\n" + "="*60 + "\n")

# Test 2: Minimal request (no optional fields)
print("Test 2: Minimal request (only file)")
boundary = b"----TestBoundary456"
body = (
    b"------TestBoundary456\r\n"
    b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + png +
    b"\r\n------TestBoundary456--\r\n"
)

req = urllib.request.Request(
    "http://127.0.0.1:8000/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----TestBoundary456"},
)

try:
    res = urllib.request.urlopen(req, timeout=60)
    print(f"✓ SUCCESS — status {res.status}")
except urllib.error.HTTPError as e:
    print(f"✗ FAILED — status {e.code}")
    try:
        error_data = json.loads(e.read())
        print(f"Error: {json.dumps(error_data, indent=2)}")
    except:
        print(e.read().decode(errors="replace")[:500])
except Exception as e:
    print(f"✗ ERROR — {e}")

print("\nDone!")
