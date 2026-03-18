import { Router } from 'express'
import Document from '../models/Document.js'

const router = Router()

// Résultats de validation agrégés
router.get('/results', async (req, res) => {
  const docs = await Document.find({}, {
    document_id: 1, file_name: 1, doc_type: 1, pipeline_status: 1, anomalies: 1, ocr_confidence: 1,
  }).lean()

  const total = docs.length
  const withAnomalies = docs.filter(d => d.anomalies && d.anomalies.length > 0)
  const erreurs = withAnomalies.filter(d => d.anomalies.some(a => a.severity === 'ERROR')).length
  const alertes = withAnomalies.filter(d => d.anomalies.some(a => a.severity === 'WARNING')).length
  const conformes = total - withAnomalies.length

  // Aplatir les anomalies et mapper rule → rule_id pour le frontend
  const allAnomalies = docs.flatMap(d =>
    (d.anomalies || []).map(a => ({
      rule_id: a.rule || a.rule_id || 'UNKNOWN',
      severity: a.severity,
      message: a.message,
      document_id: d.document_id,
      file_name: d.file_name,
      concerned_document_ids: [d.document_id],
    }))
  )

  res.json({
    stats: { total, conformes, alertes, erreurs },
    anomalies: allAnomalies,
  })
})

export default router
