import mongoose from 'mongoose'

const documentSchema = new mongoose.Schema({
  document_id: { type: String, unique: true, required: true, index: true },
  file_name: { type: String, required: true },
  file_size_bytes: { type: Number },
  mime_type: { type: String },
  doc_type: {
    type: String,
    enum: ['facture', 'devis', 'kbis', 'urssaf', 'siret', 'rib', 'inconnu'],
    default: 'inconnu',
  },
  pipeline_status: {
    type: String,
    enum: ['raw', 'ocr_done', 'validated', 'llm_refined', 'curated'],
    default: 'raw',
  },
  minio_paths: {
    raw: String,
    clean: String,
    curated: String,
  },
  entities: {
    siret: String,
    tva_intra: String,
    montant_ht: Number,
    tva: Number,
    montant_ttc: Number,
    date_emission: String,
    date_expiration: String,
    date_validite: String,
    raison_sociale: String,
    iban: String,
    bic: String,
  },
  raw_text: { type: String, default: '' },
  anomalies: [{
    rule: String,
    severity: { type: String, enum: ['ERROR', 'WARNING', 'INFO'] },
    message: String,
  }],
  ocr_confidence: Number,
  extraction_confidence: Number,
  processing_time_ms: Number,
  llm_extracted: { type: Boolean, default: false },
  llm_extraction_date: Date,
  supplier_id: { type: String, index: true },
  created_at: { type: Date, default: Date.now, index: true },
  processed_at: Date,
})

export default mongoose.model('Document', documentSchema)
