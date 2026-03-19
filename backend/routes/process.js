import { Router } from 'express'
import multer from 'multer'
import axios from 'axios'
import crypto from 'crypto'
import fs from 'fs'
import Document from '../models/Document.js'
import Supplier from '../models/Supplier.js'
import storage from '../utils/storage.js'

const router = Router()

// Configuration multer
const diskStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = '/tmp/docuflow-uploads'
    fs.mkdirSync(dir, { recursive: true })
    cb(null, dir)
  },
  filename: (req, file, cb) => {
    const hash = crypto.randomBytes(8).toString('hex')
    cb(null, `${hash}-${file.originalname}`)
  },
})

const upload = multer({
  storage: diskStorage,
  limits: { fileSize: 20 * 1024 * 1024, files: 10 },
  fileFilter: (req, file, cb) => {
    const allowed = ['application/pdf', 'image/png', 'image/jpeg']
    cb(null, allowed.includes(file.mimetype))
  },
})

const OCR_URL = process.env.OCR_SERVICE_URL || 'http://localhost:5001'
const VALIDATION_URL = process.env.VALIDATION_SERVICE_URL || 'http://localhost:5002'

// Auto-create or update supplier from OCR entities
async function upsertSupplierFromEntities(entities, documentId) {
  const siret = entities?.siret
  if (!siret || siret.length < 9) return null

  const raison_sociale = entities?.raison_sociale || `Fournisseur ${siret}`
  const supplierId = crypto.createHash('md5').update(siret).digest('hex').slice(0, 12)

  const supplier = await Supplier.findOneAndUpdate(
    { siret },
    {
      supplier_id: supplierId,
      siret,
      raison_sociale,
      tva_intra: entities?.tva_intra || '',
      iban: entities?.iban || '',
      bic: entities?.bic || '',
      $addToSet: { documents: documentId },
      updated_at: new Date(),
    },
    { upsert: true, new: true, setDefaultsOnInsert: true },
  )
  return supplier
}

// Call validation service for a SINGLE document
async function validateDocument(ocrResult) {
  try {
    const response = await axios.post(`${VALIDATION_URL}/api/validate`, {
      documents: [{
        document_id: ocrResult.document_id,
        type: ocrResult.type,
        entities: ocrResult.entities || {},
      }],
    }, { timeout: 30000 })

    return response.data?.anomalies || []
  } catch (err) {
    console.warn('Validation service unavailable:', err.message)
    return []
  }
}

// Call validation service for BATCH (inter-document checks)
async function validateBatch(ocrResults) {
  if (!ocrResults || ocrResults.length === 0) return []
  
  try {
    const documents = ocrResults.map(r => ({
      document_id: r.document_id,
      type: r.type,
      entities: r.entities || {},
    }))
    
    const response = await axios.post(`${VALIDATION_URL}/api/validate`, {
      documents,
    }, { timeout: 60000 })

    return response.data?.anomalies || []
  } catch (err) {
    console.warn('Batch validation failed:', err.message)
    return []
  }
}

router.post('/', upload.array('documents', 10), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'Aucun fichier fourni' })
  }

  console.log(`[BATCH] Received ${req.files.length} file(s):`, req.files.map(f => f.originalname))

  const results = []
  const io = req.app.get('io')
  const ocrResults = []  // Collecter tous les résultats OCR pour validation batch
  const fileInfos = []   // Infos des fichiers pour mise à jour ultérieure

  // ══════════════════════════════════════════════════════════════════════
  // PHASE 1 : OCR de tous les documents
  // ══════════════════════════════════════════════════════════════════════
  for (const file of req.files) {
    try {
      // Hash du fichier comme ID
      const fileBuffer = fs.readFileSync(file.path)
      const documentId = crypto.createHash('md5').update(fileBuffer).digest('hex')

      // Appel service OCR
      const FormData = (await import('form-data')).default
      const formData = new FormData()
      formData.append('document', fs.createReadStream(file.path), file.originalname)

      let ocrResult
      try {
        const ocrResponse = await axios.post(`${OCR_URL}/api/ocr`, formData, {
          headers: formData.getHeaders(),
          timeout: 120000,
        })
        ocrResult = ocrResponse.data
      } catch {
        ocrResult = {
          document_id: documentId,
          type: 'inconnu',
          type_confidence: 0,
          ocr_confidence: 0,
          entities: {},
          raw_text: '',
          processing_time_ms: 0,
        }
      }

      ocrResult.document_id = documentId
      ocrResults.push(ocrResult)
      fileInfos.push({ file, documentId, ocrResult })

    } catch (err) {
      console.error(`Erreur OCR ${file.originalname}:`, err.message)
      results.push({ file_name: file.originalname, error: err.message })
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // PHASE 2 : Validation BATCH (règles inter-documents : SIRET_MISMATCH, etc.)
  // ══════════════════════════════════════════════════════════════════════
  console.log(`[BATCH] Sending ${ocrResults.length} document(s) for batch validation`)
  console.log(`[BATCH] Documents:`, ocrResults.map(r => ({ id: r.document_id?.slice(0,8), type: r.type, siret: r.entities?.siret })))
  const allAnomalies = await validateBatch(ocrResults)
  console.log(`[BATCH] Validation returned ${allAnomalies.length} anomalies`)
  
  // Indexer les anomalies par document_id
  const anomaliesByDocId = {}
  for (const anomaly of allAnomalies) {
    const docIds = anomaly.concerned_document_ids || []
    for (const docId of docIds) {
      if (!anomaliesByDocId[docId]) anomaliesByDocId[docId] = []
      anomaliesByDocId[docId].push(anomaly)
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // PHASE 3 : Sauvegarde et notifications
  // ══════════════════════════════════════════════════════════════════════
  for (const { file, documentId, ocrResult } of fileInfos) {
    try {
      // Récupérer les anomalies pour CE document
      const anomalies = anomaliesByDocId[documentId] || []
      
      // Déterminer le statut pipeline
      const hasErrors = anomalies.some(a => a.severity === 'ERROR')
      const hasWarnings = anomalies.some(a => a.severity === 'WARNING')
      const pipelineStatus = anomalies.length > 0 ? 'validated' : 'ocr_done'
      const conformityStatus = hasErrors ? 'error' : hasWarnings ? 'warning' : 'ok'

      // Mapper les anomalies au schéma Document (rule_id → rule)
      const mappedAnomalies = anomalies.map(a => ({
        rule: a.rule_id || a.rule || 'UNKNOWN',
        severity: a.severity || 'INFO',
        message: a.message || '',
      }))

      // Sauvegarder le document en base
      const doc = await Document.findOneAndUpdate(
        { document_id: documentId },
        {
          document_id: documentId,
          file_name: file.originalname,
          file_size_bytes: file.size,
          mime_type: file.mimetype,
          doc_type: ocrResult.type || 'inconnu',
          pipeline_status: pipelineStatus,
          entities: ocrResult.entities || {},
          raw_text: ocrResult.raw_text || '',
          anomalies: mappedAnomalies,
          ocr_confidence: ocrResult.ocr_confidence || 0,
          extraction_confidence: ocrResult.extraction_confidence || 0,
          processing_time_ms: ocrResult.processing_time_ms || 0,
          processed_at: new Date(),
        },
        { upsert: true, new: true },
      )

      // Upload vers MinIO Data Lake
      let minioRawPath = null
      let minioCleanPath = null
      try {
        // Upload fichier brut dans raw-zone
        minioRawPath = await storage.uploadRaw(file.path, documentId, {
          type: ocrResult.type,
          originalName: file.originalname,
        })
        // Upload résultat OCR dans clean-zone
        minioCleanPath = await storage.uploadClean(documentId, ocrResult)
        // Mettre à jour le document avec les chemins MinIO
        await Document.updateOne(
          { document_id: documentId },
          { 'minio_paths.raw': minioRawPath, 'minio_paths.clean': minioCleanPath },
        )
      } catch (minioErr) {
        console.warn(`[MinIO] Upload failed for ${documentId}:`, minioErr.message)
      }

      // Auto-créer le fournisseur depuis les entités OCR
      const supplier = await upsertSupplierFromEntities(ocrResult.entities, documentId)
      if (supplier) {
        await Document.updateOne(
          { document_id: documentId },
          { supplier_id: supplier.supplier_id },
        )
        // Mettre à jour le statut conformité du fournisseur
        await Supplier.updateOne(
          { siret: supplier.siret },
          { conformity_status: conformityStatus, last_check: new Date() },
        )
      }

      results.push({
        document_id: documentId,
        file_name: file.originalname,
        type: ocrResult.type,
        type_confidence: ocrResult.type_confidence,
        ocr_confidence: ocrResult.ocr_confidence,
        entities: ocrResult.entities,
        extraction_confidence: ocrResult.extraction_confidence,
        processing_time_ms: ocrResult.processing_time_ms,
        anomalies: mappedAnomalies,
        supplier_created: !!supplier,
      })

      // Notification en temps réel
      if (io) {
        io.emit('document:processed', {
          document_id: documentId,
          type: ocrResult.type,
          file_name: file.originalname,
          anomalies_count: anomalies.length,
        })
        if (anomalies.length > 0) {
          for (const anomaly of anomalies) {
            io.emit('anomaly:detected', { ...anomaly, file_name: file.originalname })
          }
        }
      }
    } catch (err) {
      console.error(`Erreur traitement ${file.originalname}:`, err.message)
      results.push({
        file_name: file.originalname,
        error: err.message,
      })
    } finally {
      try { fs.unlinkSync(file.path) } catch {}
    }
  }

  res.json({
    total: req.files.length,
    success: results.filter(r => !r.error).length,
    results,
  })
})

// Appelé par Airflow à la fin du pipeline
router.post('/pipeline/complete', async (req, res) => {
  const { documents, anomalies } = req.body
  const io = req.app.get('io')

  if (!documents || !Array.isArray(documents)) {
    return res.status(400).json({ error: 'Format invalide' })
  }

  for (const doc of documents) {
    await Document.findOneAndUpdate(
      { document_id: doc.document_id },
      {
        pipeline_status: 'curated',
        entities: doc.entities,
        anomalies: doc.anomalies || [],
      },
    )
  }

  if (io && anomalies) {
    for (const anomaly of anomalies) {
      io.emit('anomaly:detected', anomaly)
    }
  }

  res.json({ status: 'ok', updated: documents.length })
})

// ══════════════════════════════════════════════════════════════════════════
// Revalidation BATCH - Compare les documents inter-documents
// ══════════════════════════════════════════════════════════════════════════
router.post('/revalidate-batch', async (req, res) => {
  const { document_ids, supplier_id } = req.body
  const io = req.app.get('io')

  try {
    // Récupérer les documents à revalider
    let query = {}
    if (document_ids && Array.isArray(document_ids)) {
      query = { document_id: { $in: document_ids } }
    } else if (supplier_id) {
      query = { supplier_id }
    } else {
      // Par défaut : tous les documents des dernières 24h
      const since = new Date(Date.now() - 24 * 60 * 60 * 1000)
      query = { processed_at: { $gte: since } }
    }

    const docs = await Document.find(query).lean()
    if (docs.length === 0) {
      return res.json({ status: 'ok', message: 'Aucun document à revalider', updated: 0 })
    }

    // Préparer les documents pour la validation
    const docsForValidation = docs.map(d => ({
      document_id: d.document_id,
      type: d.doc_type,
      entities: d.entities || {},
    }))

    // Appel validation batch
    const allAnomalies = await validateBatch(docsForValidation)

    // Indexer par document_id
    const anomaliesByDocId = {}
    for (const anomaly of allAnomalies) {
      const docIds = anomaly.concerned_document_ids || []
      for (const docId of docIds) {
        if (!anomaliesByDocId[docId]) anomaliesByDocId[docId] = []
        anomaliesByDocId[docId].push(anomaly)
      }
    }

    // Mettre à jour chaque document
    let updated = 0
    for (const doc of docs) {
      const anomalies = anomaliesByDocId[doc.document_id] || []
      const mappedAnomalies = anomalies.map(a => ({
        rule: a.rule_id || a.rule || 'UNKNOWN',
        severity: a.severity || 'INFO',
        message: a.message || '',
      }))

      await Document.updateOne(
        { document_id: doc.document_id },
        { 
          anomalies: mappedAnomalies,
          pipeline_status: anomalies.length > 0 ? 'validated' : doc.pipeline_status,
        }
      )
      updated++

      // Notification temps réel
      if (io && anomalies.length > 0) {
        for (const anomaly of anomalies) {
          io.emit('anomaly:detected', { ...anomaly, file_name: doc.file_name })
        }
      }
    }

    res.json({
      status: 'ok',
      documents_checked: docs.length,
      anomalies_found: allAnomalies.length,
      updated,
    })
  } catch (err) {
    console.error('Revalidation batch error:', err.message)
    res.status(500).json({ error: err.message })
  }
})

export default router
