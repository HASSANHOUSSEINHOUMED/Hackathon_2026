import { useUploadContext } from '../context/UploadContext'
import UploadZone from '../components/upload/UploadZone'
import { RotateCcw } from 'lucide-react'

export default function UploadPage() {
  const { files, addFiles, removeFile, processFiles, processing, progress, results, reset } = useUploadContext()

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Upload de documents</h1>
        {files.length > 0 && (
          <button className="btn btn-outline" onClick={reset}>
            <RotateCcw size={16} /> Réinitialiser
          </button>
        )}
      </div>

      <div className="card">
        <UploadZone
          files={files}
          onAddFiles={addFiles}
          onRemoveFile={removeFile}
          onProcess={processFiles}
          processing={processing}
          progress={progress}
        />
      </div>

      {/* Résultats */}
      {results.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: 16 }}>Résultats du traitement</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 16 }}>
            {files.filter(f => f.status === 'done' && f.result).map(f => (
              <div key={f.id} className="card" style={{ borderLeft: '4px solid #00C896' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <h4 style={{ fontSize: 14, marginBottom: 4 }}>{f.name}</h4>
                    <span className={`badge ${f.result.type === 'inconnu' ? 'badge-warning' : 'badge-info'}`}>
                      {f.result.type || 'inconnu'}
                    </span>
                  </div>
                  <ConfidenceGauge value={f.result.ocr_confidence || 0} />
                </div>

                {/* Entités extraites */}
                {f.result.entities && (
                  <div style={{ fontSize: 13, color: '#718096' }}>
                    {Object.entries(f.result.entities)
                      .filter(([_, v]) => v != null)
                      .slice(0, 5)
                      .map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #F0F4F8' }}>
                          <span style={{ fontWeight: 500 }}>{key}</span>
                          <span style={{ color: '#2D3748', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(val)}</span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ConfidenceGauge({ value }) {
  const percent = Math.round(value * 100)
  const color = percent >= 80 ? '#00C896' : percent >= 50 ? '#F4A261' : '#E63946'

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={50} height={50} viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" fill="none" stroke="#E2E8F0" strokeWidth="4" />
        <circle
          cx="25" cy="25" r="20"
          fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${percent * 1.256} 125.6`}
          strokeLinecap="round"
          transform="rotate(-90 25 25)"
        />
        <text x="25" y="28" textAnchor="middle" fontSize="11" fontWeight="600" fill={color}>
          {percent}%
        </text>
      </svg>
      <div style={{ fontSize: 10, color: '#718096' }}>OCR</div>
    </div>
  )
}
