import { Router } from 'express'

const router = Router()

router.get('/status', (req, res) => {
  res.json({ available: false, reason: 'LLM désactivé' })
})

export default router
