export default function StatCard({ label, value, tone = 'normal', icon: Icon }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>{Icon && <Icon size={20} />}</div>
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
      </div>
    </div>
  )
}
