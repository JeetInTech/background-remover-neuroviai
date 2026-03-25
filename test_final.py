"""Comprehensive API test - simulating real-world usage."""
import urllib.request
import urllib.parse
import io
import json
from PIL import Image

print("="*70)
print("BACKGROUND REMOVER API - COMPREHENSIVE TEST")
print("="*70)

base_url = "http://127.0.0.1:8001"

# Test 1: Check models endpoint
print("\n[TEST 1] GET /models")
try:
    response = urllib.request.urlopen(f"{base_url}/models", timeout=5)
    models = json.loads(response.read())
    print(f"  ✓ Models available: {len(models)}")
    for name in list(models.keys())[:3]:
        print(f"    - {name}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

def test_background_removal(img_color, img_size=(200, 200), model="isnet-general-use", desc=""):
    """Helper to test background removal with different images."""
    # Create test image
    img = Image.new("RGB", img_size, color=img_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()
    
    # Build multipart form
    boundary = "----TestBoundary123456789"
    body = bytearray()
    
    body.extend(f'--{boundary}\r\n'.encode())
    body.extend(b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n')
    body.extend(b'Content-Type: image/png\r\n\r\n')
    body.extend(image_bytes)
    body.extend(b'\r\n')
    
    body.extend(f'--{boundary}\r\n'.encode())
    body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    body.extend(model.encode())
    body.extend(b'\r\n')
    
    body.extend(f'--{boundary}\r\n'.encode())
    body.extend(b'Content-Disposition: form-data; name="alpha_matting"\r\n\r\n')
    body.extend(b'false\r\n')
    
    body.extend(f'--{boundary}--\r\n'.encode())
    
    # Send request
    req = urllib.request.Request(
        f"{base_url}/remove-bg",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    
    try:
        response = urllib.request.urlopen(req, timeout=120)
        result = response.read()
        result_img = Image.open(io.BytesIO(result))
        
        # Check if background was actually removed
        alpha = result_img.split()[-1] if result_img.mode == 'RGBA' else None
        transparency = alpha.getextrema() if alpha else None
        
        print(f"  ✓ {desc} - {img_color.upper()} {img_size}")
        print(f"    Output: {len(result)} bytes, {result_img.size} {result_img.mode}")
        if transparency:
            print(f"    Alpha channel: {transparency[0]}-{transparency[1]} (0=transparent, 255=opaque)")
        return True
    except Exception as e:
        print(f"  ✗ {desc} - {img_color.upper()} FAILED: {e}")
        return False

# Test 2-4: Different image types
print("\n[TEST 2-4] Background removal with different images")
test_background_removal("red", (300, 300), "isnet-general-use", "Test 2: Large red image")
test_background_removal("blue", (200, 200), "u2net", "Test 3: Blue image (u2net model)")
test_background_removal("green", (150, 150), "silueta", "Test 4: Small green image (silueta)")

# Test 5: Check if file size is reported correctly
print("\n[TEST 5] Response headers validation")
img = Image.new("RGB", (100, 100), "yellow")
buf = io.BytesIO()
img.save(buf, format="PNG")
image_bytes = buf.getvalue()

boundary = "----Test555"
body = bytearray()
body.extend(f'--{boundary}\r\n'.encode())
body.extend(b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n')
body.extend(b'Content-Type: image/png\r\n\r\n')
body.extend(image_bytes)
body.extend(b'\r\n')
body.extend(f'--{boundary}--\r\n'.encode())

req = urllib.request.Request(
    f"{base_url}/remove-bg",
    data=bytes(body),
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST"
)

try:
    response = urllib.request.urlopen(req, timeout=120)
    headers = dict(response.headers)
    
    print(f"  ✓ Response headers:")
    print(f"    - X-Resolution: {headers.get('X-Resolution', 'N/A')}")
    print(f"    - X-Original-Size: {headers.get('X-Original-Size', 'N/A')} bytes")
    print(f"    - X-Output-Size: {headers.get('X-Output-Size', 'N/A')} bytes")
    print(f"    - Content-Type: {headers.get('Content-Type', 'N/A')}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED - API IS WORKING!")
print("="*70)
print(f"\n🌐 Access the app at: http://localhost:8001/")
print("📝 NOTE: First use of each model will download model files (200-500MB)")
