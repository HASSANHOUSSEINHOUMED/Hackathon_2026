import { Router } from 'express'
import Document from '../models/Document.js'

const router = Router()

// Liste des documents
router.get('/', async (req, res) => {
  const { type, status, limit = 50, skip = 0 } = req.query
  const filter = {}
  if (type) filter.doc_type = type
  if (status) filter.pipeline_status = status

  const docs = await Document.find(filter)
    .sort({ created_at: -1 })
    .skip(Number(skip))
    .limit(Number(limit))
    .lean()

  const total = await Document.countDocuments(filter)
  res.json({ documents: docs, total })
})

// Détail d'un document
router.get('/:id', async (req, res) => {
  const doc = await Document.findOne({ document_id: req.params.id }).lean()
  if (!doc) return res.status(404).json({ error: 'Document non trouvé' })
  res.json(doc)
})

// Statut d'un document (pour le polling)
router.get('/:id/status', async (req, res) => {
  const doc = await Document.findOne(
    { document_id: req.params.id },
    { pipeline_status: 1, doc_type: 1, ocr_confidence: 1 },
  ).lean()
  if (!doc) return res.status(404).json({ error: 'Document non trouvé' })
  res.json({ status: doc.pipeline_status, type: doc.doc_type })
})

// Suppression
router.delete('/:id', async (req, res) => {
  const result = await Document.deleteOne({ document_id: req.params.id })
  if (result.deletedCount === 0) return res.status(404).json({ error: 'Document non trouvé' })
  res.json({ status: 'deleted' })
})

export default router
