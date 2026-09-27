import { useEffect, useRef, useState } from 'react'
import { Activity, Camera, Download, FileVideo, Shield, Upload, Video, Wifi, Zap } from 'lucide-react'
import EventTable from './components/EventTable'
import StatCard from './components/StatCard'
import TemperaturePanel from './components/TemperaturePanel'
import { API, exportUrl, getEvents, getJob, getSummary, getTemperature, getTemperatureHistory, mediaUrl, simulateTemperature, uploadVideo } from './lib/api'
import './styles.css'

export default function App() {
  const [summary, setSummary] = useState({ total_events: 0, high_severity: 0, medium_severity: 0, cameras_online: 0 })
  const [events, setEvents] = useState([])
  const [file, setFile] = useState(null)
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [temperature, setTemperature] = useState(null)
  const [temperatureHistory, setTemperatureHistory] = useState([])
  const [temperatureBusy, setTemperatureBusy] = useState(false)
  const inputRef = useRef(null)

  const refresh = async () => {
    try {
      const [s, e, t, th] = await Promise.all([getSummary(), getEvents(), getTemperature(), getTemperatureHistory()])
      setSummary(s); setEvents(e); setTemperature(t); setTemperatureHistory(th)
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { refresh(); const timer = setInterval(refresh, 5000); return () => clearInterval(timer) }, [])

  const runTemperatureSimulation = async (scenario) => {
    setTemperatureBusy(true)
    try {
      const reading = await simulateTemperature(scenario)
      setTemperature(reading)
      setTemperatureHistory(await getTemperatureHistory())
    } catch (err) { setError(err.message) }
    finally { setTemperatureBusy(false) }
  }

  const startAnalysis = async () => {
    if (!file) return
    setError(''); setBusy(true); setJob(null)
    try {
      const created = await uploadVideo(file)
      setJob(created)
      const timer = setInterval(async () => {
        try {
          const current = await getJob(created.job_id)
          setJob(current)
          if (['COMPLETED', 'FAILED'].includes(current.status)) {
            clearInterval(timer); setBusy(false); refresh()
          }
        } catch (err) { clearInterval(timer); setBusy(false); setError(err.message) }
      }, 1000)
    } catch (err) { setBusy(false); setError(err.message) }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Shield size={24}/></div><div><strong>BorderVision</strong><span>AI Analytics</span></div></div>
        <nav>
          <a className="active"><Activity size={18}/> Operations Dashboard</a>
          <a><Camera size={18}/> Camera Monitoring</a>
          <a><Zap size={18}/> AI Analytics</a>
        </nav>
        <div className="side-note"><span className="live-dot"/> System ready<br/><small>YOLO11 inference engine</small></div>
      </aside>

      <main className="main">
        <header className="topbar"><div><div className="eyebrow">SMART BORDER SURVEILLANCE</div><h1>Operations Dashboard</h1></div><div className="system-status"><Wifi size={15}/> Backend <b>ONLINE</b></div></header>

        <section className="stats-grid">
          <StatCard label="Total events" value={summary.total_events} icon={Activity}/>
          <StatCard label="High severity" value={summary.high_severity} tone="danger" icon={Shield}/>
          <StatCard label="Medium severity" value={summary.medium_severity} tone="warning" icon={Zap}/>
          <StatCard label="Cameras online" value={summary.cameras_online} tone="success" icon={Camera}/>
        </section>

        <section className="workspace-grid">
          <div className="panel upload-panel">
            <div className="panel-head"><div><h2>Video Intelligence</h2><p>Analyze uploaded surveillance footage with YOLO11 tracking.</p></div><span className="engine-pill">YOLO11</span></div>
            <div className="dropzone" onClick={() => inputRef.current?.click()}>
              <input ref={inputRef} type="file" accept="video/*,.mkv" hidden onChange={e => setFile(e.target.files?.[0] || null)}/>
              <div className="upload-icon"><FileVideo size={28}/></div>
              <strong>{file ? file.name : 'Select surveillance video'}</strong>
              <span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB selected` : 'MP4, AVI, MOV, MKV, WebM • up to 500 MB'}</span>
            </div>
            <button className="primary" disabled={!file || busy} onClick={startAnalysis}><Upload size={17}/> {busy ? 'Analyzing…' : 'Start AI Analysis'}</button>
            {job && <div className="job-box"><div className="job-row"><span>{job.status}</span><b>{Math.round(job.progress || 0)}%</b></div><div className="progress"><i style={{width: `${job.progress || 0}%`}}/></div><small>{job.message}</small>{job.output_file && <a className="result-link" href={mediaUrl(job.output_file)} target="_blank"><Video size={15}/> Open annotated video</a>}</div>}
            {error && <div className="error">{error}</div>}
          </div>

          <div className="panel architecture-panel">
            <div className="panel-head"><div><h2>AI Monitoring Stack</h2><p>Current analytics pipeline</p></div></div>
            <div className="pipeline">
              <div><span className="node active">01</span><b>Video Input</b><small>Upload / RTSP ready</small></div><i/>
              <div><span className="node active">02</span><b>YOLO11</b><small>Detection + tracking</small></div><i/>
              <div><span className="node active">03</span><b>Rule Engine</b><small>Zone + line alerts</small></div><i/>
              <div><span className="node active">04</span><b>Event Store</b><small>SQLite audit log</small></div>
            </div>
            <div className="capabilities"><span>Person detection</span><span>Vehicle detection</span><span>Zone intrusion</span><span>Line crossing</span><span>Event export</span></div>
          </div>
        </section>

        <TemperaturePanel data={temperature} history={temperatureHistory} onSimulate={runTemperatureSimulation} busy={temperatureBusy} />

        <section className="panel events-panel">
          <div className="panel-head"><div><h2>Recent Security Events</h2><p>AI-generated detections and rule-based alerts</p></div><a className="secondary" href={exportUrl()}><Download size={15}/> Export CSV</a></div>
          <EventTable events={events}/>
        </section>

        <footer>BorderVision AI • SIH prototype • AI-assisted analytics only — human review remains required for operational decisions.</footer>
      </main>
    </div>
  )
}
