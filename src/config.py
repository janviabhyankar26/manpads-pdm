# =============================================================
# config.py — Central configuration for MANPADS PdM Project
# =============================================================

import os

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH   = os.path.join(BASE_DIR, "data", "manpads_synthetic_dataset.csv")
MODEL_DIR   = os.path.join(BASE_DIR, "models")
OUTPUT_DIR  = os.path.join(BASE_DIR, "outputs")

os.makedirs(MODEL_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Columns ───────────────────────────────────────────────────
DROP_COLS = ["timestamp", "unit_id", "cycle",
             "health_label", "rul_battery", "rul_seeker",
             "rul_gyro", "failure_within_50h", "anomaly_flag"]

FEATURE_COLS = [
    # Battery subsystem
    "batt_voltage", "batt_current", "batt_internal_resistance",
    "batt_soh", "batt_temp", "batt_charge_cycles", "batt_capacity_ah",
    # Seeker / Coolant subsystem
    "seeker_coolant_temp", "seeker_coolant_pressure", "seeker_cooldown_time",
    "seeker_lock_time", "seeker_sensor_drift", "seeker_signal_noise_ratio",
    # Gyroscope subsystem
    "gyro_vibration_rms", "gyro_spinup_time", "gyro_alignment_drift",
    "gyro_bearing_temp", "gyro_acoustic_emission",
    # Launch Tube subsystem
    "tube_temp_post_fire", "tube_bore_wear_mm", "tube_recoil_deviation_pct",
    "tube_corrosion_index", "tube_wall_thickness_mm",
    # Operational / Environment
    "round_count", "op_hours", "time_since_maintenance",
    "ambient_temp", "humidity_pct", "dust_exposure", "storage_duration_days",
]

# ── Target columns ────────────────────────────────────────────
TARGET_HEALTH       = "health_label"          # 0=Healthy, 1=Warning, 2=Critical
TARGET_RUL_BATTERY  = "rul_battery"
TARGET_RUL_SEEKER   = "rul_seeker"
TARGET_RUL_GYRO     = "rul_gyro"
TARGET_FAILURE      = "failure_within_50h"
TARGET_ANOMALY      = "anomaly_flag"

# ── Health label mapping ──────────────────────────────────────
HEALTH_LABELS = {0: "Healthy", 1: "Warning", 2: "Critical"}

# ── Train/test split ──────────────────────────────────────────
TEST_SIZE       = 0.2
RANDOM_STATE    = 42

# ── Model filenames ───────────────────────────────────────────
HEALTH_MODEL_FILE   = "health_classifier.pkl"
RUL_BATTERY_FILE    = "rul_battery_model.pkl"
RUL_SEEKER_FILE     = "rul_seeker_model.pkl"
RUL_GYRO_FILE       = "rul_gyro_model.pkl"
ANOMALY_MODEL_FILE  = "anomaly_detector.pkl"
SCALER_FILE         = "scaler.pkl"
