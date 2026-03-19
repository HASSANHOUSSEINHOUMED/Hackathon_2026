import 'dotenv/config'
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import rateLimit from 'express-rate-limit'
import morgan from 'morgan'
import mongoose from 'mongoose'
import { createServer } from 'http'
import { Server as SocketServer } from 'socket.io'

import processRoutes from './routes/process.js'
import documentRoutes from './routes/documents.js'
import supplierRoutes from './routes/suppliers.js'
import validationRoutes from './routes/validation.js'
import storageRoutes from './routes/storage.js'
// import llmRoutes from './routes/llm.js'

const app = express()
const httpServer = createServer(app)
const io = new SocketServer(httpServer, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
})

// Security headers
app.use(helmet({
  contentSecurityPolicy: false,
  crossOriginEmbedderPolicy: false,
}))

// Strict CORS
const allowedOrigins = (process.env.ALLOWED_ORIGINS || 'http://localhost:3000,http://localhost:4000').split(',')
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.some(o => o.trim() === origin)) {
      callback(null, true)
    } else {
      callback(new Error('CORS: Origin non autorisée'))
    }
  },
  credentials: true,
}))

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 1000,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Trop de requêtes. Réessayez dans quelques minutes.' },
  skip: (req) => req.path === '/api/health',
})
app.use('/api/', apiLimiter)

app.use(morgan('combined'))
app.use(express.json({ limit: '20mb' }))

// Rendre io accessible dans les routes
app.set('io', io)

// Routes
app.use('/api/process', processRoutes)
app.use('/api/documents', documentRoutes)
app.use('/api/suppliers', supplierRoutes)
app.use('/api/validation', validationRoutes)
app.use('/api/storage', storageRoutes)
// app.use('/api/llm', llmRoutes)

// Admin UI auth check (server-side password validation)
app.post('/api/auth/admin-login', (req, res) => {
  const providedPassword = String(req.body?.password || '')
  const expectedPassword = process.env.ADMIN_UI_PASSWORD || 'Admin@2026'

  if (!providedPassword) {
    return res.status(400).json({ success: false, error: 'Mot de passe requis' })
  }

  if (providedPassword !== expectedPassword) {
    return res.status(401).json({ success: false, error: 'Mot de passe incorrect' })
  }

  return res.json({ success: true })
})

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'docuflow-backend',
    mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
    uptime: process.uptime(),
  })
})

// Socket.io
io.on('connection', (socket) => {
  console.log(`Client connecté : ${socket.id}`)
  socket.on('disconnect', () => {
    console.log(`Client déconnecté : ${socket.id}`)
  })
})

// Connexion MongoDB
const MONGO_URI = process.env.MONGO_URI || 'mongodb://admin:admin@localhost:27017/hackathon?authSource=admin'
const PORT = process.env.PORT || 4000

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log('✅ MongoDB connecté')
    httpServer.listen(PORT, () => {
      console.log(`🚀 Backend démarré sur le port ${PORT}`)
    })
  })
  .catch((err) => {
    console.error('❌ Erreur MongoDB :', err.message)
    process.exit(1)
  })

export default app
