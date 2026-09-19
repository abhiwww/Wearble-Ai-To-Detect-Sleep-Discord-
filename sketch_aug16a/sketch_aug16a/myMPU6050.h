/*
  MPU6050 — 6-axis IMU (accelerometer + gyroscope)
  Uses Adafruit MPU6050 library.
  Global sensor_event_t a, g, temp are available to the main sketch.
*/

#pragma once
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
sensors_event_t  a, g, temp;

void myMPU6050_initialise() {
  if (!mpu.begin()) {
    Serial.println("MPU6050 not found — check wiring");
    while (1) delay(10);
  }
  Serial.println("MPU6050 OK");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  delay(100);
}

void myMPU6050_read() {
  mpu.getEvent(&a, &g, &temp);

  Serial.print("Accel X:");  Serial.print(a.acceleration.x, 3);
  Serial.print(" Y:");       Serial.print(a.acceleration.y, 3);
  Serial.print(" Z:");       Serial.print(a.acceleration.z, 3);
  Serial.print(" m/s²  |  Gyro X:"); Serial.print(g.gyro.x, 4);
  Serial.print(" Y:");       Serial.print(g.gyro.y, 4);
  Serial.print(" Z:");       Serial.print(g.gyro.z, 4);
  Serial.println(" rad/s");

  delay(100);
}
