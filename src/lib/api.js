export const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { message = (await response.json()).detail || message } catch {}
    throw new Error(message)
  }
  return response.json()
}

export const getSummary = () => request('/api/dashboard/summary')
export const getEvents = () => request('/api/events?limit=100')
export const getTemperature = () => request('/api/temperature/current')
export const getTemperatureHistory = () => request('/api/temperature/history?limit=20')
export const simulateTemperature = (scenario = 'normal') => request(`/api/temperature/simulate?scenario=${scenario}`, { method: 'POST' })
export const uploadVideo = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request('/api/analyze/upload', { method: 'POST', body: form })
}
export const getJob = (id) => request(`/api/jobs/${id}`)
export const mediaUrl = (file) => `${API}/api/media/${encodeURIComponent(file)}`
export const exportUrl = () => `${API}/api/events/export.csv`
