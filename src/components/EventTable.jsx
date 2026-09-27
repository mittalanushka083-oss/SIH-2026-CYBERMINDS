import { AlertTriangle, ShieldAlert } from 'lucide-react'

export default function EventTable({ events }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Time</th><th>Event</th><th>Object</th><th>Confidence</th><th>Severity</th></tr>
        </thead>
        <tbody>
          {events.length === 0 ? <tr><td colSpan="5" className="empty">No events recorded yet.</td></tr> : events.map(e => (
            <tr key={e.id}>
              <td>{new Date(e.created_at).toLocaleString()}</td>
              <td><span className="event-name">{e.event_type.replaceAll('_', ' ')}</span><small>{e.message}</small></td>
              <td>{e.object_class || '—'} {e.track_id != null ? `#${e.track_id}` : ''}</td>
              <td>{e.confidence != null ? `${(e.confidence * 100).toFixed(1)}%` : '—'}</td>
              <td><span className={`badge ${e.severity.toLowerCase()}`}>{e.severity === 'HIGH' ? <ShieldAlert size={13}/> : <AlertTriangle size={13}/>} {e.severity}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
