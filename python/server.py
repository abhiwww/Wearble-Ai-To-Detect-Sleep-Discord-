"""
Flask server — receives sensor JSON from ESP8266, runs two-stage Random Forest,
stores results, and pushes classification results to Blynk IoT cloud.

Blynk virtual pins pushed from this server:
  V0 = BPM          (also sent by firmware)
  V1 = SpO2         (also sent by firmware)
  V2 = Sleep label  (0-5 integer)
  V3 = Alert level  (0=OK, 1=Warning, 2=Critical)

Streamlit dashboard reads from GET /status and GET /history.
"""

import threading
import time
import json
import os
import socket
from collections import deque

import requests
from flask import Flask, request, jsonify

from ml_model import SleepClassifier

app = Flask(__name__)
_lock = threading.Lock()

WINDOW_SIZE  = 10    # readings used for feature extraction
HISTORY_SIZE = 200

_buffer  = deque(maxlen=WINDOW_SIZE)    # sliding window fed to classifier
_history = deque(maxlen=HISTORY_SIZE)   # full log for trend graphs

_latest = {
    "bpm": 0, "spo2": 0.0,
    "accel_x": 0.0, "accel_y": 0.0, "accel_z": 0.0,
    "gyro_x":  0.0, "gyro_y": 0.0,  "gyro_z": 0.0,
    "accel_mag": 0.0,
    "sleep_state": "Waiting for sensor data...",
    "sleep_label": -1,
    "confidence":  0.0,
    "alert_level": 0,
    "timestamp": 0.0,
    "readings_received": 0,
}

_readings_received = 0

DATA_DIR    = os.path.join(os.path.dirname(__file__), "data")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

# ── Blynk config ────────────────────────────────────────────────────────────
# Token must match the one in sketch_aug16a.ino (#define BLYNK_AUTH_TOKEN)
BLYNK_TOKEN = os.environ.get("BLYNK_TOKEN", "")
BLYNK_API   = "https://blynk.cloud/external/api/update"


def _blynk_set(pin, value):
    """Push a single virtual-pin value to Blynk Cloud (fire-and-forget)."""
    try:
        requests.get(
            f"{BLYNK_API}?token={BLYNK_TOKEN}&{pin}={value}",
            timeout=4,
        )
    except Exception:
        pass


def _push_blynk(label, alert_level):
    """Push sleep label and alert level to Blynk in a daemon thread."""
    threading.Thread(
        target=lambda: (_blynk_set("V2", label), _blynk_set("V3", alert_level)),
        daemon=True,
    ).start()


def _alert_level(label, spo2):
    """
    0 = OK (Awake or Normal Sleep and SpO2 fine)
    1 = Warning  (Insomnia / Narcolepsy / Circadian / low SpO2)
    2 = Critical (Sleep Apnea / SpO2 < 90)
    """
    if spo2 > 0 and spo2 < 90:
        return 2
    if label == 3:          # Sleep Apnea
        return 2
    if label in (2, 4, 5):  # Insomnia / Narcolepsy / Circadian
        return 1
    if spo2 > 0 and spo2 < 94:
        return 1
    return 0


# ── Train model at startup ───────────────────────────────────────────────────
print("[Server] Training two-stage Random Forest model...")
classifier = SleepClassifier()
classifier.train()
print("[Server] Model ready.")


def _save_status():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(_latest, f, indent=2)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/data", methods=["POST"])
def receive_data():
    global _readings_received
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "invalid JSON"}), 400

    import math
    ax = float(raw.get("accel_x", 0))
    ay = float(raw.get("accel_y", 0))
    az = float(raw.get("accel_z", 0))

    reading = {
        "bpm":      float(raw.get("bpm",    0)),
        "spo2":     float(raw.get("spo2",   0)),
        "accel_x":  ax, "accel_y": ay, "accel_z": az,
        "gyro_x":   float(raw.get("gyro_x", 0)),
        "gyro_y":   float(raw.get("gyro_y", 0)),
        "gyro_z":   float(raw.get("gyro_z", 0)),
        "accel_mag": math.sqrt(ax**2 + ay**2 + az**2),
        "timestamp": time.time(),
    }

    with _lock:
        _buffer.append(reading)
        _history.append(reading)
        _readings_received += 1

        label, state, confidence = classifier.classify(list(_buffer))
        alert = _alert_level(label, reading["spo2"])

        _latest.update({
            **reading,
            "sleep_state":      state,
            "sleep_label":      label,
            "confidence":       confidence,
            "alert_level":      alert,
            "readings_received": _readings_received,
        })
        _save_status()

    # Push classification to Blynk (non-blocking)
    if label >= 0:
        _push_blynk(label, alert)

    print(
        f"[Data] BPM={int(reading['bpm'])} SpO2={reading['spo2']:.1f}% "
        f"AccMag={reading['accel_mag']:.2f} → {state} ({confidence*100:.0f}%) "
        f"Alert={alert}"
    )

    return jsonify({
        "status":         "ok",
        "classification": state,
        "label":          label,
        "alert_level":    alert,
    }), 200


@app.route("/status", methods=["GET"])
def get_status():
    with _lock:
        return jsonify(_latest)


@app.route("/history", methods=["GET"])
def get_history():
    with _lock:
        return jsonify(list(_history))


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "alive"}), 200


# ── Entry point ──────────────────────────────────────────────────────────────

def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = _get_local_ip()
    print("=" * 60)
    print("  Wearable AI Sleep Disorder Detection — Server")
    print("=" * 60)
    print(f"  Local IP  : {local_ip}")
    print(f"  Server URL: http://{local_ip}:5000")
    print()
    print("  >>> UPDATE sketch_aug16a.ino if IP changed <<<")
    print(f'  const char* SERVER_URL = "http://{local_ip}:5000/data";')
    print()
    print("  Blynk virtual pins pushed from this server:")
    print("    V2 = sleep label (0-5)")
    print("    V3 = alert level (0=OK, 1=Warning, 2=Critical)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
