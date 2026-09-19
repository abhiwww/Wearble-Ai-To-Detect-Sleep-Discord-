"""
Two-stage Random Forest sleep disorder classifier (as per project spec).

Stage 1: Binary classifier — Awake (0) vs Sleeping (1)
Stage 2: Multi-class classifier — Normal Sleep / Insomnia / Sleep Apnea /
         Narcolepsy / Circadian Rhythm Disorder (labels 1-5)

Feature set (11 features, per Phase 3 of methodology):
  Physiological : mean_bpm, std_bpm (HRV), mean_spo2, min_spo2,
                  std_spo2 (SpO2 variability), desat_count
  Motion        : mean_accel, std_accel (restlessness), mean_gyro,
                  movement_count, posture_count (posture transitions)
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import math

LABELS = {
    0: "Awake",
    1: "Normal Sleep",
    2: "Insomnia",
    3: "Sleep Apnea",
    4: "Narcolepsy",
    5: "Circadian Rhythm Disorder",
}

COLORS = {
    0: "#4CAF50",
    1: "#2196F3",
    2: "#FF9800",
    3: "#F44336",
    4: "#9C27B0",
    5: "#FF5722",
}

FEATURE_NAMES = [
    "mean_bpm", "std_bpm", "mean_spo2", "min_spo2", "std_spo2",
    "desat_count", "mean_accel", "std_accel", "mean_gyro",
    "movement_count", "posture_count",
]


class SleepClassifier:
    def __init__(self):
        # Stage 1: Binary — Awake vs Sleeping
        self.rf_stage1 = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        self.scaler_stage1 = StandardScaler()

        # Stage 2: Multi-class — disorder among sleeping states (labels 1-5)
        self.rf_stage2 = RandomForestClassifier(
            n_estimators=150, random_state=42, n_jobs=-1
        )
        self.scaler_stage2 = StandardScaler()

        self.trained = False

    # ── Feature helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _accel_mag(ax, ay, az):
        return math.sqrt(ax ** 2 + ay ** 2 + az ** 2)

    @staticmethod
    def _gyro_mag(gx, gy, gz):
        return math.sqrt(gx ** 2 + gy ** 2 + gz ** 2)

    # ── Feature extraction ─────────────────────────────────────────────────────

    def extract_features(self, readings):
        """Return 11-element feature vector from a window of sensor readings."""
        if not readings:
            return None

        bpms = [r["bpm"] for r in readings if r.get("bpm", 0) > 0]
        spo2s = [r["spo2"] for r in readings if r.get("spo2", 0) > 0]

        accel_mags = [
            self._accel_mag(
                r.get("accel_x", 0), r.get("accel_y", 0), r.get("accel_z", 0)
            )
            for r in readings
        ]
        gyro_mags = [
            self._gyro_mag(
                r.get("gyro_x", 0), r.get("gyro_y", 0), r.get("gyro_z", 0)
            )
            for r in readings
        ]

        # ── Physiological features ──────────────────────────────────────────
        mean_bpm  = float(np.mean(bpms))       if bpms              else 0.0
        std_bpm   = float(np.std(bpms))        if len(bpms) > 1    else 0.0
        mean_spo2 = float(np.mean(spo2s))      if spo2s             else 0.0
        min_spo2  = float(np.min(spo2s))       if spo2s             else 0.0
        std_spo2  = float(np.std(spo2s))       if len(spo2s) > 1   else 0.0
        desat_count = float(sum(1 for s in spo2s if s < 94))

        # ── Motion features ────────────────────────────────────────────────
        mean_accel = float(np.mean(accel_mags))
        std_accel  = float(np.std(accel_mags))  if len(accel_mags) > 1 else 0.0
        mean_gyro  = float(np.mean(gyro_mags))

        # Movement count: readings where accel deviates from gravity by > 0.5 m/s²
        movement_count = float(sum(1 for m in accel_mags if abs(m - 9.81) > 0.5))

        # Posture transitions: consecutive readings with accel change > 1.0 m/s²
        posture_count = 0.0
        if len(accel_mags) > 1:
            for i in range(1, len(accel_mags)):
                if abs(accel_mags[i] - accel_mags[i - 1]) > 1.0:
                    posture_count += 1.0

        return [
            mean_bpm, std_bpm, mean_spo2, min_spo2, std_spo2,
            desat_count, mean_accel, std_accel, mean_gyro,
            movement_count, posture_count,
        ]

    # ── Synthetic training data ────────────────────────────────────────────────

    def _generate_training_data(self):
        """
        Generate physiologically realistic synthetic training data.
        400 samples per class (2400 total).
        """
        rng = np.random.default_rng(42)
        X, y = [], []
        n = 400

        def add_class(
            label, bpm_r, std_bpm_r, spo2_r, min_spo2_delta,
            std_spo2_r, desat_r, accel_r, std_accel_r,
            gyro_r, mov_r, posture_r,
        ):
            for _ in range(n):
                X.append([
                    rng.uniform(*bpm_r),
                    rng.uniform(*std_bpm_r),
                    rng.uniform(*spo2_r),
                    rng.uniform(spo2_r[0] - min_spo2_delta[1],
                                spo2_r[1] - min_spo2_delta[0]),
                    rng.uniform(*std_spo2_r),
                    rng.uniform(*desat_r),
                    rng.uniform(*accel_r),
                    rng.uniform(*std_accel_r),
                    rng.uniform(*gyro_r),
                    rng.uniform(*mov_r),
                    rng.uniform(*posture_r),
                ])
                y.append(label)

        # 0 = Awake: high HR, high SpO2, lots of movement, frequent posture changes
        add_class(0,
                  bpm_r=(70, 95),    std_bpm_r=(5, 15),
                  spo2_r=(96, 99.5), min_spo2_delta=(0, 2),  std_spo2_r=(0.5, 1.5),
                  desat_r=(0, 0.5),
                  accel_r=(3.0, 10.0), std_accel_r=(1.5, 5.0), gyro_r=(0.5, 3.0),
                  mov_r=(5, 10), posture_r=(5, 10))

        # 1 = Normal Sleep: low HR, high SpO2, minimal movement, near-gravity accel
        add_class(1,
                  bpm_r=(45, 65),    std_bpm_r=(1, 5),
                  spo2_r=(95.5, 99.5), min_spo2_delta=(0, 1), std_spo2_r=(0.2, 0.8),
                  desat_r=(0, 0),
                  accel_r=(9.55, 10.1), std_accel_r=(0.01, 0.2), gyro_r=(0.001, 0.08),
                  mov_r=(0, 2), posture_r=(0, 2))

        # 2 = Insomnia: elevated HR, moderate movement, frequent posture changes
        add_class(2,
                  bpm_r=(65, 88),    std_bpm_r=(8, 18),
                  spo2_r=(93, 98),   min_spo2_delta=(1, 4),  std_spo2_r=(1.0, 3.0),
                  desat_r=(0, 2),
                  accel_r=(10.0, 12.5), std_accel_r=(0.4, 2.0), gyro_r=(0.1, 1.0),
                  mov_r=(3, 9), posture_r=(4, 9))

        # 3 = Sleep Apnea: low SpO2 with high variability, many desaturations, mostly still
        add_class(3,
                  bpm_r=(52, 80),    std_bpm_r=(10, 25),
                  spo2_r=(82, 94),   min_spo2_delta=(5, 15), std_spo2_r=(3.0, 8.0),
                  desat_r=(3, 9),
                  accel_r=(9.5, 10.6), std_accel_r=(0.05, 0.5), gyro_r=(0.02, 0.3),
                  mov_r=(1, 4), posture_r=(1, 4))

        # 4 = Narcolepsy: moderate HR, sudden movement bursts (high std_accel)
        add_class(4,
                  bpm_r=(52, 75),    std_bpm_r=(5, 14),
                  spo2_r=(93, 98),   min_spo2_delta=(0, 3),  std_spo2_r=(1.0, 3.5),
                  desat_r=(0, 2),
                  accel_r=(10.5, 14.0), std_accel_r=(2.0, 5.0), gyro_r=(0.5, 2.5),
                  mov_r=(4, 10), posture_r=(3, 7))

        # 5 = Circadian Rhythm Disorder: awake-like HR at wrong time, moderate motion
        add_class(5,
                  bpm_r=(65, 92),    std_bpm_r=(5, 12),
                  spo2_r=(92, 97),   min_spo2_delta=(1, 5),  std_spo2_r=(0.5, 2.0),
                  desat_r=(0, 3),
                  accel_r=(11.0, 14.0), std_accel_r=(0.6, 2.5), gyro_r=(0.2, 1.5),
                  mov_r=(2, 7), posture_r=(2, 6))

        return np.array(X, dtype=float), np.array(y, dtype=int)

    # ── Training ───────────────────────────────────────────────────────────────

    def train(self):
        X, y = self._generate_training_data()

        # Stage 1: binary (0=Awake, 1=Sleeping)
        y_binary = (y > 0).astype(int)
        X_s1 = self.scaler_stage1.fit_transform(X)
        self.rf_stage1.fit(X_s1, y_binary)

        # Stage 2: disorder multi-class — trained only on sleeping samples
        sleep_mask = y > 0
        X_sleep = X[sleep_mask]
        y_sleep = y[sleep_mask]
        X_s2 = self.scaler_stage2.fit_transform(X_sleep)
        self.rf_stage2.fit(X_s2, y_sleep)

        self.trained = True

        imp1 = dict(zip(FEATURE_NAMES, self.rf_stage1.feature_importances_.round(3)))
        imp2 = dict(zip(FEATURE_NAMES, self.rf_stage2.feature_importances_.round(3)))
        print(f"[ML] Stage 1 (Awake/Sleep) trained on {len(y)} samples")
        print(f"[ML] Stage 2 (Disorder)    trained on {sleep_mask.sum()} sleeping samples")
        print(f"[ML] Stage 1 feature importances: {imp1}")
        print(f"[ML] Stage 2 feature importances: {imp2}")

    # ── Inference ──────────────────────────────────────────────────────────────

    def classify(self, readings):
        """
        Two-stage cascade inference.
        Returns (label_int, label_str, confidence_float).
        """
        if not self.trained or not readings:
            return -1, "Initializing...", 0.0

        features = self.extract_features(readings)
        if features is None:
            return -1, "No data", 0.0

        if features[0] == 0.0 and features[2] == 0.0:
            return -1, "No sensor contact", 0.0

        X = np.array([features])

        # ── Stage 1: Awake vs Sleeping ──────────────────────────────────────
        X_s1 = self.scaler_stage1.transform(X)
        s1_pred = int(self.rf_stage1.predict(X_s1)[0])
        s1_proba = self.rf_stage1.predict_proba(X_s1)[0]
        s1_conf = float(s1_proba[s1_pred])

        if s1_pred == 0:
            return 0, LABELS[0], s1_conf

        # ── Stage 2: Disorder classification ────────────────────────────────
        X_s2 = self.scaler_stage2.transform(X)
        s2_pred = int(self.rf_stage2.predict(X_s2)[0])
        s2_proba = self.rf_stage2.predict_proba(X_s2)[0]
        s2_classes = list(self.rf_stage2.classes_)
        s2_conf = float(s2_proba[s2_classes.index(s2_pred)])

        return s2_pred, LABELS.get(s2_pred, "Unknown"), s2_conf
