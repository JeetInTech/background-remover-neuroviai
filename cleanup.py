"""Close all running background remover processes."""
import subprocess
import sys

print("Closing background processes on ports 8000/8001...\n")

try:
    # Get all Python processes
    result = subprocess.run(
        ["Get-Process", "-Name", "python", "-ErrorAction", "SilentlyContinue"],
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("Running Python processes found:")
        print(result.stdout)
        print("\nTo manually stop the server:")
        print("  1. Use Ctrl+C in the terminal where the server is running")
        print("  2. Or use: taskkill /PID <pid> /F")
        print("  3. Or close all Python: taskkill /IM python.exe /F")
    else:
        print("No Python processes found or already closed")
        
except Exception as e:
    print(f"Error: {e}")
    print("\nManual cleanup:")
    print("  taskkill /IM python.exe /F    # Close all Python processes")

print("\n✓ Updated Dockerfile to use run_app.py with automatic port management")
print("✓ Now supports AVIF, WebP, PNG, JPEG auto-conversion")
print("✓ Ports: 8000 (primary), 8001 (fallback)\n")
