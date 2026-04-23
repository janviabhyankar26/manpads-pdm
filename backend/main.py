from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
import sys
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (MODEL_DIR, DATA_PATH, FEATURE_COLS, HEALTH_LABELS,
                         HEALTH_MODEL_FILE, RUL_BATTERY_FILE, RUL_SEEKER_FILE,
                         RUL_GYRO_FILE, ANOMALY_MODEL_FILE, SCALER_FILE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_all():
    def _load(f):
        return joblib.load(os.path.join(MODEL_DIR, f))
    models = {
        "health"      : _load(HEALTH_MODEL_FILE),
        "rul_battery" : _load(RUL_BATTERY_FILE),
        "rul_seeker"  : _load(RUL_SEEKER_FILE),
        "rul_gyro"    : _load(RUL_GYRO_FILE),
        "anomaly"     : _load(ANOMALY_MODEL_FILE),
        "scaler"      : _load(SCALER_FILE),
    }
    gc.collect()
    return models

try:
    MODELS = load_all()
    print("[INFO] All models loaded.")
except Exception as e:
    print(f"[ERROR] {e}")
    MODELS = None

class SensorInput(BaseModel):
    batt_voltage: float
    batt_current: float
    batt_internal_resistance: float
    batt_soh: float
    batt_temp: float
    batt_charge_cycles: int
    batt_capacity_ah: float
    seeker_coolant_temp: float
    seeker_coolant_pressure: float
    seeker_cooldown_time: float
    seeker_lock_time: float
    seeker_sensor_drift: float
    seeker_signal_noise_ratio: float
    gyro_vibration_rms: float
    gyro_spinup_time: float
    gyro_alignment_drift: float
    gyro_bearing_temp: float
    gyro_acoustic_emission: float
    tube_temp_post_fire: float
    tube_bore_wear_mm: float
    tube_recoil_deviation_pct: float
    tube_corrosion_index: float
    tube_wall_thickness_mm: float
    round_count: int
    op_hours: float
    time_since_maintenance: float
    ambient_temp: float
    humidity_pct: float
    dust_exposure: float
    storage_duration_days: int

def get_recommendation(h, rb, rs, rg, anom):
    msgs = []
    if anom:
        msgs.append("Anomaly detected — inspect all subsystems immediately.")
    if h == 2:
        msgs.append("System is CRITICAL — do not deploy.")
    elif h == 1:
        msgs.append("WARNING state — schedule maintenance soon.")
    else:
        msgs.append("System is healthy — normal operation.")
    if rb < 20:
        msgs.append(f"Battery critically low ({rb} hrs) — replace now.")
    elif rb < 50:
        msgs.append(f"Battery low ({rb} hrs) — plan replacement.")
    if rs < 30:
        msgs.append(f"Seeker coolant critically low ({rs} hrs).")
    if rg < 50:
        msgs.append(f"Gyroscope low ({rg} hrs) — inspect bearings.")
    return " ".join(msgs)

@app.get("/")
def root():
    return {"status": "MANPADS PdM API running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "models_loaded": MODELS is not None}

@app.post("/predict")
def predict(data: SensorInput):
    if MODELS is None:
        raise HTTPException(503, "Models not loaded.")
    row  = pd.DataFrame([data.dict()])[FEATURE_COLS]
    X    = MODELS["scaler"].transform(row)
    h    = int(MODELS["health"].predict(X)[0])
    prob = MODELS["health"].predict_proba(X)[0].tolist()
    rb   = max(0, int(MODELS["rul_battery"].predict(X)[0]))
    rs   = max(0, int(MODELS["rul_seeker"].predict(X)[0]))
    rg   = max(0, int(MODELS["rul_gyro"].predict(X)[0]))
    anom = bool(MODELS["anomaly"].predict(X)[0] == -1)
    ascore = float(-MODELS["anomaly"].score_samples(X)[0])
    del row, X
    gc.collect()
    return {
        "health_code"    : h,
        "health_label"   : HEALTH_LABELS[h],
        "confidence_pct" : round(prob[h] * 100, 1),
        "rul_battery_hrs": rb,
        "rul_seeker_hrs" : rs,
        "rul_gyro_hrs"   : rg,
        "is_anomaly"     : anom,
        "anomaly_score"  : round(ascore, 4),
        "recommendation" : get_recommendation(h, rb, rs, rg, anom),
    }

@app.get("/units")
def get_units():
    df = pd.read_csv(DATA_PATH, usecols=["unit_id"])
    units = sorted(df["unit_id"].unique().tolist())
    del df
    gc.collect()
    return {"units": units}

@app.get("/unit/{unit_id}/predict-all")
def predict_all_cycles(unit_id: str):
    if MODELS is None:
        raise HTTPException(503, "Models not loaded.")
    df   = pd.read_csv(DATA_PATH)
    unit = df[df["unit_id"] == unit_id].copy()
    del df
    gc.collect()
    if unit.empty:
        raise HTTPException(404, f"Unit {unit_id} not found.")
    X        = MODELS["scaler"].transform(unit[FEATURE_COLS])
    health   = MODELS["health"].predict(X).astype(int).tolist()
    rul_bat  = np.maximum(0, MODELS["rul_battery"].predict(X).astype(int)).tolist()
    rul_seek = np.maximum(0, MODELS["rul_seeker"].predict(X).astype(int)).tolist()
    rul_gyro = np.maximum(0, MODELS["rul_gyro"].predict(X).astype(int)).tolist()
    anomaly  = (MODELS["anomaly"].predict(X) == -1).astype(int).tolist()
    del unit, X
    gc.collect()
    return {
        "unit_id"    : unit_id,
        "cycles"     : list(range(1, len(health)+1)),
        "health"     : health,
        "rul_battery": rul_bat,
        "rul_seeker" : rul_seek,
        "rul_gyro"   : rul_gyro,
        "anomaly"    : anomaly,
    }

@app.get("/summary")
def fleet_summary():
    if MODELS is None:
        raise HTTPException(503, "Models not loaded.")
    df     = pd.read_csv(DATA_PATH)
    latest = df.sort_values("cycle").groupby("unit_id").last().reset_index()
    del df
    gc.collect()
    X      = MODELS["scaler"].transform(latest[FEATURE_COLS])
    health = MODELS["health"].predict(X).astype(int)
    rul_bat= np.maximum(0, MODELS["rul_battery"].predict(X).astype(int))
    del latest, X
    gc.collect()
    return {
        "total_units"          : int(len(health)),
        "healthy"              : int((health == 0).sum()),
        "warning"              : int((health == 1).sum()),
        "critical"             : int((health == 2).sum()),
        "avg_rul_battery"      : int(rul_bat.mean()),
        "units_needing_service": int((rul_bat < 50).sum()),
    }
