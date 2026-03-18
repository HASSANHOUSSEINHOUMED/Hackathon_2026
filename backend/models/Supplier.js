import mongoose from 'mongoose'

const supplierSchema = new mongoose.Schema({
  supplier_id: { type: String, unique: true, required: true },
  siret: { type: String, unique: true, required: true, index: true },
  raison_sociale: { type: String, required: true },
  tva_intra: String,
  forme_juridique: String,
  adresse: {
    rue: String,
    cp: String,
    ville: String,
  },
  iban: String,
  bic: String,
  contacts: [{
    nom: String,
    email: String,
    telephone: String,
  }],
  documents: [{ type: String }], // document_ids
  conformity_status: {
    type: String,
    enum: ['ok', 'warning', 'error'],
    default: 'ok',
    index: true,
  },
  last_check: Date,
  created_at: { type: Date, default: Date.now },
  updated_at: { type: Date, default: Date.now },
})

supplierSchema.pre('save', function () {
  this.updated_at = new Date()
})

export default mongoose.model('Supplier', supplierSchema)
