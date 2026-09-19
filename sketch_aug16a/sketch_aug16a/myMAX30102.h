/*
  MAX30102 — Heart Rate + SpO2
  Uses SparkFun MAX30105 library (heartRate.h + spo2_algorithm.h)
  SpO2 calculated from red/IR buffer ratio using the Maxim algorithm.
*/

#pragma once
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "spo2_algorithm.h"

MAX30105 heartRateSensor;

int   averageBPM  = 0;
float currentSPO2 = 0.0f;

// HR averaging
static const byte RATE_SIZE = 4;
static byte       rates[RATE_SIZE];
static byte       rateSpot = 0;
static long       lastBeat = 0;

// SpO2 buffer (Maxim algorithm needs 100 samples)
static const int  OX_BUF = 100;
static uint32_t   irBuf[OX_BUF];
static uint32_t   redBuf[OX_BUF];

void myMAX30102_initialise() {
  if (!heartRateSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 not found — check wiring");
    while (1) delay(10);
  }
  // Setup: default LED power, 400 Hz sample rate, 18-bit ADC, 69 µs pulse width
  heartRateSensor.setup();
  heartRateSensor.setPulseAmplitudeRed(0x1F);
  heartRateSensor.setPulseAmplitudeIR(0x1F);
  heartRateSensor.setPulseAmplitudeGreen(0x00);
  Serial.println("MAX30102 OK — place finger on sensor");
}

void myMAX30102_read() {
  // Collect OX_BUF samples for SpO2 calculation
  for (int i = 0; i < OX_BUF; i++) {
    while (!heartRateSensor.available())
      heartRateSensor.check();

    redBuf[i] = heartRateSensor.getRed();
    irBuf[i]  = heartRateSensor.getIR();
    heartRateSensor.nextSample();

    // Detect heartbeat during buffer fill
    if (checkForBeat((long)irBuf[i])) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      float bpm = 60.0f / (delta / 1000.0f);
      if (bpm > 20 && bpm < 240) {
        rates[rateSpot++] = (byte)bpm;
        rateSpot %= RATE_SIZE;
        int sum = 0;
        for (byte j = 0; j < RATE_SIZE; j++) sum += rates[j];
        averageBPM = sum / RATE_SIZE;
      }
    }
  }

  // Check finger presence via IR level
  uint32_t irLast = irBuf[OX_BUF - 1];
  if (irLast < 50000) {
    averageBPM = 0;
    currentSPO2 = 0.0f;
    Serial.println("BPM=0 SpO2=0 (no finger)");
    return;
  }

  // Calculate SpO2 using Maxim algorithm
  int32_t spo2Raw = 0, hrRaw = 0;
  int8_t  validSPO2 = 0, validHR = 0;
  maxim_heart_rate_and_oxygen_saturation(
    irBuf, OX_BUF, redBuf, &spo2Raw, &validSPO2, &hrRaw, &validHR);

  if (validSPO2 && spo2Raw >= 70 && spo2Raw <= 100) {
    currentSPO2 = (float)spo2Raw;
  }
  if (validHR && hrRaw > 20 && hrRaw < 240) {
    averageBPM = (int)hrRaw;
  }

  Serial.print("BPM="); Serial.print(averageBPM);
  Serial.print("  SpO2="); Serial.print(currentSPO2);
  Serial.println("%");
}
