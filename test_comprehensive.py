"""Comprehensive test of the API endpoints."""
import urllib.request
import json
import io
from PIL import Image

print("="*60)
print("BACKGROUND REMOVER API TEST SUITE")
print("="*60)

# Test 1: Check /models endpoint
print("\n✓ Test 1: GET /models")
try:
    res = urllib.request.urlopen("http://127.0.0.1:8000/models", timeout=5)
    models = json.loads(res.read())
    print(f"  Available models: {len(models)}")
    for model, desc in models.items():
        print(f"    - {model}: {desc}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 2: Test with different image types
print("\n✓ Test 2: Process RED image")
img = Image.new("RGB", (300, 300), "red")
buf = io.BytesIO()
img.save(buf, format="PNG")
red_png = buf.getvalue()

boundary = b"----Test123"
body = (
    b"------Test123\r\n"
    b'Content-Disposition: form-data; name="file"; filename="red.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + red_png +
    b"\r\n------Test123\r\n"
    b'Content-Disposition: form-data; name="model"\r\n\r\n'
    b"isnet-general-use\r\n"
    b"------Test123--\r\n"
)

req = urllib.request.Request(
    "http://127.0.0.1:8000/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----Test123"},
)

try:
    res = urllib.request.urlopen(req, timeout=120)
    result = res.read()
    result_img = Image.open(io.BytesIO(result))
    print(f"  ✓ Response: {len(result)} bytes, {result_img.size}, {result_img.mode}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 3: Test with solid BLUE image (should produce transparent output)
print("\n✓ Test 3: Process BLUE image")
img = Image.new("RGB", (200, 200), "blue")
buf = io.BytesIO()
img.save(buf, format="PNG")
blue_png = buf.getvalue()

body = (
    b"------Test789\r\n"
    b'Content-Disposition: form-data; name="file"; filename="blue.png"\r\n'
    b"Content-Type: image/png\r\n\r\n" + blue_png +
    b"\r\n------Test789\r\n"
    b'Content-Disposition: form-data; name="model"\r\n\r\n'
    b"u2net\r\n"
    b"------Test789\r\n"
    b'Content-Disposition: form-data; name="alpha_matting"\r\n\r\n'
    b"true\r\n"
    b"------Test789--\r\n"
)

req = urllib.request.Request(
    "http://127.0.0.1:8000/remove-bg",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----Test789"},
)

try:
    res = urllib.request.urlopen(req, timeout=120)
    result = res.read()
    result_img = Image.open(io.BytesIO(result))
    alpha = result_img.split()[-1]
    alpha_data = alpha.getextrema()
    print(f"  ✓ Response: {len(result)} bytes")
    print(f"    Image size: {result_img.size}, mode: {result_img.mode}")
    print(f"    Alpha channel range: {alpha_data} (0=transparent, 255=opaque)")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
