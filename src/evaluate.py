# =============================================================
# evaluate.py — Evaluate all models and save plots/reports
#
# Run:  python src/evaluate.py
# =============================================================

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                    # non-interactive backend for saving files
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (classification_report, confusion_matrix,
                              mean_absolute_error, r2_score,
                              ConfusionMatrixDisplay)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (MODEL_DIR, OUTPUT_DIR, HEALTH_LABELS,
                    HEALTH_MODEL_FILE, RUL_BATTERY_FILE,
                    RUL_SEEKER_FILE, RUL_GYRO_FILE, ANOMALY_MODEL_FILE)
from src.data_loader import (load_data, get_features_and_targets,
                          split_data, load_scaler)


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def load_model(filename):
    return joblib.load(os.path.join(MODEL_DIR, filename))


# ── Plot helpers ──────────────────────────────────────────────
def save_confusion_matrix(y_true, y_pred, class_names, title, filename):
    fig, ax = plt.subplots(figsize=(6, 5))
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[SAVED] {filename}")


def save_rul_scatter(y_true, y_pred, title, filename):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_true, y_pred, alpha=0.3, s=10, color="#2563eb")
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
    ax.set_xlabel("Actual RUL (hours)")
    ax.set_ylabel("Predicted RUL (hours)")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[SAVED] {filename}")


def save_feature_importance(model, feature_names, title, filename, top_n=15):
    importances = model.feature_importances_
    indices     = np.argsort(importances)[-top_n:]
    fig, ax     = plt.subplots(figsize=(7, 5))
    ax.barh(range(top_n), importances[indices], color="#2563eb", edgecolor="none")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_names[i] for i in indices], fontsize=10)
    ax.set_xlabel("Feature Importance")
    ax.set_title(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[SAVED] {filename}")


def save_rul_distribution(y_true, y_pred, title, filename):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(y_true,  bins=40, alpha=0.6, label="Actual RUL",    color="#16a34a")
    ax.hist(y_pred,  bins=40, alpha=0.6, label="Predicted RUL", color="#2563eb")
    ax.set_xlabel("RUL (hours)")
    ax.set_ylabel("Count")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[SAVED] {filename}")


# ── Main evaluation ───────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  MANPADS PdM — MODEL EVALUATION")
    print("="*60)

    # Load data and scaler
    df     = load_data()
    X, targets = get_features_and_targets(df)
    scaler = load_scaler()
    from config import FEATURE_COLS
    feature_names = FEATURE_COLS

    # Unit-based split — must match train.py exactly
    train_units = [f"STG-{str(i).zfill(3)}" for i in range(1, 25)]
    test_units  = [f"STG-{str(i).zfill(3)}" for i in range(25, 31)]
    test_mask   = df["unit_id"].isin(test_units)

    X_test = scaler.transform(X[test_mask])

    def get_test(key):
        return targets[key][test_mask]

    y_test_h  = get_test("health")
    y_test_rb = get_test("rul_battery")
    y_test_rs = get_test("rul_seeker")
    y_test_rg = get_test("rul_gyro")
    y_test_a  = get_test("anomaly")

    # ── Task 1: Health Classification ─────────────────────────
    section("TASK 1 — Health Classification Evaluation")
    clf    = load_model(HEALTH_MODEL_FILE)
    y_pred = clf.predict(X_test)

    print(classification_report(y_test_h, y_pred,
                                  target_names=["Healthy", "Warning", "Critical"]))
    save_confusion_matrix(y_test_h, y_pred,
                           ["Healthy", "Warning", "Critical"],
                           "Health Classification — Confusion Matrix",
                           "confusion_matrix_health.png")
    save_feature_importance(clf, feature_names,
                             "Top 15 Features — Health Classifier",
                             "feature_importance_health.png")

    # ── Task 2: RUL Models ────────────────────────────────────
    for name, file, y_test in [
        ("Battery", RUL_BATTERY_FILE, y_test_rb),
        ("Seeker",  RUL_SEEKER_FILE,  y_test_rs),
        ("Gyro",    RUL_GYRO_FILE,    y_test_rg),
    ]:
        section(f"TASK 2 — RUL {name} Evaluation")
        reg    = load_model(file)
        y_pred = reg.predict(X_test)
        mae    = mean_absolute_error(y_test, y_pred)
        r2     = r2_score(y_test, y_pred)
        mape   = np.mean(np.abs((np.array(y_test) - y_pred) /
                                 (np.array(y_test) + 1e-5))) * 100
        print(f"  MAE  : {mae:.2f} hours")
        print(f"  R²   : {r2:.4f}")
        print(f"  MAPE : {mape:.2f}%")

        save_rul_scatter(np.array(y_test), y_pred,
                          f"RUL {name} — Actual vs Predicted",
                          f"rul_scatter_{name.lower()}.png")
        save_rul_distribution(np.array(y_test), y_pred,
                               f"RUL {name} — Distribution",
                               f"rul_dist_{name.lower()}.png")

    # ── Task 3: Anomaly Detection ─────────────────────────────
    section("TASK 3 — Anomaly Detection Evaluation")
    iso      = load_model(ANOMALY_MODEL_FILE)
    raw_pred = iso.predict(X_test)
    y_pred   = (raw_pred == -1).astype(int)

    print(classification_report(y_test_a, y_pred,
                                  target_names=["Normal", "Anomaly"],
                                  zero_division=0))
    save_confusion_matrix(y_test_a, y_pred,
                           ["Normal", "Anomaly"],
                           "Anomaly Detection — Confusion Matrix",
                           "confusion_matrix_anomaly.png")

    section("EVALUATION COMPLETE")
    print(f"[INFO] All plots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
