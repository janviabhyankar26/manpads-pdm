# =============================================================
# data_loader.py — Load and preprocess MANPADS dataset
# =============================================================

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (DATA_PATH, FEATURE_COLS, TARGET_HEALTH, TARGET_RUL_BATTERY,
                    TARGET_RUL_SEEKER, TARGET_RUL_GYRO, TARGET_FAILURE,
                    TARGET_ANOMALY, TEST_SIZE, RANDOM_STATE, MODEL_DIR, SCALER_FILE)


def load_data():
    """Load raw CSV and return as DataFrame."""
    print(f"[INFO] Loading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"[INFO] Dataset shape: {df.shape}")
    print(f"[INFO] Missing values: {df.isnull().sum().sum()}")
    return df


def get_features_and_targets(df):
    """Split DataFrame into feature matrix X and all target Series."""
    X = df[FEATURE_COLS].copy()

    targets = {
        "health"      : df[TARGET_HEALTH],
        "rul_battery" : df[TARGET_RUL_BATTERY],
        "rul_seeker"  : df[TARGET_RUL_SEEKER],
        "rul_gyro"    : df[TARGET_RUL_GYRO],
        "failure"     : df[TARGET_FAILURE],
        "anomaly"     : df[TARGET_ANOMALY],
    }
    return X, targets


def split_data(X, y, stratify=None):
    """Train/test split. Pass stratify=y for classification tasks."""
    return train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify
    )


def scale_features(X_train, X_test, save=True):
    """Fit StandardScaler on train set, transform both sets."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    if save:
        scaler_path = os.path.join(MODEL_DIR, SCALER_FILE)
        joblib.dump(scaler, scaler_path)
        print(f"[INFO] Scaler saved to: {scaler_path}")

    return X_train_scaled, X_test_scaled, scaler


def load_scaler():
    """Load saved scaler from disk."""
    scaler_path = os.path.join(MODEL_DIR, SCALER_FILE)
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found at {scaler_path}. Run train.py first.")
    return joblib.load(scaler_path)


def print_class_distribution(y, label="Target"):
    """Print class distribution as counts and percentages."""
    counts = y.value_counts().sort_index()
    total  = len(y)
    print(f"\n[INFO] {label} distribution:")
    for cls, cnt in counts.items():
        print(f"  Class {cls}: {cnt:>6} rows  ({cnt/total*100:.1f}%)")


if __name__ == "__main__":
    df = load_data()
    X, targets = get_features_and_targets(df)
    print(f"\n[INFO] Feature matrix shape : {X.shape}")
    print(f"[INFO] Feature columns      : {list(X.columns)}")
    print_class_distribution(targets["health"], "Health Label")
    print_class_distribution(targets["anomaly"], "Anomaly Flag")
