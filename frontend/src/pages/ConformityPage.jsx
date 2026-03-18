import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, AlertTriangle, Info, Download, Filter, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../services/api'

const SEVERITY_CONFIG = {
  ERROR:   { color: '#E63946', bg: '#FEE2E2', icon: AlertCircle, label: 'Erreur' },
  WARNING: { color: '#F4A261', bg: '#FEF3C7', icon: AlertTriangle, label: 'Avertissement' },
  INFO:    { color: '#457B9D', bg: '#DBEAFE', icon: Info, label: 'Information' },
}

export default function ConformityPage() {
  const [anomalies, setAnomalies] = useState([])
  const [stats, setStats] = useState({ total: 0, conformes: 0, alertes: 0, erreurs: 0 })
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/validation/results')
      const data = res.data
      setAnomalies(data.anomalies || [])
      setStats(data.stats || { total: 0, conformes: 0, alertes: 0, erreurs: 0 })
    } catch {
      setAnomalies([])
      setStats({ total: 0, conformes: 0, alertes: 0, erreurs: 0 })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const filtered = filterSeverity === 'all'
    ? anomalies
    : anomalies.filter(a => a.severity === filterSeverity)

  const chartData = anomalies.reduce((acc, a) => {
    const existing = acc.find(d => d.type === a.rule_id)
    if (existing) existing.count++
    else acc.push({ type: a.rule_id, count: 1 })
    return acc
  }, [])

  const conformePercent = stats.total > 0 ? Math.round((stats.conformes / stats.total) * 100) : 0

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Dashboard Conformité</h1>
        <button className="btn btn-outline" onClick={fetchData} title="Rafraîchir">
          <RefreshCw size={16} />
        </button>
      </div>

      {/* KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="value">{stats.total}</div>
          <div className="label">Documents traités</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#00C896' }}>{conformePercent}%</div>
          <div className="label">Documents conformes</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#F4A261' }}>{stats.alertes}</div>
          <div className="label">Alertes actives</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#E63946' }}>{stats.erreurs}</div>
          <div className="label">Erreurs bloquantes</div>
        </div>
      </div>

      {/* Graphique */}
      {chartData.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 16 }}>Anomalies par type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="type" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#1B2A4A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Filtres */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Filter size={16} color="#718096" />
          {['all', 'ERROR', 'WARNING', 'INFO'].map(sev => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`btn ${filterSeverity === sev ? 'btn-primary' : 'btn-outline'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              {sev === 'all' ? 'Toutes' : SEVERITY_CONFIG[sev]?.label}
            </button>
          ))}
        </div>
        <button className="btn btn-outline" style={{ fontSize: 12 }}>
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Liste des anomalies */}
      {loading ? (
        <p style={{ textAlign: 'center', color: '#718096', padding: 40 }}>Chargement...</p>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 40, color: '#718096' }}>
          <AlertCircle size={40} color="#CBD5E0" style={{ margin: '0 auto 12px' }} />
          <p>Aucune anomalie détectée.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map((anomaly, i) => {
            const config = SEVERITY_CONFIG[anomaly.severity] || SEVERITY_CONFIG.INFO
            const Icon = config.icon
            return (
              <div
                key={i}
                className="card"
                style={{
                  borderLeft: `4px solid ${config.color}`,
                  padding: 16,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <Icon size={20} color={config.color} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{anomaly.rule_id}</span>
                      <span className={`badge badge-${anomaly.severity === 'ERROR' ? 'danger' : anomaly.severity === 'WARNING' ? 'warning' : 'info'}`}>
                        {config.label}
                      </span>
                    </div>
                    <p style={{ fontSize: 14, color: '#2D3748', marginBottom: 8 }}>
                      {anomaly.message}
                    </p>
                    {anomaly.concerned_document_ids && (
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {anomaly.concerned_document_ids.map(docId => (
                          <span key={docId} style={{
                            padding: '2px 8px', borderRadius: 4,
                            background: '#F0F4F8', fontSize: 12, color: '#2D3748',
                          }}>
                            {docId}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-outline" style={{ padding: '4px 10px', fontSize: 12 }}>Ignorer</button>
                    <button className="btn btn-danger" style={{ padding: '4px 10px', fontSize: 12 }}>Escalader</button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
