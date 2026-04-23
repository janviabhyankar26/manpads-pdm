import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Overview   from "./pages/Overview";
import UnitDetail from "./pages/UnitDetail";
import Predict    from "./pages/Predict";
import styles     from "./App.module.css";

export default function App() {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <span className={styles.logoMark}>M</span>
          <div>
            <div className={styles.logoTitle}>MANPADS</div>
            <div className={styles.logoSub}>PdM System</div>
          </div>
        </div>

        <nav className={styles.nav}>
          <NavLink to="/"        className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem} end>
            <span className={styles.navIcon}>◈</span> Fleet Overview
          </NavLink>
          <NavLink to="/unit"    className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <span className={styles.navIcon}>◉</span> Unit Analysis
          </NavLink>
          <NavLink to="/predict" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <span className={styles.navIcon}>◎</span> Live Predict
          </NavLink>
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.footerDot} />
          <span>API connected</span>
        </div>
      </aside>

      <main className={styles.main}>
        <Routes>
          <Route path="/"        element={<Overview />}   />
          <Route path="/unit"    element={<UnitDetail />} />
          <Route path="/predict" element={<Predict />}    />
        </Routes>
      </main>
    </div>
  );
}
