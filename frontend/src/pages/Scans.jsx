import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getScans, initiateScan, cancelScan, deleteScan } from '../services/api'
import { FiActivity, FiX, FiTrash2, FiPlay } from 'react-icons/fi'
import './Scans.css'

const Scans = () => {
  const queryClient = useQueryClient()
  const [showNewScan, setShowNewScan] = useState(false)
  const [scanForm, setScanForm] = useState({
    type: 'NETWORK',
    target: '',
    scanProfile: 'default'
  })

  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => getScans().then(res => res.data),
    refetchInterval: 3000,
  })

  const initiateMutation = useMutation({
    mutationFn: (data) => initiateScan(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      setShowNewScan(false)
      setScanForm({ type: 'NETWORK', target: '', scanProfile: 'default' })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (id) => cancelScan(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteScan(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    initiateMutation.mutate(scanForm)
  }

  const getStatusBadge = (status) => {
    const classes = {
      PENDING: 'badge-medium',
      RUNNING: 'badge-info',
      COMPLETED: 'badge-success',
      FAILED: 'badge-critical',
      CANCELLED: 'badge-low',
    }
    return classes[status] || 'badge-info'
  }

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="scans-page">
      <div className="page-header">
        <div>
          <h1><FiActivity /> Security Scans</h1>
          <p className="page-subtitle">{scans?.length || 0} total scans</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowNewScan(!showNewScan)}
        >
          <FiPlay /> New Scan
        </button>
      </div>

      {showNewScan && (
        <div className="card new-scan-form">
          <h3>Initiate New Scan</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Scan Type</label>
              <select
                value={scanForm.type}
                onChange={(e) => setScanForm({...scanForm, type: e.target.value})}
                required
              >
                <option value="NETWORK">Network Scan</option>
                <option value="PORT">Port Scan</option>
                <option value="VULNERABILITY">Vulnerability Scan</option>
                <option value="MALWARE">Malware Scan</option>
                <option value="FULL">Full Scan</option>
              </select>
            </div>
            <div className="form-group">
              <label>Target (IP/Domain/Range)</label>
              <input
                type="text"
                value={scanForm.target}
                onChange={(e) => setScanForm({...scanForm, target: e.target.value})}
                placeholder="192.168.1.0/24 or example.com"
                required
              />
            </div>
            <div className="form-group">
              <label>Scan Profile</label>
              <select
                value={scanForm.scanProfile}
                onChange={(e) => setScanForm({...scanForm, scanProfile: e.target.value})}
              >
                <option value="default">Default</option>
                <option value="quick">Quick</option>
                <option value="thorough">Thorough</option>
                <option value="stealth">Stealth</option>
              </select>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-success" disabled={initiateMutation.isLoading}>
                Start Scan
              </button>
              <button type="button" className="btn btn-danger" onClick={() => setShowNewScan(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="scans-list">
        {scans && scans.length > 0 ? (
          scans.map(scan => (
            <div key={scan.id} className="scan-card card">
              <div className="scan-header">
                <div>
                  <span className={`badge ${getStatusBadge(scan.status)}`}>
                    {scan.status}
                  </span>
                  <span className="badge badge-info">{scan.type}</span>
                </div>
                <span className="scan-time">
                  {new Date(scan.startedAt).toLocaleString()}
                </span>
              </div>
              
              <h3 className="scan-title">Scan #{scan.id} - {scan.target}</h3>
              
              <div className="scan-details">
                <span><strong>Profile:</strong> {scan.scanProfile || 'default'}</span>
                {scan.startedBy && (
                  <span><strong>Started by:</strong> {scan.startedBy}</span>
                )}
                {scan.durationSeconds && (
                  <span><strong>Duration:</strong> {scan.durationSeconds}s</span>
                )}
                {scan.findingsCount !== null && (
                  <span><strong>Findings:</strong> {scan.findingsCount}</span>
                )}
                {scan.vulnerabilitiesFound !== null && (
                  <span><strong>Vulnerabilities:</strong> {scan.vulnerabilitiesFound}</span>
                )}
                {scan.threatsDetected !== null && (
                  <span><strong>Threats:</strong> {scan.threatsDetected}</span>
                )}
              </div>

              {scan.errorMessage && (
                <div className="error-box">
                  <strong>Error:</strong> {scan.errorMessage}
                </div>
              )}

              <div className="scan-actions">
                {(scan.status === 'RUNNING' || scan.status === 'PENDING') && (
                  <button
                    className="btn btn-danger"
                    onClick={() => cancelMutation.mutate(scan.id)}
                    disabled={cancelMutation.isLoading}
                  >
                    <FiX /> Cancel
                  </button>
                )}
                {(scan.status === 'COMPLETED' || scan.status === 'FAILED' || scan.status === 'CANCELLED') && (
                  <button
                    className="btn btn-danger"
                    onClick={() => {
                      if (confirm('Delete this scan?')) {
                        deleteMutation.mutate(scan.id)
                      }
                    }}
                    disabled={deleteMutation.isLoading}
                  >
                    <FiTrash2 /> Delete
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <FiActivity size={48} />
            <p>No scans found</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Scans
