import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getThreats, updateThreatStatus, applyMitigation, deleteThreat } from '../services/api'
import { FiShield, FiCheck, FiTrash2 } from 'react-icons/fi'
import './Threats.css'

const Threats = () => {
  const queryClient = useQueryClient()
  
  const { data: threats, isLoading } = useQuery({
    queryKey: ['threats'],
    queryFn: () => getThreats().then(res => res.data),
    refetchInterval: 5000,
  })

  const mitigateMutation = useMutation({
    mutationFn: (id) => applyMitigation(id, 'Automated mitigation applied'),
    onSuccess: () => {
      queryClient.invalidateQueries(['threats'])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteThreat(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['threats'])
    },
  })

  const getSeverityBadge = (severity) => {
    const classes = {
      CRITICAL: 'badge-critical',
      HIGH: 'badge-high',
      MEDIUM: 'badge-medium',
      LOW: 'badge-low',
    }
    return classes[severity] || 'badge-info'
  }

  const getStatusBadge = (status) => {
    const classes = {
      ACTIVE: 'badge-critical',
      MITIGATED: 'badge-success',
      MONITORING: 'badge-medium',
      FALSE_POSITIVE: 'badge-low',
      RESOLVED: 'badge-success',
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
    <div className="threats-page">
      <div className="page-header">
        <h1><FiShield /> Threat Intelligence</h1>
        <p className="page-subtitle">{threats?.length || 0} total threats detected</p>
      </div>

      <div className="threats-list">
        {threats && threats.length > 0 ? (
          threats.map(threat => (
            <div key={threat.id} className="threat-card card">
              <div className="threat-header">
                <div>
                  <span className={`badge ${getSeverityBadge(threat.severity)}`}>
                    {threat.severity}
                  </span>
                  <span className={`badge ${getStatusBadge(threat.status)}`}>
                    {threat.status}
                  </span>
                  <span className="badge badge-info">{threat.type}</span>
                </div>
                <span className="threat-time">
                  {new Date(threat.detectedAt).toLocaleString()}
                </span>
              </div>
              
              <h3 className="threat-title">{threat.name}</h3>
              <p className="threat-description">{threat.description}</p>
              
              <div className="threat-details">
                {threat.sourceIp && (
                  <span><strong>Source IP:</strong> {threat.sourceIp}</span>
                )}
                {threat.targetIp && (
                  <span><strong>Target IP:</strong> {threat.targetIp}</span>
                )}
                {threat.targetPort && (
                  <span><strong>Port:</strong> {threat.targetPort}</span>
                )}
                {threat.detectionMethod && (
                  <span><strong>Detection:</strong> {threat.detectionMethod}</span>
                )}
                {threat.confidenceScore && (
                  <span><strong>Confidence:</strong> {(threat.confidenceScore * 100).toFixed(0)}%</span>
                )}
              </div>

              {threat.indicators && (
                <div className="threat-indicators">
                  <strong>Indicators:</strong>
                  <p>{threat.indicators}</p>
                </div>
              )}

              {threat.mitigationApplied && threat.mitigationDetails && (
                <div className="mitigation-info">
                  <FiCheck /> <strong>Mitigation Applied:</strong> {threat.mitigationDetails}
                </div>
              )}

              <div className="threat-actions">
                {threat.status === 'ACTIVE' && !threat.mitigationApplied && (
                  <button
                    className="btn btn-success"
                    onClick={() => mitigateMutation.mutate(threat.id)}
                    disabled={mitigateMutation.isLoading}
                  >
                    <FiShield /> Apply Mitigation
                  </button>
                )}
                <button
                  className="btn btn-danger"
                  onClick={() => {
                    if (confirm('Delete this threat?')) {
                      deleteMutation.mutate(threat.id)
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
            <FiShield size={48} />
            <p>No threats detected</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Threats
