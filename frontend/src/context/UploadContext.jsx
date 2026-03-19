import { createContext, useContext, useState, useCallback } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'

const UploadContext = createContext(null)

export function UploadProvider({ children }) {
  const [files, setFiles] = useState([])
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState([])
  const [batchMode, setBatchMode] = useState(false) // Mode batch fournisseur

  const addFiles = useCallback((newFiles) => {
    const mapped = newFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      name: file.name,
      size: file.size,
      status: 'pending',
      result: null,
    }))
    setFiles(prev => [...prev, ...mapped])
  }, [])

  const removeFile = useCallback((id) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const processFiles = useCallback(async (forceBatch = null) => {
    if (files.length === 0) return

    // Si forceBatch est fourni, l'utiliser. Sinon, utiliser l'état batchMode
    const useBatchMode = forceBatch !== null ? forceBatch : batchMode

    setProcessing(true)
    setProgress(0)
    setResults([])

    const totalFiles = files.length
    const newResults = []

    // ═══════════════════════════════════════════════════════════════════
    // MODE BATCH : Tous les fichiers du même fournisseur (MISMATCH activé)
    // ═══════════════════════════════════════════════════════════════════
    if (useBatchMode && files.length > 1) {
      console.log('[BATCH] Sending all files in one request')
      // Marquer tous les fichiers en processing
      setFiles(prev => prev.map(f => ({ ...f, status: 'processing' })))
      setProgress(10)

      try {
        const formData = new FormData()
        files.forEach(f => formData.append('documents', f.file))

        const response = await api.post('/process', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000, // 5 min pour batch
        })

        const data = response.data
        const resultsArray = data.results || []
        
        // Associer chaque résultat au bon fichier par nom
        setFiles(prev => prev.map(f => {
          const matchingResult = resultsArray.find(r => r.file_name === f.name)
          if (matchingResult) {
            newResults.push(matchingResult)
            return { ...f, status: 'done', result: matchingResult }
          }
          return { ...f, status: 'error', result: { error: 'Résultat non trouvé' } }
        }))

        setProgress(100)
        toast.success(`${resultsArray.length}/${totalFiles} document(s) traité(s) en batch`)
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message
        setFiles(prev => prev.map(f => ({ ...f, status: 'error', result: { error: errorMsg } })))
        toast.error(`Erreur batch : ${errorMsg}`)
      }
    } else {
      // ═══════════════════════════════════════════════════════════════════
      // MODE NORMAL : Un fichier à la fois (pas de MISMATCH inter-documents)
      // ═══════════════════════════════════════════════════════════════════
      for (let i = 0; i < files.length; i++) {
        const fileEntry = files[i]
        setFiles(prev => prev.map(f =>
          f.id === fileEntry.id ? { ...f, status: 'processing' } : f
        ))

        try {
          const formData = new FormData()
          formData.append('documents', fileEntry.file)

          const response = await api.post('/process', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 180000,
          })

          const data = response.data
          const result = data.results?.[0] || data
          newResults.push(result)

          setFiles(prev => prev.map(f =>
            f.id === fileEntry.id ? { ...f, status: 'done', result } : f
          ))
        } catch (error) {
          const errorMsg = error.response?.data?.error || error.message
          setFiles(prev => prev.map(f =>
            f.id === fileEntry.id ? { ...f, status: 'error', result: { error: errorMsg } } : f
          ))
          toast.error(`Erreur : ${fileEntry.name}`)
        }

        setProgress(Math.round(((i + 1) / totalFiles) * 100))
      }
    }

    setResults(newResults)
    setProcessing(false)
  }, [files, batchMode])

  const reset = useCallback(() => {
    setFiles([])
    setResults([])
    setProgress(0)
  }, [])

  return (
    <UploadContext.Provider value={{ files, addFiles, removeFile, processFiles, processing, progress, results, reset, batchMode, setBatchMode }}>
      {children}
    </UploadContext.Provider>
  )
}

export function useUploadContext() {
  const ctx = useContext(UploadContext)
  if (!ctx) throw new Error('useUploadContext must be used within UploadProvider')
  return ctx
}
