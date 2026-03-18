import 'dotenv/config'
import express from 'express'
import cors from 'cors'
import morgan from 'morgan'
import mongoose from 'mongoose'
import { createServer } from 'http'
import { Server as SocketServer } from 'socket.io'

import processRoutes from './routes/process.js'
import documentRoutes from './routes/documents.js'
import supplierRoutes from './routes/suppliers.js'
import validationRoutes from './routes/validation.js'
import llmRoutes from './routes/llm.js'

const app = express()
const httpServer = createServer(app)
const io = new SocketServer(httpServer, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
})

// Middleware
app.use(cors())
app.use(morgan('combined'))
app.use(express.json({ limit: '20mb' }))

// Rendre io accessible dans les routes
app.set('io', io)

// Routes
app.use('/api/process', processRoutes)
app.use('/api/documents', documentRoutes)
app.use('/api/suppliers', supplierRoutes)
app.use('/api/validation', validationRoutes)
app.use('/api/llm', llmRoutes)

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
