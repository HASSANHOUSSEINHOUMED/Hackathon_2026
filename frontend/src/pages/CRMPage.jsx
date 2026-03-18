import { useState, useEffect } from 'react'
import { Search, Building2, CheckCircle, AlertTriangle, XCircle, RefreshCw, Globe, Plus } from 'lucide-react'
import CRMForm from '../components/crm/CRMForm'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function CRMPage() {
  const [suppliers, setSuppliers] = useState([])
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)

  const fetchSuppliers = async () => {
    try {
      setLoading(true)
      const res = await api.get('/suppliers')
      setSuppliers(res.data)
    } catch {
      setSuppliers([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSuppliers() }, [])

  const filtered = suppliers.filter(s =>
    s.raison_sociale?.toLowerCase().includes(search.toLowerCase()) ||
    s.siret?.includes(search)
  )

  const handleVerifySiren = async () => {
    const cleaned = search.replace(/\s/g, '')
    if (!/^\d{9,14}$/.test(cleaned)) {
      toast.error('Entrez un SIREN (9 chiffres) ou SIRET (14 chiffres)')
      return
    }
    setVerifying(true)
    setVerifyResult(null)
    try {
      const res = await api.get(`/suppliers/verify/${cleaned}`)
      setVerifyResult(res.data)
      if (res.data.verified) {
        toast.success(`Entreprise vérifiée : ${res.data.data.raison_sociale}`)
      } else {
        toast.error('Aucune entreprise trouvée pour ce numéro')
      }
    } catch {
      toast.error('Erreur de vérification API')
    } finally {
      setVerifying(false)
    }
  }

  const handleImportFromVerification = async () => {
    if (!verifyResult?.data) return
    const d = verifyResult.data
    try {
      await api.post('/suppliers', {
        siret: d.siret || d.siren,
        raison_sociale: d.raison_sociale,
        forme_juridique: d.forme_juridique,
        adresse_rue: d.adresse,
        adresse_cp: d.code_postal,
        adresse_ville: d.ville,
      })
      toast.success('Fournisseur importé avec succès')
      setVerifyResult(null)
      fetchSuppliers()
    } catch {
      toast.error("Erreur lors de l'import")
    }
  }

  const statusIcon = (status) => {
    switch (status) {
      case 'ok': return <CheckCircle size={16} color="#00C896" />
      case 'warning': return <AlertTriangle size={16} color="#F4A261" />
      case 'error': return <XCircle size={16} color="#E63946" />
      default: return <CheckCircle size={16} color="#CBD5E0" />
    }
  }

  const statusLabel = (status) => {
    switch (status) {
      case 'ok': return 'Conforme'
      case 'warning': return 'Alerte'
      case 'error': return 'Erreur'
      default: return 'Non vérifié'
    }
  }

  const getInitials = (name) => {
    if (!name) return '??'
    return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
  }

  const colors = ['#1B2A4A', '#00C896', '#E63946', '#F4A261', '#2A9D8F', '#6D6875', '#457B9D']
  const getColor = (name) => colors[(name?.length || 0) % colors.length]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>CRM Fournisseurs</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-outline" onClick={fetchSuppliers} title="Rafraîchir">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="value">{suppliers.length}</div>
          <div className="label">Fournisseurs</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#00C896' }}>{suppliers.filter(s => s.conformity_status === 'ok').length}</div>
          <div className="label">Conformes</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#F4A261' }}>{suppliers.filter(s => s.conformity_status === 'warning').length}</div>
          <div className="label">Alertes</div>
        </div>
        <div className="kpi-card">
          <div className="value" style={{ color: '#E63946' }}>{suppliers.filter(s => s.conformity_status === 'error').length}</div>
          <div className="label">Erreurs</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Panel gauche : liste */}
        <div style={{ width: 380, flexShrink: 0 }}>
          {/* Recherche + vérification SIREN */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'white', borderRadius: 8, padding: '10px 14px',
            border: '1px solid #E2E8F0', marginBottom: 8,
          }}>
            <Search size={18} color="#718096" />
            <input
              type="text"
              placeholder="Rechercher ou vérifier SIREN/SIRET..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && /^\d{9,14}$/.test(search.replace(/\s/g, ''))) handleVerifySiren() }}
              style={{ border: 'none', outline: 'none', flex: 1, fontSize: 14, fontFamily: 'Inter' }}
            />
            <button
              onClick={handleVerifySiren}
              disabled={verifying}
              style={{
                background: '#1B2A4A', color: 'white', border: 'none', borderRadius: 6,
                padding: '6px 12px', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4,
                opacity: verifying ? 0.6 : 1,
              }}
              title="Vérifier via API gouvernementale"
            >
              <Globe size={14} />
              {verifying ? '...' : 'Vérifier'}
            </button>
          </div>

          {/* Résultat de la vérification SIREN */}
          {verifyResult && (
            <div className="card" style={{
              marginBottom: 12, padding: 16,
              borderLeft: verifyResult.verified ? '4px solid #00C896' : '4px solid #E63946',
              background: verifyResult.verified ? 'rgba(0,200,150,0.03)' : 'rgba(230,57,70,0.03)',
            }}>
              {verifyResult.verified ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <CheckCircle size={16} color="#00C896" />
                    <span style={{ fontWeight: 600, fontSize: 14, color: '#00C896' }}>Entreprise vérifiée</span>
                  </div>
                  <div style={{ fontSize: 13, color: '#2D3748' }}>
                    <div><strong>{verifyResult.data.raison_sociale}</strong></div>
                    <div>SIREN: {verifyResult.data.siren} | SIRET: {verifyResult.data.siret}</div>
                    <div>{verifyResult.data.adresse}</div>
                    <div>{verifyResult.data.code_postal} {verifyResult.data.ville}</div>
                    {verifyResult.data.activite && <div style={{ marginTop: 4, color: '#718096' }}>Activité: {verifyResult.data.activite}</div>}
                    {verifyResult.data.etat_administratif && (
                      <div style={{ marginTop: 4 }}>
                        État: <span style={{ color: verifyResult.data.etat_administratif === 'A' ? '#00C896' : '#E63946' }}>
                          {verifyResult.data.etat_administratif === 'A' ? 'Actif' : 'Fermé'}
                        </span>
                      </div>
                    )}
                  </div>
                  <button
                    className="btn btn-accent"
                    style={{ marginTop: 12, fontSize: 12, padding: '6px 14px' }}
                    onClick={handleImportFromVerification}
                  >
                    <Plus size={14} /> Importer ce fournisseur
                  </button>
                </>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <XCircle size={16} color="#E63946" />
                  <span style={{ fontSize: 13, color: '#E63946' }}>{verifyResult.message}</span>
                </div>
              )}
            </div>
          )}

          {/* Liste */}
          {loading ? (
            <p style={{ color: '#718096', textAlign: 'center', padding: 40 }}>Chargement...</p>
          ) : filtered.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 40, color: '#718096' }}>
              <Building2 size={40} color="#CBD5E0" style={{ margin: '0 auto 12px' }} />
              <p>Aucun fournisseur trouvé.</p>
              <p style={{ fontSize: 13 }}>Uploadez des documents ou vérifiez un SIREN pour alimenter le CRM.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filtered.map(s => (
                <div
                  key={s.supplier_id || s.siret}
                  onClick={() => { setSelected(s); setVerifyResult(null) }}
                  className="card"
                  style={{
                    cursor: 'pointer',
                    padding: 16,
                    border: selected?.siret === s.siret ? '2px solid #00C896' : '1px solid #E2E8F0',
                    display: 'flex', alignItems: 'center', gap: 12,
                    transition: 'border 0.2s',
                  }}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: 8,
                    background: getColor(s.raison_sociale),
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontWeight: 700, fontSize: 14,
                    fontFamily: 'Space Grotesk',
                    flexShrink: 0,
                  }}>
                    {getInitials(s.raison_sociale)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {s.raison_sociale}
                    </div>
                    <div style={{ fontSize: 12, color: '#718096' }}>
                      SIRET : {s.siret}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    {statusIcon(s.conformity_status)}
                    <span style={{ fontSize: 10, color: '#718096' }}>{statusLabel(s.conformity_status)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Panel droit : fiche détaillée */}
        <div style={{ flex: 1 }}>
          {selected ? (
            <CRMForm supplier={selected} onSaved={fetchSuppliers} />
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: 60, color: '#718096' }}>
              <Building2 size={48} color="#CBD5E0" />
              <p style={{ marginTop: 16 }}>Sélectionnez un fournisseur pour voir sa fiche.</p>
              <p style={{ fontSize: 13 }}>Ou utilisez la barre de recherche pour vérifier un SIREN/SIRET.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
