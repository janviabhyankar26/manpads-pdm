import React from "react";
import styles from "./Components.module.css";

/* ── StatCard ─────────────────────────────────────────────── */
export function StatCard({ label, value, sub, accentColor }) {
  return (
    <div className={styles.statCard}>
      {accentColor && <div className={styles.accent} style={{ background: accentColor }} />}
      <div className={styles.statLabel}>{label}</div>
      <div className={styles.statValue}>{value ?? "—"}</div>
      {sub && <div className={styles.statSub}>{sub}</div>}
    </div>
  );
}

/* ── HealthBadge ──────────────────────────────────────────── */
export function HealthBadge({ code }) {
  const map = {
    0: { label: "Healthy",  cls: styles.ok   },
    1: { label: "Warning",  cls: styles.warn  },
    2: { label: "Critical", cls: styles.crit  },
  };
  const { label, cls } = map[code] ?? { label: "Unknown", cls: "" };
  return <span className={`${styles.badge} ${cls}`}>{label}</span>;
}

/* ── ProgressBar ──────────────────────────────────────────── */
export function ProgressBar({ pct }) {
  const color = pct > 60 ? "#2d7a3a" : pct > 30 ? "#d4890a" : "#c0392b";
  return (
    <div className={styles.track}>
      <div className={styles.fill} style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

/* ── AlertItem ────────────────────────────────────────────── */
export function AlertItem({ severity, title, description }) {
  const cls = { crit: styles.alertCrit, warn: styles.alertWarn, ok: styles.alertOk };
  const icon = { crit: "!", warn: "~", ok: "✓" };
  return (
    <div className={styles.alertRow}>
      <div className={`${styles.alertIcon} ${cls[severity]}`}>{icon[severity]}</div>
      <div className={styles.alertBody}>
        <div className={styles.alertTitle}>{title}</div>
        <div className={styles.alertDesc}>{description}</div>
      </div>
    </div>
  );
}

/* ── PageHeader ───────────────────────────────────────────── */
export function PageHeader({ title, subtitle }) {
  return (
    <div className={styles.pageHeader}>
      <h1 className={styles.pageTitle}>{title}</h1>
      {subtitle && <p className={styles.pageSub}>{subtitle}</p>}
    </div>
  );
}

/* ── Card ─────────────────────────────────────────────────── */
export function Card({ title, children, style }) {
  return (
    <div className={styles.card} style={style}>
      {title && <div className={styles.cardTitle}>{title}</div>}
      {children}
    </div>
  );
}

/* ── Loading / Error ──────────────────────────────────────── */
export function Loading() {
  return <div className={styles.loading}>Loading...</div>;
}

export function ErrorMsg({ message }) {
  return <div className={styles.error}>{message}</div>;
}
