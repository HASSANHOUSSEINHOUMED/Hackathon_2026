import { useState, useCallback } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function useUpload() {
  const [files, setFiles] = useState([])
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState([])

  const addFiles = useCallback((newFiles) => {
    const mapped = newFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      name: file.name,
      size: file.size,
      status: 'pending', // pending | processing | done | error
      result: null,
    }))
    setFiles(prev => [...prev, ...mapped])
  }, [])

  const removeFile = useCallback((id) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const processFiles = useCallback(async () => {
    if (files.length === 0) return

    setProcessing(true)
    setProgress(0)
    setResults([])

    const totalFiles = files.length
    const newResults = []

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

    setResults(newResults)
    setProcessing(false)
    toast.success(`${newResults.length}/${totalFiles} document(s) traité(s)`)
  }, [files])

  const reset = useCallback(() => {
    setFiles([])
    setResults([])
    setProgress(0)
  }, [])

  return { files, addFiles, removeFile, processFiles, processing, progress, results, reset }
}
