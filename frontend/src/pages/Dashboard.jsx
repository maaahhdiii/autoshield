import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDashboard } from '../services/api'
import { FiAlertTriangle, FiShield, FiActivity, FiCheckCircle } from 'react-icons/fi'
import './Dashboard.css'

const Dashboard = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard().then(res => res.data),
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-message">
        <p>Failed to load dashboard data</p>
      </div>
    )
  }

  const stats = data?.statistics || {}
  const health = data?.systemHealth || {}

  return (
    <div className="dashboard">
      <h1>Security Dashboard</h1>
      
      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card critical">
          <FiAlertTriangle className="stat-icon" />
          <div className="stat-content">
            <h3>Critical Alerts</h3>
            <p className="stat-value">{stats.criticalAlerts || 0}</p>
          </div>
        </div>
        
        <div className="stat-card warning">
          <FiAlertTriangle className="stat-icon" />
          <div className="stat-content">
            <h3>Total Alerts</h3>
            <p className="stat-value">{stats.totalAlerts || 0}</p>
          </div>
        </div>
        
        <div className="stat-card danger">
          <FiShield className="stat-icon" />
          <div className="stat-content">
            <h3>Active Threats</h3>
            <p className="stat-value">{stats.activeThreats || 0}</p>
          </div>
        </div>
        
        <div className="stat-card success">
          <FiCheckCircle className="stat-icon" />
          <div className="stat-content">
            <h3>Mitigated Threats</h3>
            <p className="stat-value">{stats.mitigatedThreats || 0}</p>
          </div>
        </div>
        
        <div className="stat-card info">
          <FiActivity className="stat-icon" />
          <div className="stat-content">
            <h3>Completed Scans</h3>
            <p className="stat-value">{stats.completedScans || 0}</p>
          </div>
        </div>
        
        <div className="stat-card info">
          <FiActivity className="stat-icon" />
          <div className="stat-content">
            <h3>Running Scans</h3>
            <p className="stat-value">{stats.runningScans || 0}</p>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="card">
        <h2>System Health</h2>
        <div className="health-grid">
          <div className="health-item">
            <span className="health-label">Python AI Service</span>
            <span className={`health-status ${health.pythonAiStatus?.toLowerCase()}`}>
              {health.pythonAiStatus || 'UNKNOWN'}
            </span>
          </div>
          <div className="health-item">
            <span className="health-label">Kali MCP Service</span>
            <span className={`health-status ${health.kaliMcpStatus?.toLowerCase()}`}>
              {health.kaliMcpStatus || 'UNKNOWN'}
            </span>
          </div>
          <div className="health-item">
            <span className="health-label">Database</span>
            <span className={`health-status ${health.databaseStatus?.toLowerCase()}`}>
              {health.databaseStatus || 'UNKNOWN'}
            </span>
          </div>
          <div className="health-item">
            <span className="health-label">Overall Status</span>
            <span className={`health-status ${health.overallStatus?.toLowerCase()}`}>
              {health.overallStatus || 'UNKNOWN'}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <a href="/scans" className="btn btn-primary">
            <FiActivity /> Start New Scan
          </a>
          <a href="/alerts" className="btn btn-primary">
            <FiAlertTriangle /> View All Alerts
          </a>
          <a href="/threats" className="btn btn-primary">
            <FiShield /> Manage Threats
          </a>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
