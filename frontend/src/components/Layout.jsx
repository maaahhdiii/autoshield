import React from 'react'
import { NavLink } from 'react-router-dom'
import { FiHome, FiAlertTriangle, FiShield, FiActivity } from 'react-icons/fi'
import './Layout.css'

const Layout = ({ children }) => {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <FiShield className="logo-icon" />
          <h1>AutoShield</h1>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className="nav-link">
            <FiHome /> Dashboard
          </NavLink>
          <NavLink to="/alerts" className="nav-link">
            <FiAlertTriangle /> Alerts
          </NavLink>
          <NavLink to="/threats" className="nav-link">
            <FiShield /> Threats
          </NavLink>
          <NavLink to="/scans" className="nav-link">
            <FiActivity /> Scans
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <p>Version 2.0.0</p>
        </div>
      </aside>
      <main className="main-content">
        <div className="container">
          {children}
        </div>
      </main>
    </div>
  )
}

export default Layout
