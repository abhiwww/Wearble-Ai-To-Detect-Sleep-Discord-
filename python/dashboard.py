"""
Streamlit dashboard for real-time sleep disorder monitoring.
Polls the Flask server at localhost:5000 every 3 seconds.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import math
import time

SERVER = "http://localhost:5000"

LABELS = {
    -1: "Waiting...",
    0: "Awake",
    1: "Normal Sleep",
    2: "Insomnia",
    3: "Sleep Apnea",
    4: "Narcolepsy",
    5: "Circadian Rhythm Disorder",
}

COLORS = {
    -1: "#808080",
    0: "#4CAF50",
    1: "#2196F3",
    2: "#FF9800",
    3: "#F44336",
    4: "#9C27B0",
    5: "#FF5722",
}

ICONS = {
    -1: "⏳", 0: "👁️", 1: "😴", 2: "🌙", 3: "😮‍💨", 4: "💤", 5: "🕐",
}

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sleep Disorder Monitor",
    page_icon="😴",
    layout="wide",
)


st.title("🛌 Wearable AI Sleep Disorder Detection")
st.caption("Real-time monitoring · MAX30102 + MPU6050 + ESP8266")

# ── Fetch data ───────────────────────────────────────────────────────────────

def fetch_status():
    try:
        r = requests.get(f"{SERVER}/status", timeout=2)
        return r.json() if r.ok else None
    except Exception:
        return None


def fetch_history():
    try:
        r = requests.get(f"{SERVER}/history", timeout=2)
        return r.json() if r.ok else []
    except Exception:
        return []


status = fetch_status()
history = fetch_history()

# ── Server offline message ────────────────────────────────────────────────────
if status is None:
    st.error("Cannot reach Flask server at http://localhost:5000")
    st.markdown("""
**To start the server:**
```
cd python
venv\\Scripts\\activate
python server.py
```
""")
    st.stop()

# ── Metric row ───────────────────────────────────────────────────────────────
bpm    = status.get("bpm", 0)
spo2   = status.get("spo2", 0.0)
accel  = status.get("accel_mag", 0.0)
label  = status.get("sleep_label", -1)
state  = status.get("sleep_state", "Waiting...")
conf   = status.get("confidence", 0.0)
n_recv = status.get("readings_received", 0)
color     = COLORS.get(label, "#808080")
icon      = ICONS.get(label, "⏳")
no_finger = bpm == 0 and spo2 == 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    bpm_status = "" if bpm == 0 else ("Normal" if 60 <= bpm <= 100 else "⚠ Abnormal")
    st.metric("Heart Rate (BPM)", f"{int(bpm)}" if bpm else "—", bpm_status)
with col2:
    spo2_status = "" if spo2 == 0 else ("Normal" if spo2 >= 95 else "⚠ Low" if spo2 >= 90 else "🚨 Critical")
    st.metric("SpO2 (%)", f"{spo2:.1f}" if spo2 else "—", spo2_status)
with col3:
    st.metric("Accel Mag (m/s²)", f"{accel:.2f}")
with col4:
    st.metric("Readings", n_recv, "data points")

# ── Classification banner ─────────────────────────────────────────────────────
if no_finger:
    st.markdown(
        """
        <div style="background:#FFF3E022;border-left:6px solid #FF9800;
                    padding:18px 24px;border-radius:10px;margin:12px 0">
            <h2 style="color:#FF9800;margin:0">👆 Place your finger on the MAX30102 sensor</h2>
            <p style="margin:6px 0 0;opacity:0.8">
                Heart rate and SpO2 are required for sleep disorder prediction.
                Press fingertip gently on the sensor and hold still.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div style="background:{color}22;border-left:6px solid {color};
                    padding:18px 24px;border-radius:10px;margin:12px 0">
            <h2 style="color:{color};margin:0">{icon} {state}</h2>
            <p style="margin:6px 0 0;opacity:0.8">
                Confidence: <strong>{conf*100:.1f}%</strong> &nbsp;·&nbsp;
                Readings in window: <strong>{min(n_recv, 10)}/10</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Trend charts ─────────────────────────────────────────────────────────────
if history:
    df = pd.DataFrame(history)
    df["time"] = pd.to_datetime(df["timestamp"], unit="s")

    c1, c2 = st.columns(2)

    # Heart Rate
    with c1:
        st.subheader("Heart Rate")
        df_bpm = df[df["bpm"] > 0]
        if not df_bpm.empty:
            fig = go.Figure()
            fig.add_hrect(y0=60, y1=100, fillcolor="green", opacity=0.08,
                          annotation_text="Normal 60-100 BPM", annotation_position="top right")
            fig.add_trace(go.Scatter(
                x=df_bpm["time"], y=df_bpm["bpm"],
                mode="lines+markers", name="BPM",
                line=dict(color="#F44336", width=2),
                marker=dict(size=5),
            ))
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                              yaxis_title="BPM", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Place finger firmly on MAX30102 sensor")

    # SpO2
    with c2:
        st.subheader("SpO2")
        df_spo2 = df[df["spo2"] > 0]
        if not df_spo2.empty:
            fig = go.Figure()
            fig.add_hrect(y0=95, y1=100, fillcolor="green", opacity=0.1,
                          annotation_text="Normal ≥95%")
            fig.add_hrect(y0=90, y1=95, fillcolor="orange", opacity=0.1,
                          annotation_text="Low 90-95%")
            fig.add_hrect(y0=0, y1=90, fillcolor="red", opacity=0.1,
                          annotation_text="Critical <90%")
            fig.add_trace(go.Scatter(
                x=df_spo2["time"], y=df_spo2["spo2"],
                mode="lines+markers", name="SpO2",
                line=dict(color="#2196F3", width=2),
                marker=dict(size=5),
            ))
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                              yaxis_title="SpO2 %", xaxis_title="",
                              yaxis_range=[75, 101])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for SpO2 data...")

    c3, c4 = st.columns(2)

    # Acceleration magnitude
    with c3:
        st.subheader("Body Movement (Accel Magnitude)")
        if "accel_mag" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["accel_mag"],
                mode="lines", name="Accel Mag",
                fill="tozeroy",
                line=dict(color="#FF9800", width=2),
                fillcolor="rgba(255,152,0,0.12)",
            ))
            fig.add_hline(y=9.81, line_dash="dash", line_color="gray",
                          annotation_text="Gravity (9.81)")
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                              yaxis_title="m/s²", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    # Gyroscope
    with c4:
        st.subheader("Gyroscope (Angular Velocity)")
        if all(c in df.columns for c in ["gyro_x", "gyro_y", "gyro_z"]):
            fig = go.Figure()
            for axis, clr in zip(["gyro_x", "gyro_y", "gyro_z"],
                                  ["#F44336", "#4CAF50", "#2196F3"]):
                fig.add_trace(go.Scatter(
                    x=df["time"], y=df[axis],
                    mode="lines", name=axis.upper(),
                    line=dict(color=clr, width=1.5),
                ))
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                              yaxis_title="rad/s", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No sensor data yet. Ensure ESP8266 is running and connected to this server.")
    st.markdown("""
**Check:**
- ESP8266 is powered and connected to WiFi
- `SERVER_URL` in `sketch_aug16a.ino` matches this PC's IP (shown when server starts)
- `server.py` is running
""")

# ── Alerts ────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Alerts")

alerts = []
if not no_finger:
    if spo2 > 0 and spo2 < 90:
        alerts.append(("critical", f"SpO2 critically low: {spo2:.1f}% — possible severe apnea event!"))
    elif spo2 > 0 and spo2 < 94:
        alerts.append(("warning", f"SpO2 low: {spo2:.1f}% — monitor closely"))
    if bpm > 110:
        alerts.append(("warning", f"Heart rate elevated: {int(bpm)} BPM"))
    if bpm > 0 and bpm < 45:
        alerts.append(("warning", f"Heart rate very low: {int(bpm)} BPM"))
    if label == 3:
        alerts.append(("critical", "Sleep Apnea pattern detected — breathing irregularity identified"))
    if label == 2:
        alerts.append(("info", "Insomnia pattern — frequent movement and elevated HR during sleep period"))
    if label == 4:
        alerts.append(("warning", "Narcolepsy pattern — sudden movement bursts detected"))

if no_finger:
    st.info("Place finger on sensor — alerts will appear once readings begin.")
elif alerts:
    for level, msg in alerts:
        if level == "critical":
            st.error(f"🚨 {msg}")
        elif level == "warning":
            st.warning(f"⚠️ {msg}")
        else:
            st.info(f"ℹ️ {msg}")
else:
    if n_recv > 0:
        st.success("✅ All readings within normal range — no alerts")
    else:
        st.info("Waiting for sensor readings...")

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("Raw sensor data (latest reading)"):
    st.json(status)

st.caption(f"Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')} · Auto-refreshes every 3 seconds")

time.sleep(3)
st.rerun()
