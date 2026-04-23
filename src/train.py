# =============================================================
# train.py — Train all MANPADS PdM models and save to disk
#
# Run:  python src/train.py
# =============================================================

import os
import sys
import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (classification_report, confusion_matrix,
                              mean_absolute_error, r2_score, accuracy_score)
from xgboost import XGBClassifier, XGBRegressor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (MODEL_DIR, HEALTH_LABELS,
                    HEALTH_MODEL_FILE, RUL_BATTERY_FILE,
                    RUL_SEEKER_FILE, RUL_GYRO_FILE, ANOMALY_MODEL_FILE)
from src.data_loader import (load_data, get_features_and_targets,
                          split_data, scale_features, print_class_distribution)


# ── Helper ────────────────────────────────────────────────────
def save_model(model, filename):
    path = os.path.join(MODEL_DIR, filename)
    joblib.dump(model, path)
    print(f"[SAVED] {filename}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Task 1: Health State Classification ───────────────────────
def train_health_classifier(X_train, X_test, y_train, y_test):
    section("TASK 1 — Health State Classification")
    print_class_distribution(y_train, "Train set health_label")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        # Handle class imbalance: scale weight for minority classes
        scale_pos_weight=1
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n[RESULT] Accuracy : {acc*100:.2f}%")
    print("\n[RESULT] Classification Report:")
    print(classification_report(y_test, y_pred,
                                 target_names=["Healthy", "Warning", "Critical"]))

    save_model(model, HEALTH_MODEL_FILE)
    return model


# ── Task 2a: RUL Battery Prediction ──────────────────────────
def train_rul_model(X_train, X_test, y_train, y_test, target_name, filename):
    section(f"TASK 2 — RUL Regression: {target_name}")

    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-5))) * 100

    print(f"\n[RESULT] MAE  : {mae:.2f} hours")
    print(f"[RESULT] R²   : {r2:.4f}")
    print(f"[RESULT] MAPE : {mape:.2f}%")

    save_model(model, filename)
    return model


# ── Task 3: Anomaly Detection ─────────────────────────────────
def train_anomaly_detector(X_train, X_test, y_test):
    section("TASK 3 — Anomaly Detection (Isolation Forest)")

    # Isolation Forest is unsupervised — train on all features, no labels needed
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,   # ~5% anomalies in dataset
        random_state=42
    )

    model.fit(X_train)

    # Isolation Forest returns -1 for anomaly, 1 for normal
    # Convert to 0/1 to match our anomaly_flag column
    raw_pred = model.predict(X_test)
    y_pred   = (raw_pred == -1).astype(int)

    print("\n[RESULT] Anomaly Detection Report (using anomaly_flag as reference):")
    print(classification_report(y_test, y_pred,
                                 target_names=["Normal", "Anomaly"],
                                 zero_division=0))

    save_model(model, ANOMALY_MODEL_FILE)
    return model


# ── Main Training Pipeline ────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  MANPADS PREDICTIVE MAINTENANCE — TRAINING PIPELINE")
    print("="*60)

    # 1. Load data
    df = load_data()
    X, targets = get_features_and_targets(df)

    # 2. Unit-based train/test split — keeps each unit's time-series intact
    #    Units STG-001 to STG-024 → train (80%), STG-025 to STG-030 → test (20%)
    train_units = [f"STG-{str(i).zfill(3)}" for i in range(1, 25)]
    test_units  = [f"STG-{str(i).zfill(3)}" for i in range(25, 31)]

    train_mask = df["unit_id"].isin(train_units)
    test_mask  = df["unit_id"].isin(test_units)

    X_train_raw = X[train_mask]
    X_test_raw  = X[test_mask]
    X_train, X_test, scaler = scale_features(X_train_raw, X_test_raw, save=True)

    def get_split(target_key):
        y = targets[target_key]
        return y[train_mask], y[test_mask]

    y_train_h,  y_test_h  = get_split("health")
    y_train_rb, y_test_rb = get_split("rul_battery")
    y_train_rs, y_test_rs = get_split("rul_seeker")
    y_train_rg, y_test_rg = get_split("rul_gyro")
    y_train_a,  y_test_a  = get_split("anomaly")

    # 3. Train all models
    train_health_classifier(X_train, X_test, y_train_h, y_test_h)

    train_rul_model(X_train, X_test, y_train_rb, y_test_rb,
                    "RUL Battery", RUL_BATTERY_FILE)
    train_rul_model(X_train, X_test, y_train_rs, y_test_rs,
                    "RUL Seeker",  RUL_SEEKER_FILE)
    train_rul_model(X_train, X_test, y_train_rg, y_test_rg,
                    "RUL Gyro",    RUL_GYRO_FILE)

    train_anomaly_detector(X_train, X_test, y_test_a)

    section("ALL MODELS TRAINED SUCCESSFULLY")
    print(f"[INFO] Models saved in: {MODEL_DIR}")
    print("[INFO] Next step: run  python src/predict.py")


if __name__ == "__main__":
    main()
