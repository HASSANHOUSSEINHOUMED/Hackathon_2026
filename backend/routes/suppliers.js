import { Router } from 'express'
import axios from 'axios'
import Supplier from '../models/Supplier.js'
import crypto from 'crypto'

const router = Router()

// Liste des fournisseurs
router.get('/', async (req, res) => {
  const suppliers = await Supplier.find()
    .sort({ updated_at: -1 })
    .lean()
  res.json(suppliers)
})

// Créer ou mettre à jour un fournisseur
router.post('/', async (req, res) => {
  const { siret, raison_sociale, tva_intra, forme_juridique, iban, bic, adresse_rue, adresse_cp, adresse_ville } = req.body

  if (!siret || !raison_sociale) {
    return res.status(400).json({ error: 'SIRET et raison sociale requis' })
  }

  const supplierId = crypto.createHash('md5').update(siret).digest('hex').slice(0, 12)

  const supplier = await Supplier.findOneAndUpdate(
    { siret },
    {
      supplier_id: supplierId,
      siret,
      raison_sociale,
      tva_intra,
      forme_juridique,
      iban,
      bic,
      adresse: {
        rue: adresse_rue,
        cp: adresse_cp,
        ville: adresse_ville,
      },
    },
    { upsert: true, new: true },
  )

  res.json(supplier)
})

// Vérifier un SIREN/SIRET via l'API gouvernementale (recherche-entreprises.api.gouv.fr)
router.get('/verify/:number', async (req, res) => {
  const { number } = req.params
  const cleaned = number.replace(/\s/g, '')

  if (!/^\d{9,14}$/.test(cleaned)) {
    return res.status(400).json({ error: 'Numéro SIREN (9 chiffres) ou SIRET (14 chiffres) invalide' })
  }

  try {
    const response = await axios.get(
      `https://recherche-entreprises.api.gouv.fr/search?q=${encodeURIComponent(cleaned)}`,
      { timeout: 10000 }
    )

    const results = response.data?.results || []
    if (results.length === 0) {
      return res.json({ verified: false, message: 'Aucune entreprise trouvée', data: null })
    }

    const entreprise = results[0]
    const siege = entreprise.siege || {}

    return res.json({
      verified: true,
      message: 'Entreprise vérifiée via API gouvernementale',
      data: {
        siren: entreprise.siren,
        siret: siege.siret,
        raison_sociale: entreprise.nom_complet,
        forme_juridique: entreprise.nature_juridique,
        adresse: siege.adresse,
        code_postal: siege.code_postal,
        ville: siege.libelle_commune,
        activite: entreprise.activite_principale,
        date_creation: entreprise.date_creation,
        nombre_etablissements: entreprise.nombre_etablissements,
        tranche_effectif: entreprise.tranche_effectif_salarie,
        etat_administratif: entreprise.etat_administratif,
      },
    })
  } catch (err) {
    return res.status(502).json({ error: 'Erreur lors de la vérification', details: err.message })
  }
})

// Détail d'un fournisseur
router.get('/:siret', async (req, res) => {
  const supplier = await Supplier.findOne({ siret: req.params.siret }).lean()
  if (!supplier) return res.status(404).json({ error: 'Fournisseur non trouvé' })
  res.json(supplier)
})

// Suppression
router.delete('/:siret', async (req, res) => {
  const result = await Supplier.deleteOne({ siret: req.params.siret })
  if (result.deletedCount === 0) return res.status(404).json({ error: 'Fournisseur non trouvé' })
  res.json({ status: 'deleted' })
})

export default router
