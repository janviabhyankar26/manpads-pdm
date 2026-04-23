import React, { useState } from "react";
import { postPredict } from "../api";
import { HealthBadge, AlertItem, PageHeader, Card, ErrorMsg } from "../components/Components";
import styles from "./Pages.module.css";

const DEFAULTS = {
  batt_voltage: 27.5, batt_current: 8.5, batt_internal_resistance: 0.025,
  batt_soh: 88.0, batt_temp: 32.0, batt_charge_cycles: 120, batt_capacity_ah: 2.4,
  seeker_coolant_temp: -63.0, seeker_coolant_pressure: 4.8, seeker_cooldown_time: 1.4,
  seeker_lock_time: 0.9, seeker_sensor_drift: 0.05, seeker_signal_noise_ratio: 42.0,
  gyro_vibration_rms: 0.8, gyro_spinup_time: 0.9, gyro_alignment_drift: 0.03,
  gyro_bearing_temp: 28.0, gyro_acoustic_emission: 34.0,
  tube_temp_post_fire: 145.0, tube_bore_wear_mm: 0.12, tube_recoil_deviation_pct: 1.2,
  tube_corrosion_index: 3.5, tube_wall_thickness_mm: 5.6,
  round_count: 80, op_hours: 220.0, time_since_maintenance: 30.0,
  ambient_temp: 28.0, humidity_pct: 60.0, dust_exposure: 2.0, storage_duration_days: 15,
};

const SECTIONS = [
  {
    title: "Battery subsystem",
    color: "#378ADD",
    fields: [
      { key: "batt_voltage",             label: "Voltage (V)",              step: 0.01 },
      { key: "batt_current",             label: "Current (A)",              step: 0.01 },
      { key: "batt_internal_resistance", label: "Internal resistance (Ω)",  step: 0.001 },
      { key: "batt_soh",                 label: "State of health (%)",      step: 0.1 },
      { key: "batt_temp",                label: "Temperature (°C)",         step: 0.1 },
      { key: "batt_charge_cycles",       label: "Charge cycles",            step: 1,   isInt: true },
      { key: "batt_capacity_ah",         label: "Capacity (Ah)",            step: 0.01 },
    ],
  },
  {
    title: "Seeker / Coolant subsystem",
    color: "#1D9E75",
    fields: [
      { key: "seeker_coolant_temp",       label: "Coolant temp (°C)",       step: 0.1 },
      { key: "seeker_coolant_pressure",   label: "Coolant pressure",        step: 0.01 },
      { key: "seeker_cooldown_time",      label: "Cooldown time (s)",       step: 0.01 },
      { key: "seeker_lock_time",          label: "Lock time (s)",           step: 0.01 },
      { key: "seeker_sensor_drift",       label: "Sensor drift",            step: 0.001 },
      { key: "seeker_signal_noise_ratio", label: "Signal/noise ratio",      step: 0.1 },
    ],
  },
  {
    title: "Gyroscope subsystem",
    color: "#7F77DD",
    fields: [
      { key: "gyro_vibration_rms",   label: "Vibration RMS (mm/s)", step: 0.01 },
      { key: "gyro_spinup_time",     label: "Spin-up time (s)",     step: 0.01 },
      { key: "gyro_alignment_drift", label: "Alignment drift",      step: 0.001 },
      { key: "gyro_bearing_temp",    label: "Bearing temp (°C)",    step: 0.1 },
      { key: "gyro_acoustic_emission",label:"Acoustic emission",    step: 0.1 },
    ],
  },
  {
    title: "Launch tube",
    color: "#EF9F27",
    fields: [
      { key: "tube_temp_post_fire",      label: "Temp post fire (°C)",     step: 0.1 },
      { key: "tube_bore_wear_mm",        label: "Bore wear (mm)",          step: 0.001 },
      { key: "tube_recoil_deviation_pct",label: "Recoil deviation (%)",    step: 0.01 },
      { key: "tube_corrosion_index",     label: "Corrosion index",         step: 0.01 },
      { key: "tube_wall_thickness_mm",   label: "Wall thickness (mm)",     step: 0.001 },
    ],
  },
  {
    title: "Operational & environment",
    color: "#888780",
    fields: [
      { key: "round_count",             label: "Round count",              step: 1,   isInt: true },
      { key: "op_hours",                label: "Operating hours",          step: 0.1 },
      { key: "time_since_maintenance",  label: "Days since maintenance",   step: 0.1 },
      { key: "ambient_temp",            label: "Ambient temp (°C)",        step: 0.1 },
      { key: "humidity_pct",            label: "Humidity (%)",             step: 0.1 },
      { key: "dust_exposure",           label: "Dust exposure",            step: 0.01 },
      { key: "storage_duration_days",   label: "Storage days",             step: 1,   isInt: true },
    ],
  },
];

function buildAlerts(result) {
  const a = [];
  if (result.is_anomaly)
    a.push({ severity:"crit", title:"Anomaly detected", description:`Score: ${result.anomaly_score}` });
  if (result.health_code === 2)
    a.push({ severity:"crit", title:"System critical", description:"Do not deploy." });
  else if (result.health_code === 1)
    a.push({ severity:"warn", title:"System warning",  description:"Schedule maintenance." });
  if (result.rul_battery_hrs < 50)
    a.push({ severity:"crit", title:"Battery critical", description:`${result.rul_battery_hrs} hrs remaining.` });
  if (result.rul_seeker_hrs  < 30)
    a.push({ severity:"crit", title:"Seeker critical",  description:`${result.rul_seeker_hrs} hrs remaining.` });
  if (result.rul_gyro_hrs    < 50)
    a.push({ severity:"warn", title:"Gyro low",         description:`${result.rul_gyro_hrs} hrs remaining.` });
  if (a.length === 0)
    a.push({ severity:"ok",   title:"All systems nominal", description:"No faults detected." });
  return a;
}

export default function Predict() {
  const [form,    setForm]    = useState(DEFAULTS);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  function handleChange(key, val, isInt) {
    setForm(prev => ({ ...prev, [key]: isInt ? parseInt(val) : parseFloat(val) }));
  }

  async function handleSubmit() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await postPredict(form);
      setResult(res.data);
    } catch (e) {
      setError("Prediction failed. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setForm(DEFAULTS);
    setResult(null);
    setError("");
  }

  return (
    <div>
      <PageHeader
        title="Live Prediction"
        subtitle="Enter sensor readings manually to get an instant health and RUL prediction."
      />

      {error && <ErrorMsg message={error} />}

      <div className={styles.predictLayout}>
        {/* Left — input form */}
        <div className={styles.formCol}>
          {SECTIONS.map(section => (
            <Card key={section.title} style={{ marginBottom: 14 }}>
              <div className={styles.sectionHeader}>
                <span className={styles.sectionDot} style={{ background: section.color }} />
                <span className={styles.sectionTitle}>{section.title}</span>
              </div>
              <div className={styles.fieldGrid}>
                {section.fields.map(f => (
                  <div key={f.key} className={styles.fieldRow}>
                    <label className={styles.fieldLabel}>{f.label}</label>
                    <input
                      type="number"
                      step={f.step}
                      value={form[f.key]}
                      onChange={e => handleChange(f.key, e.target.value, f.isInt)}
                      className={styles.fieldInput}
                    />
                  </div>
                ))}
              </div>
            </Card>
          ))}

          <div className={styles.btnRow}>
            <button className={styles.btnPrimary} onClick={handleSubmit} disabled={loading}>
              {loading ? "Running..." : "Run Prediction"}
            </button>
            <button className={styles.btnSecondary} onClick={handleReset}>
              Reset to defaults
            </button>
          </div>
        </div>

        {/* Right — results */}
        <div className={styles.resultCol}>
          {!result && (
            <div className={styles.emptyResult}>
              Fill in sensor values and click Run Prediction to see results here.
            </div>
          )}

          {result && (
            <>
              <Card title="Prediction result">
                <div className={styles.resultKpis}>
                  <div className={styles.resultKpi}>
                    <div className={styles.rkLabel}>Health state</div>
                    <HealthBadge code={result.health_code} />
                    <div className={styles.rkSub}>{result.confidence_pct}% confidence</div>
                  </div>
                  <div className={styles.resultKpi}>
                    <div className={styles.rkLabel}>RUL · Battery</div>
                    <div className={styles.rkVal}>{result.rul_battery_hrs}</div>
                    <div className={styles.rkSub}>hours</div>
                  </div>
                  <div className={styles.resultKpi}>
                    <div className={styles.rkLabel}>RUL · Seeker</div>
                    <div className={styles.rkVal}>{result.rul_seeker_hrs}</div>
                    <div className={styles.rkSub}>hours</div>
                  </div>
                  <div className={styles.resultKpi}>
                    <div className={styles.rkLabel}>RUL · Gyro</div>
                    <div className={styles.rkVal}>{result.rul_gyro_hrs}</div>
                    <div className={styles.rkSub}>hours</div>
                  </div>
                </div>

                <div className={styles.anomalyRow}>
                  <span className={styles.anomalyLabel}>Anomaly</span>
                  <span className={result.is_anomaly ? styles.anomalyYes : styles.anomalyNo}>
                    {result.is_anomaly ? "Detected" : "None"}
                  </span>
                  <span className={styles.anomalyScore}>score {result.anomaly_score}</span>
                </div>
              </Card>

              <Card title="Alerts" style={{ marginTop: 14 }}>
                {buildAlerts(result).map((a, i) => <AlertItem key={i} {...a} />)}
              </Card>

              <Card title="Recommendation" style={{ marginTop: 14 }}>
                <div className={styles.recText}>{result.recommendation}</div>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
