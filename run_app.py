"""Start the app with port cleanup."""
import socket
import time
import subprocess
import sys

# Try to connect and see if port is actually in use
port = 8000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print(f"Waiting for port {port} to become available...")
for attempt in range(10):
    try:
        sock.bind(("0.0.0.0", port))
        sock.close()
        print(f"✓ Port {port} is now available")
        break
    except OSError:
        print(f"  Attempt {attempt+1}/10: Port still in use, waiting...")
        time.sleep(1)
else:
    print(f"✗ Port {port} still in use after 10 seconds. Using port 8001 instead.")
    port = 8001

print(f"\nStarting app on port {port}...")
subprocess.run([sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(port)])
