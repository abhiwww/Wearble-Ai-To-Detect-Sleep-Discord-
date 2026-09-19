import serial
import time
import sys

PORT = "COM4"
BAUD = 115200
DURATION = 40  # seconds to monitor

try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2)
    print(f"=== Serial Monitor ({PORT} @ {BAUD}) ===")
    start = time.time()
    while time.time() - start < DURATION:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            elapsed = time.time() - start
            print(f"[{elapsed:5.1f}s] {line}")
            sys.stdout.flush()
    ser.close()
    print("=== Monitor complete ===")
except Exception as e:
    print(f"Error: {e}")
