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

// Call validation service
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

router.post('/', upload.array('documents', 10), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'Aucun fichier fourni' })
  }

  const results = []
  const io = req.app.get('io')

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

      // Appel service de validation
      ocrResult.document_id = documentId
      const anomalies = await validateDocument(ocrResult)

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

export default router
