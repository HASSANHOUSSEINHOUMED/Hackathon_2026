import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import UploadPage from './pages/UploadPage'
import CRMPage from './pages/CRMPage'
import ConformityPage from './pages/ConformityPage'
import DocumentsPage from './pages/DocumentsPage'
import { UploadProvider } from './context/UploadContext'

export default function App() {
  return (
    <UploadProvider>
      <div className="app-layout">
        <Layout>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/crm" element={<CRMPage />} />
            <Route path="/conformity" element={<ConformityPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
          </Routes>
        </Layout>
      </div>
    </UploadProvider>
  )
}
