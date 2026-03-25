"""Test with better multipart handling."""
import urllib.request
import io
from PIL import Image

# Create a test image
img = Image.new("RGB", (100, 100), color='red')
buf = io.BytesIO()
img.save(buf, format="PNG")
image_bytes = buf.getvalue()

print(f"Image size: {len(image_bytes)} bytes")
print(f"First 20 bytes (hex): {image_bytes[:20].hex()}")
print(f"PNG header should start with: 89504e47 (PNG magic)")

# Create multipart form data manually
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = bytearray()

# Add file field
body.extend(f'--{boundary}\r\n'.encode())
body.extend(b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n')
body.extend(b'Content-Type: image/png\r\n\r\n')
body.extend(image_bytes)
body.extend(b'\r\n')

# Add model field
body.extend(f'--{boundary}\r\n'.encode())
body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
body.extend(b'isnet-general-use\r\n')

# Closing boundary
body.extend(f'--{boundary}--\r\n'.encode())

print(f"\nForm data size: {len(body)} bytes")
print(f"Form data first 100 bytes:\n{body[:100]}\n")

# Send the request
url = "http://127.0.0.1:8001/remove-bg"
req = urllib.request.Request(
    url,
    data=bytes(body),
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "TestClient/1.0"
    },
    method="POST"
)

print(f"Sending to {url}...")
try:
    response = urllib.request.urlopen(req, timeout=120)
    result = response.read()
    print(f"✓ SUCCESS - status {response.status}, response size: {len(result)} bytes")
    
    # Verify it's a valid image
    try:
        result_img = Image.open(io.BytesIO(result))
        print(f"✓ Valid image: {result_img.size} {result_img.mode}")
    except Exception as e:
        print(f"✗ Response is not a valid image: {e}")
        
except urllib.error.HTTPError as e:
    print(f"✗ ERROR - HTTP {e.code}")
    error_response = e.read().decode(errors='replace')
    print(f"Response: {error_response[:500]}")
except Exception as e:
    print(f"✗ ERROR: {e}")
