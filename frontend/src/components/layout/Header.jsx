import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Wifi } from 'lucide-react'
import api from '../../services/api'

export default function Header({ title }) {
  const [services, setServices] = useState({
    backend: false,
    ocr: false,
  })

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.get('/health')
        setServices(prev => ({ ...prev, backend: true }))
      } catch {
        setServices(prev => ({ ...prev, backend: false }))
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header style={{
      height: 64,
      background: 'white',
      borderBottom: '1px solid #E2E8F0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 30px',
    }}>
      <h2 style={{
        fontFamily: 'Space Grotesk, sans-serif',
        fontSize: '1.3rem',
        color: '#1B2A4A',
      }}>
        {title}
      </h2>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <ServiceIndicator name="API" online={services.backend} />
      </div>
    </header>
  )
}

function ServiceIndicator({ name, online }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 13,
      color: online ? '#00C896' : '#E63946',
    }}>
      {online ? <CheckCircle size={14} /> : <XCircle size={14} />}
      <span>{name}</span>
    </div>
  )
}
