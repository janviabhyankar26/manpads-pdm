# MANPADS Predictive Maintenance System

## Project Structure

```
manpads_pdm/
│
├── data/
│   └── manpads_synthetic_dataset.csv     ← put your dataset here
│
├── src/
│   ├── config.py        ← all constants & paths (edit this if needed)
│   ├── data_loader.py   ← load, split, scale data
│   ├── train.py         ← train all 3 models
│   ├── evaluate.py      ← generate metrics & plots
│   └── predict.py       ← run predictions on new data
│
├── models/              ← saved .pkl model files (auto-created)
├── outputs/             ← plots & batch prediction CSVs (auto-created)
├── app.py               ← Streamlit dashboard
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Run Order

```bash
# Step 1 — Train all models (saves .pkl files to models/)
python src/train.py

# Step 2 — Evaluate models (saves plots to outputs/)
python src/evaluate.py

# Step 3 — Test predictions on sample data
python src/predict.py

# Step 4 — Launch dashboard
streamlit run app.py
```

## Models Built

| Model | Type | Target | Algorithm |
|---|---|---|---|
| Health Classifier | Multi-class Classification | health_label (0/1/2) | XGBoost |
| RUL Battery | Regression | rul_battery (hours) | XGBoost |
| RUL Seeker | Regression | rul_seeker (hours) | XGBoost |
| RUL Gyro | Regression | rul_gyro (hours) | XGBoost |
| Anomaly Detector | Unsupervised | anomaly_flag | Isolation Forest |
