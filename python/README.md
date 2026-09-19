# Wearable AI for Detecting Sleep Disorders

A wearable IoT system that monitors physiological and motion signals in real time,
classifies sleep states using a two-stage Random Forest model, displays results
on a local LCD and Streamlit dashboard, and pushes data to Blynk IoT cloud.

---

## System Overview

```
MAX30102 (HR + SpO2)  ──┐
                         ├──► ESP8266 ──► WiFi ──► Flask Server (port 5000)
MPU6050 (Accel + Gyro) ──┘      │                        │
                                  │                   Random Forest
                               16x2 LCD            (2-stage classifier)
                                                         │        │
                                                  Streamlit    Blynk Cloud
                                                  (port 8501)  (V0-V3)
```

**Sleep classes detected:**

| Label | Class |
|-------|-------|
| 0 | Awake |
| 1 | Normal Sleep |
| 2 | Insomnia |
| 3 | Sleep Apnea |
| 4 | Narcolepsy |
| 5 | Circadian Rhythm Disorder |

---

## Hardware Requirements

| Component | Specification |
|-----------|--------------|
| Microcontroller | ESP8266 NodeMCU (ESP-12E) |
| Heart Rate + SpO2 | MAX30102 |
| IMU | MPU6050 (6-axis: Accel + Gyro) |
| Display | 16x2 LCD with I2C backpack (address 0x27) |
| Host PC | Windows/Linux/macOS with Python 3.10+ |

### Wiring (I2C bus — all sensors share SDA/SCL)

| ESP8266 Pin | Connected To |
|-------------|-------------|
| D2 (GPIO4)  | SDA — MAX30102, MPU6050, LCD |
| D1 (GPIO5)  | SCL — MAX30102, MPU6050, LCD |
| 3.3V        | VCC — MAX30102, MPU6050 |
| 5V          | VCC — LCD |
| GND         | GND — all components |

---

## Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Arduino IDE | 2.x | ESP8266 firmware upload |
| Python | 3.10+ | ML backend + dashboard |
| pip packages | see requirements.txt | Flask, Streamlit, scikit-learn, etc. |

### Arduino Libraries (install via Library Manager)

- SparkFun MAX30105 (includes `heartRate.h` and `spo2_algorithm.h`)
- Adafruit MPU6050
- Adafruit Unified Sensor
- LiquidCrystal I2C
- Blynk (for ESP8266)
- ESP8266WiFi — built-in with ESP8266 board package
- ESP8266HTTPClient — built-in with ESP8266 board package

### Arduino Board Package

In Arduino IDE → Preferences → Additional Board Manager URLs, add:
```
http://arduino.esp8266.com/stable/package_esp8266com_index.json
```
Then install **esp8266 by ESP8266 Community** in Board Manager.

Arduino IDE board settings:
- Board: **NodeMCU 1.0 (ESP-12E Module)**
- Upload Speed: 115200
- Port: (whichever COM port appears when ESP8266 is plugged in)

---

## Project File Structure

```
code/
├── README.md                    ← This file
├── sketch_aug16a/
│   ├── sketch_aug16a.ino        ← Main ESP8266 firmware
│   ├── myMAX30102.h             ← MAX30102 driver (real SpO2 via Maxim algorithm)
│   ├── myMPU6050.h              ← MPU6050 driver (accel + gyro)
│   └── myBlynk.h                ← Reference only (NOT included by .ino)
└── python/
    ├── venv/                    ← Python virtual environment (pre-created)
    ├── requirements.txt         ← Python dependencies
    ├── ml_model.py              ← Two-stage Random Forest classifier
    ├── server.py                ← Flask backend (port 5000)
    ├── dashboard.py             ← Streamlit dashboard (port 8501)
    ├── setup_venv.bat           ← One-time venv setup
    ├── start_server.bat         ← Start Flask server
    ├── start_dashboard.bat      ← Start Streamlit dashboard
    └── data/
        └── status.json          ← Latest reading (written by server.py)
```

---

## Step-by-Step Setup and Run Guide

### Step 1 — Set Up Python Virtual Environment (first time only)

Open a terminal in the `code/python/` folder and run:

```bat
cd python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Or simply double-click `setup_venv.bat` if it exists.

Verify installation:
```bat
venv\Scripts\activate
python -c "import flask, sklearn, streamlit, plotly; print('All packages OK')"
```

### Step 2 — Find Your PC's Local IP Address

Open Command Prompt and run:
```
ipconfig
```
Look for **IPv4 Address** under your WiFi adapter, e.g., `192.168.1.5`.

You need this IP for Step 4.

### Step 3 — Start the Flask Server

In a terminal inside `code/python/`:
```bat
venv\Scripts\activate
python server.py
```

Or double-click `start_server.bat`.

The server will print your current local IP:
```
============================================================
  Wearable AI Sleep Disorder Detection — Server
============================================================
  Local IP  : 192.168.1.5
  Server URL: http://192.168.1.5:5000

  >>> UPDATE sketch_aug16a.ino if IP changed <<<
  const char* SERVER_URL = "http://192.168.1.5:5000/data";
============================================================
```

**Leave this terminal window open.** The server must stay running while the ESP8266 is active.

### Step 4 — Update ESP8266 Firmware (if IP changed)

Open `sketch_aug16a/sketch_aug16a.ino` in Arduino IDE.

Find this line and update the IP address:
```cpp
const char* SERVER_URL = "http://192.168.1.5:5000/data";
//                                  ^^^^^^^^^^^
//                          replace with your PC's IP from Step 2/3
```

WiFi credentials are already set:
```cpp
const char* WIFI_SSID = "<configure locally>";
const char* WIFI_PASS = "<configure locally>";
```

### Step 5 — Upload Firmware to ESP8266

1. Connect ESP8266 to PC via USB cable.
2. In Arduino IDE: **Tools → Board → NodeMCU 1.0 (ESP-12E Module)**
3. **Tools → Port → (select the COM port for ESP8266)**
4. Click **Upload** (Ctrl+U).
5. Wait for "Done uploading".

Open **Serial Monitor** (Tools → Serial Monitor, 115200 baud) to verify:
```
WiFi OK — IP: 192.168.1.x
Blynk connected
MAX30102 OK — place finger on sensor
```

### Step 6 — Start the Streamlit Dashboard

Open a **new terminal** in `code/python/` (keep the server terminal open):
```bat
venv\Scripts\activate
streamlit run dashboard.py
```

Or double-click `start_dashboard.bat`.

The browser will open automatically at **http://localhost:8501**

If it does not open, manually navigate to http://localhost:8501 in your browser.

### Step 7 — Use the System

1. Place your finger on the **MAX30102 sensor** (on the glass window, apply light pressure).
2. Keep the wearable device on your wrist/body so MPU6050 captures movement.
3. The LCD will display: `HR:72  O2:98%` on line 1, `Mov:9.81 m/s2` on line 2.
4. The Streamlit dashboard auto-refreshes every 3 seconds.
5. After **10 readings (~20 seconds)**, the ML model produces classification results.

---

## Blynk IoT Setup

### Blynk App Configuration

The firmware uses these credentials (already set in the .ino file):
- **Template ID:** `TMPL3Pk_nIuBx`
- **Auth Token:** configure locally and set `BLYNK_TOKEN` before starting the server

### Virtual Pin Mapping

| Virtual Pin | Data | Source |
|-------------|------|--------|
| V0 | Heart Rate (BPM) | ESP8266 firmware |
| V1 | SpO2 (%) | ESP8266 firmware |
| V2 | Sleep label (0-5) | Flask server (Python) |
| V3 | Alert level (0=OK, 1=Warning, 2=Critical) | Flask server (Python) |

### Add Widgets in Blynk App

1. Open Blynk app → your template.
2. Add a **Gauge** or **Value Display** widget → Virtual Pin V0 → label "BPM".
3. Add a **Gauge** or **Value Display** → V1 → label "SpO2 (%)".
4. Add a **Value Display** → V2 → label "Sleep State (0-5)".
5. Add a **LED** or **Value Display** → V3 → label "Alert" (0=green, 1-2=red).

---

## ML Model Details

### Two-Stage Cascade Classifier

**Stage 1 — Binary (Awake vs Sleeping)**
- 100 decision trees
- Trained on all 2400 samples
- Output: 0 (Awake) or 1 (Sleeping)

**Stage 2 — Multi-class Disorder (if Stage 1 says Sleeping)**
- 150 decision trees
- Trained on 2000 sleeping samples only
- Output: 1 (Normal) / 2 (Insomnia) / 3 (Apnea) / 4 (Narcolepsy) / 5 (Circadian)

### Features Extracted (11 total)

**Physiological (from MAX30102):**
- `mean_bpm` — average heart rate
- `std_bpm` — HRV proxy (heart rate variability)
- `mean_spo2` — mean blood oxygen saturation
- `min_spo2` — minimum SpO2 (detects apnea dips)
- `std_spo2` — SpO2 variability
- `desat_count` — count of readings with SpO2 < 94%

**Motion (from MPU6050):**
- `mean_accel` — mean acceleration magnitude
- `std_accel` — restlessness index
- `mean_gyro` — mean angular velocity magnitude
- `movement_count` — readings where accel deviates from gravity by > 0.5 m/s²
- `posture_count` — posture transitions (accel change > 1.0 m/s² between readings)

### Sliding Window

The classifier uses a **10-reading sliding window** (FIFO). Each reading arrives every ~2 seconds, so the window represents ~20 seconds of data. Classification starts immediately with the first reading and improves as the window fills.

---

## Alert Conditions

| Condition | Alert Level | Display |
|-----------|-------------|---------|
| SpO2 < 90% | Critical (2) | Red error banner |
| Sleep Apnea detected | Critical (2) | Red error banner |
| SpO2 90-94% | Warning (1) | Orange warning |
| Insomnia / Narcolepsy / Circadian | Warning (1) | Orange warning |
| All normal | OK (0) | Green success |

---

## Troubleshooting

### ESP8266 won't connect to WiFi
- Check SSID and password in the `.ino` file.
- Ensure the router is 2.4 GHz (ESP8266 does not support 5 GHz).
- Open Serial Monitor at 115200 baud to see connection status.

### Server not receiving data
- Verify `SERVER_URL` IP in the `.ino` matches what `server.py` prints.
- Check Windows Firewall — allow Python on port 5000 (or disable temporarily for testing).
- Ping the PC from another device to verify the IP is reachable.

### Streamlit says "Cannot reach Flask server"
- Make sure `server.py` is running in a separate terminal.
- The dashboard connects to `http://localhost:5000` — both must run on the same PC.

### MAX30102 reads 0 BPM / 0 SpO2
- Finger not firmly on sensor (IR < 50000 threshold triggers no-finger mode).
- Apply light, steady pressure — do not press hard.
- Ensure the sensor glass is clean.

### Blynk V2/V3 not updating
- Confirm the `BLYNK_TOKEN` in `server.py` matches the token in the `.ino` file.
- Blynk cloud pushes require internet connectivity on the PC running `server.py`.
- Check Blynk app widget is set to the correct virtual pin (V2 / V3).

### Classification stays at "Initializing..."
- The model needs at least 1 valid reading (BPM > 0 and SpO2 > 0).
- Place finger on sensor and wait for `BPM=XX SpO2=XX` in the server console.

---

## Running Both Server and Dashboard Together (Quick Start)

Open two separate Command Prompt windows:

**Window 1 (Server):**
```bat
cd "C:\Users\user\Desktop\Wearable Ai for detecting sleep disorder\code\python"
start_server.bat
```

**Window 2 (Dashboard):**
```bat
cd "C:\Users\user\Desktop\Wearable Ai for detecting sleep disorder\code\python"
start_dashboard.bat
```

Then open http://localhost:8501 in your browser.
