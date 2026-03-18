import { Router } from 'express'
import OpenAI from 'openai'
import Document from '../models/Document.js'
import Supplier from '../models/Supplier.js'
import crypto from 'crypto'

const router = Router()

const OPENAI_API_KEY = process.env.OPENAI_API_KEY || ''

function getOpenAIClient() {
  if (!OPENAI_API_KEY) {
    throw new Error('OPENAI_API_KEY non configuree')
  }
  return new OpenAI({ apiKey: OPENAI_API_KEY })
}

const EXTRACTION_PROMPT = `Tu es un expert en extraction de donnees de documents administratifs francais.
A partir du texte OCR brut ci-dessous, extrais les entites structurees suivantes selon le type de document.

TYPES DE DOCUMENTS ET CHAMPS ATTENDUS :
- facture : siret, tva_intra, montant_ht (nombre), tva (nombre), montant_ttc (nombre), date_emission, raison_sociale, iban, bic
- devis : siret, tva_intra, montant_ht (nombre), tva (nombre), montant_ttc (nombre), date_emission, date_validite, raison_sociale
- kbis : siret, siren, raison_sociale, capital_social, dirigeant, tva_intra, forme_juridique, date_immatriculation
- urssaf : siret, siren, raison_sociale, date_expiration
- siret : siret, siren, raison_sociale, code_naf, adresse
- rib : iban, bic, raison_sociale, siret, banque

REGLES :
- SIRET = 14 chiffres, SIREN = 9 premiers chiffres du SIRET
- TVA intracommunautaire = FR + 2 chiffres + SIREN (ex: FR32552100554)
- IBAN francais = FR76 + 23 caracteres
- Les montants = nombres decimaux sans symbole euro
- Les dates au format JJ/MM/AAAA
- Si un champ est introuvable, renvoie null
- Determine aussi le type du document

Reponds UNIQUEMENT avec un JSON valide :
{
  "type": "facture|devis|kbis|urssaf|siret|rib|inconnu",
  "confidence": 0.95,
  "entities": { ... }
}`

// POST /api/llm/reextract/:documentId - Re-extraction via LLM OpenAI
router.post('/reextract/:documentId', async (req, res) => {
  const { documentId } = req.params

  const doc = await Document.findOne({ document_id: documentId })
  if (!doc) {
    return res.status(404).json({ error: 'Document non trouve' })
  }

  if (!doc.raw_text || doc.raw_text.trim().length < 10) {
    return res.status(400).json({
      error: 'Texte OCR insuffisant pour la re-extraction. Re-uploadez le document.',
    })
  }

  let openai
  try {
    openai = getOpenAIClient()
  } catch (e) {
    return res.status(503).json({ error: e.message })
  }

  try {
    const start = Date.now()

    const userMessage = [
      'Type detecte par OCR : ' + doc.doc_type,
      '',
      'Texte OCR :',
      doc.raw_text.slice(0, 8000),
    ].join('\n')

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      temperature: 0.1,
      max_tokens: 1500,
      messages: [
        { role: 'system', content: EXTRACTION_PROMPT },
        { role: 'user', content: userMessage },
      ],
      response_format: { type: 'json_object' },
    })

    const content = completion.choices?.[0]?.message?.content
    if (!content) {
      return res.status(500).json({ error: 'Reponse LLM vide' })
    }

    let extracted
    try {
      extracted = JSON.parse(content)
    } catch {
      return res.status(500).json({ error: 'Reponse LLM non-JSON', raw: content })
    }

    const newEntities = extracted.entities || {}
    const newType = extracted.type || doc.doc_type

    // Fusionner : LLM remplace les champs null/vides et corrige les existants
    const currentEntities = doc.entities?.toObject ? doc.entities.toObject() : { ...doc.entities }
    const mergedEntities = { ...currentEntities }
    for (const [key, val] of Object.entries(newEntities)) {
      if (val !== null && val !== undefined && val !== '') {
        mergedEntities[key] = val
      }
    }

    // Mettre a jour le document en base
    await Document.findOneAndUpdate(
      { document_id: documentId },
      {
        doc_type: newType !== 'inconnu' ? newType : doc.doc_type,
        entities: mergedEntities,
        extraction_confidence: extracted.confidence || 0.9,
        llm_extracted: true,
        llm_extraction_date: new Date(),
        pipeline_status: 'llm_refined',
        processed_at: new Date(),
      },
      { new: true },
    )

    // Auto-upsert fournisseur si SIRET trouve par le LLM
    const siret = mergedEntities.siret
    if (siret && String(siret).replace(/\s/g, '').length >= 9) {
      const cleanSiret = String(siret).replace(/\s/g, '')
      const raison_sociale = mergedEntities.raison_sociale || 'Fournisseur ' + cleanSiret
      const supplierId = crypto.createHash('md5').update(cleanSiret).digest('hex').slice(0, 12)
      const updateObj = {
        supplier_id: supplierId,
        siret: cleanSiret,
        raison_sociale,
        tva_intra: mergedEntities.tva_intra || '',
        iban: mergedEntities.iban || '',
        bic: mergedEntities.bic || '',
        updated_at: new Date(),
      }
      await Supplier.findOneAndUpdate(
        { siret: cleanSiret },
        { ...updateObj, $addToSet: { documents: documentId } },
        { upsert: true, new: true, setDefaultsOnInsert: true },
      )
    }

    const durationMs = Date.now() - start
    const tokensUsed = completion.usage?.total_tokens || 0

    // Notification WebSocket
    const io = req.app.get('io')
    if (io) {
      io.emit('document:llm_refined', {
        document_id: documentId,
        type: newType,
        file_name: doc.file_name,
      })
    }

    res.json({
      document_id: documentId,
      previous_type: doc.doc_type,
      new_type: newType,
      entities: mergedEntities,
      confidence: extracted.confidence,
      llm_duration_ms: durationMs,
      tokens_used: tokensUsed,
      model: 'gpt-4o-mini',
    })
  } catch (err) {
    console.error('LLM extraction error:', err.message)
    if (err.status === 401) {
      return res.status(503).json({ error: 'Cle API OpenAI invalide' })
    }
    if (err.status === 429) {
      return res.status(429).json({ error: 'Rate limit OpenAI, reessayez dans quelques secondes' })
    }
    return res.status(500).json({ error: 'Erreur LLM', details: err.message })
  }
})

// GET /api/llm/status - Verifier si la cle API est configuree
router.get('/status', (req, res) => {
  res.json({
    available: !!OPENAI_API_KEY,
    model: 'gpt-4o-mini',
  })
})

export default router