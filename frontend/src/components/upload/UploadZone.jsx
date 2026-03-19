import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Image, X, CheckCircle, AlertCircle, Loader } from 'lucide-react'

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function StatusIcon({ status }) {
  switch (status) {
    case 'done': return <CheckCircle size={18} color="#00C896" />
    case 'error': return <AlertCircle size={18} color="#E63946" />
    case 'processing': return <Loader size={18} color="#F4A261" className="animate-pulse" />
    default: return <div style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid #CBD5E0' }} />
  }
}

export default function UploadZone({ files, onAddFiles, onRemoveFile, onProcess, processing, progress, batchMode, onBatchModeChange }) {
  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) onAddFiles(accepted)
  }, [onAddFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    multiple: true,
  })

  return (
    <div>
      {/* Dropzone */}
      <div
        {...getRootProps()}
        style={{
          height: 200,
          border: `2px dashed ${isDragActive ? '#00C896' : '#CBD5E0'}`,
          borderRadius: 16,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          background: isDragActive ? 'rgba(0,200,150,0.05)' : 'white',
          transition: 'all 0.3s',
          marginBottom: 24,
        }}
      >
        <input {...getInputProps()} />
        <Upload size={40} color={isDragActive ? '#00C896' : '#CBD5E0'} style={{ marginBottom: 12 }} />
        <p style={{ fontSize: 16, fontWeight: 600, color: '#2D3748' }}>
          {isDragActive ? 'Déposez les fichiers ici...' : 'Glissez vos documents ou cliquez pour sélectionner'}
        </p>
        <p style={{ fontSize: 13, color: '#718096', marginTop: 4 }}>
          PDF, PNG, JPG — Taille max 20 MB
        </p>
      </div>

      {/* Liste des fichiers */}
      {files.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>
            {files.length} document(s) sélectionné(s)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {files.map(f => (
              <div key={f.id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                background: 'white',
                borderRadius: 8,
                border: '1px solid #E2E8F0',
              }}>
                <StatusIcon status={f.status} />
                {f.name.endsWith('.pdf') ? <FileText size={18} color="#E63946" /> : <Image size={18} color="#00C896" />}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{f.name}</div>
                  <div style={{ fontSize: 12, color: '#718096' }}>{formatSize(f.size)}</div>
                </div>
                {f.result?.type && (
                  <span className="badge badge-info">{f.result.type}</span>
                )}
                {f.result?.ocr_confidence != null && (
                  <span style={{ fontSize: 12, color: '#718096' }}>
                    OCR: {Math.round(f.result.ocr_confidence * 100)}%
                  </span>
                )}
                {f.status === 'pending' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onRemoveFile(f.id) }}
                    style={{ background: 'none', border: 'none', padding: 4 }}
                  >
                    <X size={16} color="#718096" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Barre de progression */}
      {processing && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            height: 8,
            background: '#E2E8F0',
            borderRadius: 4,
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${progress}%`,
              background: 'linear-gradient(90deg, #00C896, #1B2A4A)',
              borderRadius: 4,
              transition: 'width 0.3s',
            }} />
          </div>
          <p style={{ textAlign: 'center', fontSize: 13, color: '#718096', marginTop: 6 }}>
            {progress}% — Traitement en cours...
          </p>
        </div>
      )}

      {/* Boutons de traitement */}
      {files.length > 0 && (
        <div style={{ display: 'flex', gap: 12, flexDirection: files.length > 1 ? 'row' : 'column' }}>
          {/* Bouton traitement individuel */}
          <button
            className="btn btn-accent"
            onClick={() => { onBatchModeChange(false); onProcess(false); }}
            disabled={processing || files.every(f => f.status === 'done')}
            style={{ 
              flex: 1, 
              justifyContent: 'center', 
              padding: '14px 0', 
              fontSize: 15,
              background: '#1B2A4A',
            }}
          >
            {processing && !batchMode ? (
              <><div className="spinner" /> Traitement...</>
            ) : (
              <>
                <Upload size={18} />
                Traiter {files.filter(f => f.status === 'pending').length} document(s)
              </>
            )}
          </button>

          {/* Bouton batch - visible si > 1 fichier */}
          {files.length > 1 && (
            <button
              className="btn"
              onClick={() => { onBatchModeChange(true); onProcess(true); }}
              disabled={processing || files.every(f => f.status === 'done')}
              style={{ 
                flex: 1, 
                justifyContent: 'center', 
                padding: '14px 0', 
                fontSize: 15,
                background: '#00C896',
                color: 'white',
                border: 'none',
              }}
            >
              {processing && batchMode ? (
                <><div className="spinner" /> Traitement batch...</>
              ) : (
                <>
                  <Upload size={18} />
                  Batch (même fournisseur)
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
