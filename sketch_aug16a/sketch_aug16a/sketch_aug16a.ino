// ============================================================
//  Wearable AI Sleep Disorder Detection — ESP8266 Firmware
//  Sensors : MAX30102 (HR + SpO2), MPU6050 (IMU)
//  Display : 16x2 LCD I2C @ 0x27
//  IoT     : Blynk (V0=BPM, V1=SpO2) + HTTP POST to PC server
// ============================================================

#define BLYNK_TEMPLATE_ID "TMPL3gdmQvGkE"
#define BLYNK_TEMPLATE_NAME "prjoject"
#define BLYNK_AUTH_TOKEN "<configure locally>"
#define BLYNK_PRINT         Serial

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include "myMAX30102.h"
#include "myMPU6050.h"

// ── WiFi credentials ─────────────────────────────────────────
const char* WIFI_SSID = "<configure locally>";
const char* WIFI_PASS = "<configure locally>";

// PC local IP — re-run server.py if your IP changes (it prints the correct URL)
const char* SERVER_URL = "http://10.51.6.168:5000/data";

// ── Hardware ─────────────────────────────────────────────────
LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiClient wifiClient;

bool blynkOK = true;

// ── LCD helper ────────────────────────────────────────────────
void lcdPrint(const char* row0, const char* row1 = "") {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print(row0);
  lcd.setCursor(0, 1); lcd.print(row1);
}

// ── WiFi + Blynk init (non-blocking WiFi, optional Blynk) ────
void connectNetwork() {
  lcdPrint("Connecting WiFi", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 24) {
    delay(500);
    tries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK — IP: ");
    Serial.println(WiFi.localIP());
    lcdPrint("WiFi OK", WiFi.localIP().toString().c_str());
    delay(800);
    // Connect Blynk with 4-second timeout
    Blynk.config(BLYNK_AUTH_TOKEN);
    blynkOK = Blynk.connect(4000);
    Serial.println(blynkOK ? "Blynk connected" : "Blynk timeout — continuing offline");
  } else {
    Serial.println("WiFi failed — continuing offline");
    lcdPrint("No WiFi", "Offline mode");
    delay(800);
  }
}

// ── HTTP POST sensor data to Python server ────────────────────
void sendToServer() {
  if (WiFi.status() != WL_CONNECTED) return;

  float ax = a.acceleration.x;
  float ay = a.acceleration.y;
  float az = a.acceleration.z;
  float gx = g.gyro.x;
  float gy = g.gyro.y;
  float gz = g.gyro.z;

  String body = String("{\"bpm\":") + averageBPM
              + ",\"spo2\":"   + String(currentSPO2, 1)
              + ",\"accel_x\":" + String(ax, 3)
              + ",\"accel_y\":" + String(ay, 3)
              + ",\"accel_z\":" + String(az, 3)
              + ",\"gyro_x\":"  + String(gx, 4)
              + ",\"gyro_y\":"  + String(gy, 4)
              + ",\"gyro_z\":"  + String(gz, 4)
              + "}";

  HTTPClient http;
  http.begin(wifiClient, SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000);
  int code = http.POST(body);
  if (code > 0) {
    Serial.print("Server response: ");
    Serial.println(http.getString());
  } else {
    Serial.print("HTTP error: ");
    Serial.println(code);
  }
  http.end();
}

// ── Setup ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(100);

  lcd.init();
  lcd.backlight();
  lcdPrint("Sleep Monitor", "Starting...");
  delay(500);

  connectNetwork();

  lcdPrint("Init sensors...", "");
  myMAX30102_initialise();
  myMPU6050_initialise();

  lcdPrint("Sleep Monitor", "Ready!");
  delay(1000);
}

// ── Loop ──────────────────────────────────────────────────────
void loop() {
  if (blynkOK) Blynk.run();

  // ── Read sensors ──────────────────────────────────────
  myMAX30102_read();
  myMPU6050_read();

  // ── Compute accel magnitude ───────────────────────────
  float ax = a.acceleration.x;
  float ay = a.acceleration.y;
  float az = a.acceleration.z;
  float accelMag = sqrt(ax * ax + ay * ay + az * az);

  // ── LCD display ───────────────────────────────────────
  char row0[17], row1[17];
  if (averageBPM > 0) {
    snprintf(row0, sizeof(row0), "HR:%-3d O2:%-3d%%", averageBPM, (int)currentSPO2);
  } else {
    snprintf(row0, sizeof(row0), "Place finger...");
  }
  snprintf(row1, sizeof(row1), "Mov:%-5.2f m/s2", accelMag);
  lcdPrint(row0, row1);

  // ── Blynk virtual pins ────────────────────────────────
  if (blynkOK) {
    Blynk.virtualWrite(V0, averageBPM);
    Blynk.virtualWrite(V1, currentSPO2);
  }

  // ── Send to Python server ─────────────────────────────
  sendToServer();

  if (blynkOK) Blynk.run();

  delay(2000);
}
