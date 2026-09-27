import { Thermometer, RefreshCw, Radio } from 'lucide-react'

function Metric({ label, value, note, alert }) {
  return (
    <div className={`temp-metric ${alert ? 'temp-alert' : ''}`}>
      <span>{label}</span>
      <strong>{value == null ? '—' : `${Number(value).toFixed(1)} °C`}</strong>
      <small>{note}</small>
    </div>
  )
}

export default function TemperaturePanel({ data, history, onSimulate, busy }) {
  const points = [...history].reverse()
  const max = Math.max(...points.map(x => Number(x.human_reference_c || 0)), 38)
  const min = Math.min(...points.map(x => Number(x.human_reference_c || 0)), 35)
  const range = Math.max(max - min, 1)

  return (
    <section className="panel temperature-panel">
      <div className="panel-head">
        <div>
          <h2><Thermometer size={17}/> Temperature Monitoring</h2>
          <p>Thermal/sensor telemetry layer for the surveillance dashboard.</p>
        </div>
        <span className="engine-pill"><Radio size={12}/> {data?.sensor_mode || 'SIMULATION'}</span>
      </div>

      <div className="temperature-grid">
        <Metric
          label="Human reference"
          value={data?.human_reference_c}
          note="Reference value — not measured by RGB video"
          alert={data?.human_status === 'TEMPERATURE_ALERT'}
        />
        <Metric label="Ambient" value={data?.ambient_c} note="Environment" />
        <Metric label="Surface / ground" value={data?.surface_c} note="Thermal sensor" />
        <Metric label="Camera" value={data?.camera_c} note="Equipment telemetry" />
      </div>

      <div className="temperature-status-row">
        <span className={data?.human_status === 'TEMPERATURE_ALERT' ? 'temp-status alert' : 'temp-status'}>
          {data?.human_status === 'TEMPERATURE_ALERT' ? 'TEMPERATURE ALERT' : 'REFERENCE STATUS: NORMAL'}
        </span>
        <button className="secondary" onClick={() => onSimulate('normal')} disabled={busy}>
          <RefreshCw size={13}/> Simulate normal
        </button>
        <button className="secondary danger-button" onClick={() => onSimulate('alert')} disabled={busy}>
          <Thermometer size={13}/> Test alert
        </button>
      </div>

      <div className="temp-chart">
        <div className="temp-chart-title">Human reference trend · simulated sensor data</div>
        <div className="temp-bars">
          {points.map((item, index) => {
            const value = Number(item.human_reference_c || 0)
            const height = Math.max(8, Math.min(100, ((value - min) / range) * 100))
            return <i key={`${item.id}-${index}`} style={{ height: `${height}%` }} title={`${value.toFixed(1)} °C`} />
          })}
        </div>
        <div className="temp-axis"><span>{min.toFixed(1)} °C</span><span>{max.toFixed(1)} °C</span></div>
      </div>
    </section>
  )
}
