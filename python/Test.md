# Wearable AI Sleep Disorder Detection — Project Instructions

## Hardware (DO NOT CHANGE)
- Microcontroller: **ESP8266** NodeMCU (ESP-12E) — NOT ESP32
- Sensors: MAX30102 (HR + SpO2 via I2C), MPU6050 (IMU via I2C)
- Display: 16x2 LCD I2C at address 0x27
- All hardware is assembled and wired — no circuit changes needed

## Credentials (DO NOT CHANGE)
- WiFi SSID and password: configure locally in the firmware
- Blynk Template ID and token: configure locally; set `BLYNK_TOKEN` before starting the server
- Blynk Virtual Pins: V0 = BPM, V1 = SpO2
- PC local IP (may change on DHCP): `192.168.1.3`

## Project File Structure
```
code/
├── sketch_aug16a/
│   ├── sketch_aug16a.ino   ← Main ESP8266 sketch (complete)
│   ├── myMAX30102.h        ← MAX30102 driver with real SpO2 (spo2_algorithm.h)
│   ├── myMPU6050.h         ← MPU6050 driver (gyro enabled)
│   └── myBlynk.h           ← Reference only — NOT included by .ino
└── python/
    ├── venv/               ← Python venv (already set up)
    ├── server.py           ← Flask server on port 5000
    ├── dashboard.py        ← Streamlit dashboard on port 8501
    ├── ml_model.py         ← Random Forest classifier (6 sleep classes)
    ├── requirements.txt
    ├── start_server.bat
    └── start_dashboard.bat
```

## Data Flow
```
MAX30102 + MPU6050 → ESP8266 → HTTP POST JSON → Flask (5000)
                                                     ↓
                                           Random Forest ML
                                          (10-reading window)
                                                     ↓
                                    Streamlit (8501) + Blynk cloud
```

## Sleep Classes
0=Awake | 1=Normal Sleep | 2=Insomnia | 3=Sleep Apnea | 4=Narcolepsy | 5=Circadian Rhythm Disorder

## How to Run
1. `cd python` → `start_server.bat` (starts Flask, prints current PC IP)
2. Upload `sketch_aug16a.ino` to ESP8266 (if not done) — update `SERVER_URL` if IP changed
3. `start_dashboard.bat` → open http://localhost:8501

## Arduino IDE Settings
- Board: NodeMCU 1.0 (ESP-12E Module) | Baud: 115200
- Required libraries: SparkFun MAX30105, Adafruit MPU6050, Adafruit Unified Sensor,
  LiquidCrystal I2C, Blynk, ESP8266WiFi (built-in), ESP8266HTTPClient (built-in)

## ML Model Notes
- 9 features: mean_bpm, std_bpm, mean_spo2, min_spo2, desat_count (<94%),
  mean_accel, std_accel, mean_gyro, movement_count
- 400 synthetic samples per class (2400 total), RF 150 trees
- Top features: mean_accel (0.194), std_accel (0.186), desat_count (0.165)
- Validated: Sleep Apnea correctly detected at SpO2=85-88%

## Key Rules for Claude
- Always use ESP8266 libraries (not ESP32)
- Never change hardware wiring or I2C addresses
- Python UI is always Streamlit (never Flask templates or Jupyter)
- Validate changes against running server before reporting done
- If PC IP changes, update SERVER_URL in .ino and note it here
