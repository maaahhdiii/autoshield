import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Basic auth - in production, use proper authentication
  auth: {
    username: 'admin',
    password: 'admin123'
  }
})

// Dashboard
export const getDashboard = () => api.get('/dashboard')

// Alerts
export const getAlerts = () => api.get('/alerts')
export const getAlertById = (id) => api.get(`/alerts/${id}`)
export const createAlert = (data) => api.post('/alerts', data)
export const updateAlertStatus = (id, status) => 
  api.put(`/alerts/${id}/status`, null, { params: { status } })
export const acknowledgeAlert = (id, acknowledgedBy) =>
  api.put(`/alerts/${id}/acknowledge`, null, { params: { acknowledgedBy } })
export const deleteAlert = (id) => api.delete(`/alerts/${id}`)

// Threats
export const getThreats = () => api.get('/threats')
export const getThreatById = (id) => api.get(`/threats/${id}`)
export const createThreat = (data) => api.post('/threats', data)
export const updateThreatStatus = (id, status) =>
  api.put(`/threats/${id}/status`, null, { params: { status } })
export const applyMitigation = (id, mitigationDetails) =>
  api.put(`/threats/${id}/mitigate`, { mitigationDetails })
export const deleteThreat = (id) => api.delete(`/threats/${id}`)

// Scans
export const getScans = () => api.get('/scans')
export const getScanById = (id) => api.get(`/scans/${id}`)
export const initiateScan = (data) => api.post('/scans', data)
export const cancelScan = (id) => api.put(`/scans/${id}/cancel`)
export const deleteScan = (id) => api.delete(`/scans/${id}`)

// Health
export const getHealth = () => api.get('/health')

export default api
