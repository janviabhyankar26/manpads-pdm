# =============================================================
# predict.py — Load saved models and predict on new/test data
#
# Run:  python src/predict.py
# =============================================================

import os
import sys
import joblib
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (MODEL_DIR, FEATURE_COLS, HEALTH_LABELS,
                    HEALTH_MODEL_FILE, RUL_BATTERY_FILE,
                    RUL_SEEKER_FILE, RUL_GYRO_FILE, ANOMALY_MODEL_FILE)
from data_loader import load_data, load_scaler


# ── Load all saved models ─────────────────────────────────────
def load_all_models():
    """Load all trained models from the models/ directory."""
    def _load(filename):
        path = os.path.join(MODEL_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model not found: {path}\nRun train.py first.")
        return joblib.load(path)

    models = {
        "health"      : _load(HEALTH_MODEL_FILE),
        "rul_battery" : _load(RUL_BATTERY_FILE),
        "rul_seeker"  : _load(RUL_SEEKER_FILE),
        "rul_gyro"    : _load(RUL_GYRO_FILE),
        "anomaly"     : _load(ANOMALY_MODEL_FILE),
    }
    print("[INFO] All models loaded successfully.")
    return models


# ── Core prediction function ──────────────────────────────────
def predict_single(row: dict, models: dict, scaler) -> dict:
    """
    Run all models on a single sensor reading.

    Parameters
    ----------
    row    : dict with keys matching FEATURE_COLS
    models : dict of loaded models from load_all_models()
    scaler : fitted StandardScaler from load_scaler()

    Returns
    -------
    dict with all prediction results
    """
    # Build feature vector in correct column order
    X = pd.DataFrame([row])[FEATURE_COLS]
    X_scaled = scaler.transform(X)

    # 1. Health classification
    health_code  = int(models["health"].predict(X_scaled)[0])
    health_proba = models["health"].predict_proba(X_scaled)[0]
    health_label = HEALTH_LABELS[health_code]

    # 2. RUL predictions (clamp negatives to 0)
    rul_battery = max(0, int(models["rul_battery"].predict(X_scaled)[0]))
    rul_seeker  = max(0, int(models["rul_seeker"].predict(X_scaled)[0]))
    rul_gyro    = max(0, int(models["rul_gyro"].predict(X_scaled)[0]))

    # 3. Anomaly detection (-1 = anomaly → 1, else 0)
    raw_anomaly  = models["anomaly"].predict(X_scaled)[0]
    is_anomaly   = True if raw_anomaly == -1 else False
    anomaly_score = -models["anomaly"].score_samples(X_scaled)[0]  # higher = more anomalous

    # 4. Maintenance recommendation
    recommendation = _get_recommendation(
        health_code, rul_battery, rul_seeker, rul_gyro, is_anomaly
    )

    return {
        "health_code"       : health_code,
        "health_label"      : health_label,
        "confidence_pct"    : round(float(health_proba[health_code]) * 100, 1),
        "rul_battery_hrs"   : rul_battery,
        "rul_seeker_hrs"    : rul_seeker,
        "rul_gyro_hrs"      : rul_gyro,
        "is_anomaly"        : is_anomaly,
        "anomaly_score"     : round(float(anomaly_score), 4),
        "recommendation"    : recommendation,
    }


def predict_batch(df: pd.DataFrame, models: dict, scaler) -> pd.DataFrame:
    """
    Run all models on a full DataFrame of sensor readings.

    Returns original DataFrame with prediction columns appended.
    """
    X = df[FEATURE_COLS]
    X_scaled = scaler.transform(X)

    df = df.copy()
    df["pred_health_code"]  = models["health"].predict(X_scaled).astype(int)
    df["pred_health_label"] = df["pred_health_code"].map(HEALTH_LABELS)
    df["pred_rul_battery"]  = np.maximum(0, models["rul_battery"].predict(X_scaled).astype(int))
    df["pred_rul_seeker"]   = np.maximum(0, models["rul_seeker"].predict(X_scaled).astype(int))
    df["pred_rul_gyro"]     = np.maximum(0, models["rul_gyro"].predict(X_scaled).astype(int))

    raw_anomaly             = models["anomaly"].predict(X_scaled)
    df["pred_anomaly"]      = (raw_anomaly == -1).astype(int)

    return df


# ── Recommendation logic ──────────────────────────────────────
def _get_recommendation(health_code, rul_bat, rul_seek, rul_gyro, is_anomaly):
    """Generate plain-English maintenance recommendation from model outputs."""
    msgs = []

    if is_anomaly:
        msgs.append("ANOMALY DETECTED — Inspect all subsystems immediately.")

    if health_code == 2:
        msgs.append("System is CRITICAL — Do NOT deploy. Immediate maintenance required.")
    elif health_code == 1:
        msgs.append("System is in WARNING state — Schedule maintenance soon.")
    else:
        msgs.append("System is HEALTHY — Normal operation.")

    if rul_bat < 20:
        msgs.append(f"Battery RUL is critically low ({rul_bat} hrs) — Replace immediately.")
    elif rul_bat < 50:
        msgs.append(f"Battery RUL is low ({rul_bat} hrs) — Schedule replacement.")

    if rul_seek < 30:
        msgs.append(f"Seeker coolant RUL is critically low ({rul_seek} hrs) — Service immediately.")
    elif rul_seek < 80:
        msgs.append(f"Seeker coolant RUL is low ({rul_seek} hrs) — Plan service.")

    if rul_gyro < 50:
        msgs.append(f"Gyroscope RUL is critically low ({rul_gyro} hrs) — Inspect bearings.")

    return " | ".join(msgs)


# ── Demo: run predictions on a sample ────────────────────────
def main():
    print("\n" + "="*60)
    print("  MANPADS PdM — PREDICTION PIPELINE")
    print("="*60)

    models = load_all_models()
    scaler = load_scaler()
    df     = load_data()

    # ── Single prediction demo ────────────────────────────────
    print("\n--- Single Row Prediction (Row 0) ---")
    sample_row = df[FEATURE_COLS].iloc[0].to_dict()
    result = predict_single(sample_row, models, scaler)

    print(f"  Health State   : {result['health_label']}  (confidence: {result['confidence_pct']}%)")
    print(f"  RUL Battery    : {result['rul_battery_hrs']} hrs")
    print(f"  RUL Seeker     : {result['rul_seeker_hrs']} hrs")
    print(f"  RUL Gyro       : {result['rul_gyro_hrs']} hrs")
    print(f"  Anomaly        : {'YES' if result['is_anomaly'] else 'No'}  (score: {result['anomaly_score']})")
    print(f"  Recommendation : {result['recommendation']}")

    # ── Batch prediction demo ─────────────────────────────────
    print("\n--- Batch Prediction (first 1000 rows) ---")
    batch_df = df.head(1000).copy()
    results  = predict_batch(batch_df, models, scaler)

    print(results[["unit_id", "cycle",
                    "pred_health_label", "pred_rul_battery",
                    "pred_rul_seeker",   "pred_rul_gyro",
                    "pred_anomaly"]].head(10).to_string(index=False))

    # Save batch results
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "outputs", "batch_predictions.csv"
    )
    results.to_csv(out_path, index=False)
    print(f"\n[SAVED] Batch predictions → {out_path}")


if __name__ == "__main__":
    main()
