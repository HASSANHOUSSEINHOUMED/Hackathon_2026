import { useState, useEffect, useCallback } from 'react'
import { FileText, Image, Clock, CheckCircle, AlertTriangle, XCircle, Trash2, RefreshCw, Eye, Sparkles, Loader } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  raw: { color: '#718096', label: 'En attente' },
  ocr_done: { color: '#457B9D', label: 'OCR terminé' },
  validated: { color: '#F4A261', label: 'Validé' },
  llm_refined: { color: '#8B5CF6', label: 'IA raffiné' },
  curated: { color: '#00C896', label: 'Finalisé' },
}

const TYPE_COLORS = {
  facture: '#E63946',
  devis: '#F4A261',
  kbis: '#2A9D8F',
  urssaf: '#457B9D',
  siret: '#6D6875',
  rib: '#1B2A4A',
  inconnu: '#CBD5E0',
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState('all')
  const [expanded, setExpanded] = useState(null)
  const [extracting, setExtracting] = useState(null)
  const [llmAvailable, setLlmAvailable] = useState(false)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const params = filterType !== 'all' ? `?type=${filterType}&limit=100` : '?limit=100'
      const res = await api.get(`/documents${params}`)
      setDocuments(res.data.documents || [])
      setTotal(res.data.total || 0)
    } catch {
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [filterType])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  useEffect(() => {
    api.get('/llm/status').then(res => setLlmAvailable(res.data.available)).catch(() => {})
  }, [])

  const handleReextract = async (docId, fileName) => {
    setExtracting(docId)
    try {
      const res = await api.post(`/llm/reextract/${docId}`, {}, { timeout: 60000 })
      const data = res.data
      toast.success(
        `${fileName} re-extrait par IA (${data.new_type}, confiance ${Math.round((data.confidence || 0) * 100)}%, ${data.tokens_used} tokens)`,
        { duration: 5000 }
      )
      fetchDocuments()
    } catch (err) {
      const msg = err.response?.data?.error || err.message
      toast.error(`Erreur IA : ${msg}`)
    } finally {
      setExtracting(null)
    }
  }

  const handleDelete = async (docId) => {
    try {
      await api.delete(`/documents/${docId}`)
      toast.success('Document supprimé')
      fetchDocuments()
    } catch {
      toast.error('Erreur de suppression')
    }
  }

  const formatDate = (d) => {
    if (!d) return '-'
    return new Date(d).toLocaleDateString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  }

  const formatSize = (bytes) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const docTypes = ['all', 'facture', 'devis', 'kbis', 'urssaf', 'siret', 'rib', 'inconnu']

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Historique Documents</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#718096' }}>{total} document(s)</span>
          <button className="btn btn-outline" onClick={fetchDocuments} title="Rafraîchir">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Filtres par type */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {docTypes.map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`btn ${filterType === type ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '6px 14px', fontSize: 12, textTransform: 'capitalize' }}
          >
            {type === 'all' ? 'Tous' : type}
          </button>
        ))}
      </div>

      {/* Liste */}
      {loading ? (
        <p style={{ textAlign: 'center', color: '#718096', padding: 40 }}>Chargement...</p>
      ) : documents.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60, color: '#718096' }}>
          <FileText size={48} color="#CBD5E0" />
          <p style={{ marginTop: 16 }}>Aucun document trouvé.</p>
          <p style={{ fontSize: 13 }}>Uploadez des documents pour les voir ici.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {documents.map(doc => {
            const statusConf = STATUS_CONFIG[doc.pipeline_status] || STATUS_CONFIG.raw
            const typeColor = TYPE_COLORS[doc.doc_type] || TYPE_COLORS.inconnu
            const isExpanded = expanded === doc.document_id
            const hasAnomalies = doc.anomalies && doc.anomalies.length > 0
            const isPdf = doc.mime_type === 'application/pdf'

            return (
              <div key={doc.document_id} className="card" style={{
                padding: 0,
                borderLeft: `4px solid ${typeColor}`,
                overflow: 'hidden',
              }}>
                {/* En-tête */}
                <div
                  style={{
                    padding: 16, display: 'flex', alignItems: 'center', gap: 12,
                    cursor: 'pointer',
                  }}
                  onClick={() => setExpanded(isExpanded ? null : doc.document_id)}
                >
                  {isPdf ? <FileText size={20} color={typeColor} /> : <Image size={20} color={typeColor} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.file_name}
                    </div>
                    <div style={{ fontSize: 12, color: '#718096', display: 'flex', gap: 12, marginTop: 2 }}>
                      <span>{formatSize(doc.file_size_bytes)}</span>
                      <span><Clock size={11} style={{ verticalAlign: 'middle' }} /> {formatDate(doc.processed_at || doc.created_at)}</span>
                    </div>
                  </div>

                  {/* Badges */}
                  <span style={{
                    padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                    background: typeColor + '15', color: typeColor, textTransform: 'capitalize',
                  }}>
                    {doc.doc_type}
                  </span>

                  <span style={{
                    padding: '3px 10px', borderRadius: 12, fontSize: 11,
                    background: statusConf.color + '15', color: statusConf.color,
                  }}>
                    {statusConf.label}
                  </span>

                  {doc.ocr_confidence != null && (
                    <span style={{ fontSize: 12, color: doc.ocr_confidence >= 0.8 ? '#00C896' : '#F4A261', fontWeight: 600 }}>
                      {Math.round(doc.ocr_confidence * 100)}%
                    </span>
                  )}

                  {hasAnomalies && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {doc.anomalies.some(a => a.severity === 'ERROR')
                        ? <XCircle size={16} color="#E63946" />
                        : <AlertTriangle size={16} color="#F4A261" />}
                      <span style={{ fontSize: 11, color: '#718096' }}>{doc.anomalies.length}</span>
                    </span>
                  )}

                  {doc.llm_extracted && <Sparkles size={14} color="#8B5CF6" title="Raffiné par IA" />}

                  <Eye size={16} color="#718096" style={{ opacity: isExpanded ? 1 : 0.4 }} />
                </div>

                {/* Détails expansés */}
                {isExpanded && (
                  <div style={{ padding: '0 16px 16px', borderTop: '1px solid #F0F4F8' }}>
                    {/* Entités */}
                    {doc.entities && Object.keys(doc.entities).some(k => doc.entities[k]) && (
                      <div style={{ marginTop: 12 }}>
                        <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#1B2A4A' }}>Entités extraites</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px' }}>
                          {Object.entries(doc.entities)
                            .filter(([, v]) => v != null && v !== '')
                            .map(([key, val]) => (
                              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13, borderBottom: '1px solid #F0F4F8' }}>
                                <span style={{ color: '#718096', fontWeight: 500 }}>{key}</span>
                                <span style={{ color: '#2D3748' }}>{String(val)}</span>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Anomalies */}
                    {hasAnomalies && (
                      <div style={{ marginTop: 12 }}>
                        <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#E63946' }}>Anomalies ({doc.anomalies.length})</h4>
                        {doc.anomalies.map((a, i) => (
                          <div key={i} style={{
                            padding: '8px 12px', marginBottom: 4, borderRadius: 6,
                            background: a.severity === 'ERROR' ? '#FEE2E2' : a.severity === 'WARNING' ? '#FEF3C7' : '#DBEAFE',
                            fontSize: 13,
                          }}>
                            <strong>{a.rule}</strong>: {a.message}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {llmAvailable && (
                        <button
                          className="btn btn-accent"
                          style={{ fontSize: 12, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
                          onClick={(e) => { e.stopPropagation(); handleReextract(doc.document_id, doc.file_name) }}
                          disabled={extracting === doc.document_id}
                        >
                          {extracting === doc.document_id
                            ? <><Loader size={14} className="animate-pulse" /> Extraction IA en cours...</>
                            : <><Sparkles size={14} /> Re-extraire avec IA</>
                          }
                        </button>
                      )}
                      {doc.llm_extracted && (
                        <span style={{
                          display: 'flex', alignItems: 'center', gap: 4,
                          fontSize: 11, color: '#8B5CF6', padding: '6px 10px',
                          background: 'rgba(139,92,246,0.08)', borderRadius: 6,
                        }}>
                          <Sparkles size={12} /> Raffiné par IA
                          {doc.llm_extraction_date && (' le ' + new Date(doc.llm_extraction_date).toLocaleDateString('fr-FR'))}
                        </span>
                      )}
                      <button
                        className="btn btn-danger"
                        style={{ fontSize: 12, padding: '4px 12px' }}
                        onClick={(e) => { e.stopPropagation(); handleDelete(doc.document_id) }}
                      >
                        <Trash2 size={14} /> Supprimer
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
