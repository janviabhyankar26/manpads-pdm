import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getSummary, getUnits, getUnitPredictions } from "../api";
import { StatCard, HealthBadge, PageHeader, Card, Loading, ErrorMsg } from "../components/Components";
import styles from "./Pages.module.css";

export default function Overview() {
  const [summary, setSummary]   = useState(null);
  const [units,   setUnits]     = useState([]);
  const [fleet,   setFleet]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [sumRes, unitRes] = await Promise.all([getSummary(), getUnits()]);
        setSummary(sumRes.data);

        // Get last cycle prediction for each unit for fleet table
        const unitList = unitRes.data.units;
        setUnits(unitList);

        const results = await Promise.all(
          unitList.map(u => getUnitPredictions(u))
        );

        const fleetData = results.map((res, i) => {
          const d    = res.data;
          const last = d.cycles.length - 1;
          return {
            unit    : d.unit_id,
            health  : d.health[last],
            rul_bat : d.rul_battery[last],
            rul_seek: d.rul_seeker[last],
            rul_gyro: d.rul_gyro[last],
            anomalies: d.anomaly.filter(a => a === 1).length,
          };
        });
        setFleet(fleetData);
      } catch (e) {
        setError("Could not connect to API. Make sure the backend is running on port 8000.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <Loading />;
  if (error)   return <ErrorMsg message={error} />;

  const healthDist = [
    { label: "Healthy",  value: summary.healthy,  color: "#2d7a3a" },
    { label: "Warning",  value: summary.warning,   color: "#d4890a" },
    { label: "Critical", value: summary.critical,  color: "#c0392b" },
  ];

  return (
    <div>
      <PageHeader
        title="Fleet Overview"
        subtitle={`${summary.total_units} units monitored · ${summary.units_needing_service} units need service`}
      />

      {/* KPI Row */}
      <div className={styles.kpiGrid}>
        <StatCard label="Total units"           value={summary.total_units}           accentColor="#1a1a1a" />
        <StatCard label="Healthy"               value={summary.healthy}               accentColor="#2d7a3a" sub="units" />
        <StatCard label="Warning"               value={summary.warning}               accentColor="#d4890a" sub="units" />
        <StatCard label="Critical"              value={summary.critical}              accentColor="#c0392b" sub="units" />
        <StatCard label="Avg battery RUL"       value={`${summary.avg_rul_battery} hrs`} accentColor="#378ADD" />
        <StatCard label="Need service now"      value={summary.units_needing_service} accentColor="#EF9F27" sub="units" />
      </div>

      <div className={styles.twoCol} style={{ marginTop: 20 }}>
        {/* Health Distribution Chart */}
        <Card title="Fleet health distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={healthDist} barSize={48}>
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#999" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#bbb" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ border: "1px solid #e8e6e0", borderRadius: 8, fontSize: 12 }}
                cursor={{ fill: "#f5f4f0" }}
              />
              <Bar dataKey="value" radius={[5, 5, 0, 0]}>
                {healthDist.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Battery RUL Distribution */}
        <Card title="Battery RUL per unit (last cycle)">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={fleet.slice(0, 15)} barSize={12}>
              <XAxis dataKey="unit" tick={{ fontSize: 10, fill: "#bbb" }}
                tickFormatter={v => v.replace("STG-","")} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#bbb" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ border: "1px solid #e8e6e0", borderRadius: 8, fontSize: 12 }}
                cursor={{ fill: "#f5f4f0" }}
                formatter={(v) => [`${v} hrs`, "Battery RUL"]}
              />
              <Bar dataKey="rul_bat" radius={[3, 3, 0, 0]}>
                {fleet.slice(0, 15).map((d, i) => (
                  <Cell key={i} fill={d.rul_bat < 50 ? "#c0392b" : d.rul_bat < 150 ? "#d4890a" : "#378ADD"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Fleet Table */}
      <Card title="Unit status table" style={{ marginTop: 20 }}>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Unit ID</th>
                <th>Health</th>
                <th>RUL Battery</th>
                <th>RUL Seeker</th>
                <th>RUL Gyro</th>
                <th>Anomalies</th>
              </tr>
            </thead>
            <tbody>
              {fleet.map(u => (
                <tr key={u.unit}>
                  <td className={styles.monoCell}>{u.unit}</td>
                  <td><HealthBadge code={u.health} /></td>
                  <td className={u.rul_bat  < 50  ? styles.redCell : ""}>{u.rul_bat} hrs</td>
                  <td className={u.rul_seek < 30  ? styles.redCell : ""}>{u.rul_seek} hrs</td>
                  <td className={u.rul_gyro < 50  ? styles.redCell : ""}>{u.rul_gyro} hrs</td>
                  <td className={u.anomalies > 0  ? styles.warnCell : ""}>{u.anomalies}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
