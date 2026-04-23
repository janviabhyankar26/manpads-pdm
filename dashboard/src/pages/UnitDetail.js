import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from "recharts";
import { getUnits, getUnitPredictions } from "../api";
import { HealthBadge, ProgressBar, AlertItem, PageHeader, Card, Loading, ErrorMsg } from "../components/Components";
import styles from "./Pages.module.css";

const MAX = { battery: 537, seeker: 1164, gyro: 2205 };

function buildAlerts(lastRow) {
  const alerts = [];
  if (!lastRow) return alerts;
  if (lastRow.anomaly === 1)
    alerts.push({ severity: "crit", title: "Anomaly detected", description: "Unusual sensor pattern in last cycle." });
  if (lastRow.rul_battery < 50)
    alerts.push({ severity: "crit", title: "Battery critical", description: `Only ${lastRow.rul_battery} hrs remaining.` });
  else if (lastRow.rul_battery < 150)
    alerts.push({ severity: "warn", title: "Battery low", description: `${lastRow.rul_battery} hrs remaining.` });
  if (lastRow.rul_seeker < 30)
    alerts.push({ severity: "crit", title: "Seeker coolant critical", description: `${lastRow.rul_seeker} hrs remaining.` });
  if (lastRow.rul_gyro < 50)
    alerts.push({ severity: "warn", title: "Gyro RUL low", description: `${lastRow.rul_gyro} hrs remaining.` });
  if (alerts.length === 0)
    alerts.push({ severity: "ok", title: "All systems nominal", description: "No active faults detected." });
  return alerts;
}

export default function UnitDetail() {
  const [units,     setUnits]     = useState([]);
  const [selected,  setSelected]  = useState("");
  const [data,      setData]      = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");

  useEffect(() => {
    getUnits()
      .then(r => { setUnits(r.data.units); setSelected(r.data.units[0]); })
      .catch(() => setError("Cannot connect to API."));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setData(null);
    getUnitPredictions(selected)
      .then(r => setData(r.data))
      .catch(() => setError("Failed to load unit data."))
      .finally(() => setLoading(false));
  }, [selected]);

  const chartData = data
    ? data.cycles.map((c, i) => ({
        cycle      : c,
        rul_battery: data.rul_battery[i],
        rul_seeker : data.rul_seeker[i],
        rul_gyro   : data.rul_gyro[i],
        health     : data.health[i],
        anomaly    : data.anomaly[i],
      }))
    : [];

  const lastRow  = chartData.length ? chartData[chartData.length - 1] : null;
  const alerts   = buildAlerts(lastRow);

  const battPct  = lastRow ? Math.round((lastRow.rul_battery / MAX.battery)  * 100) : 0;
  const seekPct  = lastRow ? Math.round((lastRow.rul_seeker  / MAX.seeker)   * 100) : 0;
  const gyroPct  = lastRow ? Math.round((lastRow.rul_gyro    / MAX.gyro)     * 100) : 0;

  return (
    <div>
      <PageHeader title="Unit Analysis" subtitle="Select a unit to view full cycle predictions and RUL trends." />

      {error && <ErrorMsg message={error} />}

      {/* Unit selector */}
      <div className={styles.unitSelector}>
        {units.map(u => (
          <button
            key={u}
            className={`${styles.unitBtn} ${selected === u ? styles.unitBtnActive : ""}`}
            onClick={() => setSelected(u)}
          >
            {u.replace("STG-", "")}
          </button>
        ))}
      </div>

      {loading && <Loading />}

      {data && lastRow && (
        <>
          {/* KPI row */}
          <div className={styles.kpiGrid} style={{ marginTop: 20 }}>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Health state</div>
              <HealthBadge code={lastRow.health} />
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>RUL · Battery</div>
              <div className={styles.statVal}>{lastRow.rul_battery} hrs</div>
              <ProgressBar pct={battPct} />
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>RUL · Seeker</div>
              <div className={styles.statVal}>{lastRow.rul_seeker} hrs</div>
              <ProgressBar pct={seekPct} />
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>RUL · Gyro</div>
              <div className={styles.statVal}>{lastRow.rul_gyro} hrs</div>
              <ProgressBar pct={gyroPct} />
            </div>
          </div>

          <div className={styles.twoCol} style={{ marginTop: 20 }}>
            {/* RUL Trend Chart */}
            <Card title="RUL trend over all cycles">
              <div style={{ display: "flex", gap: 16, marginBottom: 10 }}>
                {[["Battery","#378ADD"],["Seeker","#1D9E75"],["Gyro","#7F77DD"]].map(([label,color])=>(
                  <span key={label} style={{ display:"flex", alignItems:"center", gap:5, fontSize:11, color:"#888" }}>
                    <span style={{ width:10, height:10, borderRadius:2, background:color, display:"inline-block" }} />
                    {label}
                  </span>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <XAxis dataKey="cycle" tick={{ fontSize: 11, fill: "#bbb" }} axisLine={false} tickLine={false} interval={49} />
                  <YAxis tick={{ fontSize: 11, fill: "#bbb" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ border: "1px solid #e8e6e0", borderRadius: 8, fontSize: 12 }} />
                  <ReferenceLine y={150} stroke="#d4890a" strokeDasharray="4 3" strokeWidth={1} />
                  <Line type="monotone" dataKey="rul_battery" stroke="#378ADD" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="rul_seeker"  stroke="#1D9E75" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="rul_gyro"    stroke="#7F77DD" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            {/* Alerts */}
            <Card title="Active alerts">
              {alerts.map((a, i) => <AlertItem key={i} {...a} />)}
            </Card>
          </div>

          {/* Health over cycles */}
          <Card title="Health state over all cycles" style={{ marginTop: 20 }}>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={chartData}>
                <XAxis dataKey="cycle" tick={{ fontSize: 11, fill: "#bbb" }} axisLine={false} tickLine={false} interval={49} />
                <YAxis ticks={[0,1,2]} tickFormatter={v => ["Healthy","Warning","Critical"][v]} tick={{ fontSize: 10, fill: "#bbb" }} axisLine={false} tickLine={false} width={60} />
                <Tooltip
                  contentStyle={{ border: "1px solid #e8e6e0", borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [["Healthy","Warning","Critical"][v], "Health"]}
                />
                <Line type="stepAfter" dataKey="health" stroke="#1a1a1a" dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}
    </div>
  );
}
