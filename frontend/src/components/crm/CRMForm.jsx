import { useState } from 'react'
import { Sparkles, Save, Download, Globe, CheckCircle, XCircle } from 'lucide-react'
import api from '../../services/api'
import toast from 'react-hot-toast'

function AIField({ label, value, confidence, onChange }) {
  const isAI = confidence != null && confidence > 0

  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#718096', marginBottom: 4 }}>
        {label}
      </label>
      <div style={{
        position: 'relative',
        borderLeft: isAI ? '3px solid #00C896' : '3px solid transparent',
        background: isAI ? 'rgba(0,200,150,0.03)' : 'white',
        borderRadius: 6,
      }}>
        <input
          type="text"
          value={value || ''}
          onChange={e => onChange(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 36px 10px 12px',
            border: '1px solid #E2E8F0',
            borderRadius: 6,
            fontSize: 14,
            fontFamily: 'Inter',
            outline: 'none',
          }}
          title={isAI ? `Extrait par IA (confiance: ${Math.round(confidence * 100)}%)` : ''}
        />
        {isAI && (
          <Sparkles
            size={14}
            color="#00C896"
            style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)' }}
          />
        )}
      </div>
    </div>
  )
}

export default function CRMForm({ supplier, onSaved }) {
  const [form, setForm] = useState({ ...supplier })
  const [saving, setSaving] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState(null)

  const update = (field) => (value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.post('/suppliers', {
        ...form,
        adresse_rue: form.adresse?.rue || form.adresse_rue,
        adresse_cp: form.adresse?.cp || form.adresse_cp,
        adresse_ville: form.adresse?.ville || form.adresse_ville,
      })
      toast.success('Fournisseur sauvegardé')
      if (onSaved) onSaved()
    } catch {
      toast.error('Erreur de sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const handleVerify = async () => {
    const siret = form.siret?.replace(/\s/g, '')
    if (!siret || !/^\d{9,14}$/.test(siret)) {
      toast.error('SIRET invalide pour la vérification')
      return
    }
    setVerifying(true)
    setVerifyResult(null)
    try {
      const res = await api.get(`/suppliers/verify/${siret}`)
      setVerifyResult(res.data)
      if (res.data.verified) {
        toast.success('SIRET vérifié avec succès')
      } else {
        toast.error('SIRET non trouvé dans la base officielle')
      }
    } catch {
      toast.error('Erreur de vérification')
    } finally {
      setVerifying(false)
    }
  }

  const applyVerifiedData = () => {
    if (!verifyResult?.data) return
    const d = verifyResult.data
    setForm(prev => ({
      ...prev,
      raison_sociale: d.raison_sociale || prev.raison_sociale,
      forme_juridique: d.forme_juridique || prev.forme_juridique,
      adresse_rue: d.adresse || prev.adresse?.rue || prev.adresse_rue,
      adresse_cp: d.code_postal || prev.adresse?.cp || prev.adresse_cp,
      adresse_ville: d.ville || prev.adresse?.ville || prev.adresse_ville,
    }))
    toast.success('Données officielles appliquées')
  }

  const conf = 0.85

  return (
    <div className="card">
      <h3 style={{ fontSize: '1.1rem', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Sparkles size={18} color="#00C896" />
        Fiche Fournisseur (auto-remplie IA)
      </h3>

      {/* Section Identité */}
      <h4 style={{ fontSize: 14, color: '#1B2A4A', marginBottom: 12, fontFamily: 'Space Grotesk' }}>Identité</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
        <AIField label="Raison Sociale" value={form.raison_sociale} confidence={conf} onChange={update('raison_sociale')} />
        <AIField label="SIRET" value={form.siret} confidence={conf} onChange={update('siret')} />
        <AIField label="TVA Intracommunautaire" value={form.tva_intra} confidence={conf} onChange={update('tva_intra')} />
        <AIField label="Forme Juridique" value={form.forme_juridique} confidence={conf} onChange={update('forme_juridique')} />
      </div>

      {/* Bouton vérification SIREN */}
      <div style={{ marginBottom: 16 }}>
        <button
          className="btn btn-outline"
          onClick={handleVerify}
          disabled={verifying}
          style={{ fontSize: 12, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Globe size={14} />
          {verifying ? 'Vérification...' : 'Vérifier SIRET via API gouv'}
        </button>

        {verifyResult && (
          <div style={{
            marginTop: 8, padding: 12, borderRadius: 8,
            background: verifyResult.verified ? 'rgba(0,200,150,0.05)' : 'rgba(230,57,70,0.05)',
            border: `1px solid ${verifyResult.verified ? '#00C896' : '#E63946'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              {verifyResult.verified ? <CheckCircle size={14} color="#00C896" /> : <XCircle size={14} color="#E63946" />}
              <span style={{ fontSize: 13, fontWeight: 600, color: verifyResult.verified ? '#00C896' : '#E63946' }}>
                {verifyResult.verified ? 'Entreprise vérifiée' : 'Non trouvé'}
              </span>
            </div>
            {verifyResult.verified && (
              <>
                <div style={{ fontSize: 12, color: '#2D3748', marginBottom: 8 }}>
                  <div><strong>{verifyResult.data.raison_sociale}</strong></div>
                  <div>{verifyResult.data.adresse}, {verifyResult.data.code_postal} {verifyResult.data.ville}</div>
                  <div>État: {verifyResult.data.etat_administratif === 'A' ? 'Actif' : 'Fermé'}</div>
                </div>
                <button
                  className="btn btn-accent"
                  style={{ fontSize: 11, padding: '4px 10px' }}
                  onClick={applyVerifiedData}
                >
                  Appliquer les données officielles
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Section Coordonnées */}
      <h4 style={{ fontSize: 14, color: '#1B2A4A', margin: '20px 0 12px', fontFamily: 'Space Grotesk' }}>Coordonnées</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '0 16px' }}>
        <AIField label="Adresse" value={form.adresse?.rue || form.adresse_rue} confidence={conf} onChange={update('adresse_rue')} />
        <AIField label="Code Postal" value={form.adresse?.cp || form.adresse_cp} confidence={conf} onChange={update('adresse_cp')} />
        <AIField label="Ville" value={form.adresse?.ville || form.adresse_ville} confidence={conf} onChange={update('adresse_ville')} />
      </div>

      {/* Section Banque */}
      <h4 style={{ fontSize: 14, color: '#1B2A4A', margin: '20px 0 12px', fontFamily: 'Space Grotesk' }}>Coordonnées bancaires</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0 16px' }}>
        <AIField label="IBAN" value={form.iban} confidence={conf} onChange={update('iban')} />
        <AIField label="BIC" value={form.bic} confidence={conf} onChange={update('bic')} />
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <button className="btn btn-accent" onClick={handleSave} disabled={saving}>
          {saving ? <div className="spinner" /> : <Save size={16} />}
          Sauvegarder en base
        </button>
        <button className="btn btn-outline">
          <Download size={16} /> Exporter fiche
        </button>
      </div>
    </div>
  )
}
