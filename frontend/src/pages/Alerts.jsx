import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAlerts, acknowledgeAlert, updateAlertStatus, deleteAlert } from '../services/api'
import { FiAlertTriangle, FiCheck, FiTrash2 } from 'react-icons/fi'
import './Alerts.css'

const Alerts = () => {
  const queryClient = useQueryClient()
  
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => getAlerts().then(res => res.data),
    refetchInterval: 5000,
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id) => acknowledgeAlert(id, 'admin'),
    onSuccess: () => {
      queryClient.invalidateQueries(['alerts'])
    },
  })

  const resolveMutation = useMutation({
    mutationFn: (id) => updateAlertStatus(id, 'RESOLVED'),
    onSuccess: () => {
      queryClient.invalidateQueries(['alerts'])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['alerts'])
    },
  })

  const getSeverityBadge = (severity) => {
    const classes = {
      CRITICAL: 'badge-critical',
      HIGH: 'badge-high',
      MEDIUM: 'badge-medium',
      LOW: 'badge-low',
      INFO: 'badge-info',
    }
    return classes[severity] || 'badge-info'
  }

  const getStatusBadge = (status) => {
    const classes = {
      NEW: 'badge-critical',
      ACKNOWLEDGED: 'badge-medium',
      IN_PROGRESS: 'badge-medium',
      RESOLVED: 'badge-success',
      FALSE_POSITIVE: 'badge-low',
      IGNORED: 'badge-low',
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
    <div className="alerts-page">
      <div className="page-header">
        <h1><FiAlertTriangle /> Security Alerts</h1>
        <p className="page-subtitle">{alerts?.length || 0} total alerts</p>
      </div>

      <div className="alerts-list">
        {alerts && alerts.length > 0 ? (
          alerts.map(alert => (
            <div key={alert.id} className="alert-card card">
              <div className="alert-header">
                <div>
                  <span className={`badge ${getSeverityBadge(alert.severity)}`}>
                    {alert.severity}
                  </span>
                  <span className={`badge ${getStatusBadge(alert.status)}`}>
                    {alert.status}
                  </span>
                </div>
                <span className="alert-time">
                  {new Date(alert.createdAt).toLocaleString()}
                </span>
              </div>
              
              <h3 className="alert-title">{alert.title}</h3>
              <p className="alert-description">{alert.description}</p>
              
              <div className="alert-details">
                {alert.sourceModule && (
                  <span><strong>Module:</strong> {alert.sourceModule}</span>
                )}
                {alert.sourceIp && (
                  <span><strong>Source:</strong> {alert.sourceIp}</span>
                )}
                {alert.targetIp && (
                  <span><strong>Target:</strong> {alert.targetIp}</span>
                )}
              </div>

              <div className="alert-actions">
                {alert.status === 'NEW' && (
                  <button
                    className="btn btn-primary"
                    onClick={() => acknowledgeMutation.mutate(alert.id)}
                    disabled={acknowledgeMutation.isLoading}
                  >
                    <FiCheck /> Acknowledge
                  </button>
                )}
                {(alert.status === 'NEW' || alert.status === 'ACKNOWLEDGED') && (
                  <button
                    className="btn btn-success"
                    onClick={() => resolveMutation.mutate(alert.id)}
                    disabled={resolveMutation.isLoading}
                  >
                    <FiCheck /> Resolve
                  </button>
                )}
                <button
                  className="btn btn-danger"
                  onClick={() => {
                    if (confirm('Delete this alert?')) {
                      deleteMutation.mutate(alert.id)
                    }
                  }}
                  disabled={deleteMutation.isLoading}
                >
                  <FiTrash2 /> Delete
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <FiAlertTriangle size={48} />
            <p>No alerts found</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Alerts
