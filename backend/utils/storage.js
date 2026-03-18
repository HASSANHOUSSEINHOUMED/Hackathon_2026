/**
 * Client MinIO pour le stockage des documents dans le Data Lake.
 * 3 zones : raw-zone (fichiers bruts), clean-zone (OCR), curated-zone (validé)
 */
import { Client } from 'minio'
import fs from 'fs'
import path from 'path'

const ZONES = {
  RAW: 'raw-zone',
  CLEAN: 'clean-zone',
  CURATED: 'curated-zone',
  PENDING: 'pending-zone',
}

class MinioStorage {
  constructor() {
    this.client = new Client({
      endPoint: process.env.MINIO_ENDPOINT || 'minio',
      port: parseInt(process.env.MINIO_PORT || '9000'),
      useSSL: process.env.MINIO_SECURE === 'true',
      accessKey: process.env.MINIO_ACCESS_KEY || process.env.MINIO_ROOT_USER || 'minioadmin',
      secretKey: process.env.MINIO_SECRET_KEY || process.env.MINIO_ROOT_PASSWORD || 'minioadmin',
    })
    this.initialized = false
  }

  /**
   * Initialise les buckets si nécessaire
   */
  async init() {
    if (this.initialized) return

    for (const zone of Object.values(ZONES)) {
      const exists = await this.client.bucketExists(zone)
      if (!exists) {
        await this.client.makeBucket(zone)
        console.log(`[MinIO] Bucket créé: ${zone}`)
      }
    }
    this.initialized = true
    console.log('[MinIO] Connecté et initialisé')
  }

  /**
   * Génère le préfixe date du jour
   */
  _datePrefix() {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  }

  /**
   * Upload un fichier brut dans raw-zone
   * @param {string} filePath - Chemin local du fichier
   * @param {string} documentId - ID du document
   * @param {object} metadata - Métadonnées additionnelles
   * @returns {Promise<string>} - Chemin MinIO
   */
  async uploadRaw(filePath, documentId, metadata = {}) {
    await this.init()

    const ext = path.extname(filePath)
    const objectName = `${this._datePrefix()}/${documentId}${ext}`

    const metaHeaders = {
      'X-Amz-Meta-Document-Id': documentId,
      'X-Amz-Meta-Original-Name': path.basename(filePath),
      'X-Amz-Meta-Upload-Time': new Date().toISOString(),
      ...Object.fromEntries(
        Object.entries(metadata).map(([k, v]) => [`X-Amz-Meta-${k}`, String(v)])
      ),
    }

    await this.client.fPutObject(ZONES.RAW, objectName, filePath, metaHeaders)
    console.log(`[MinIO] Upload raw: ${ZONES.RAW}/${objectName}`)

    return `${ZONES.RAW}/${objectName}`
  }

  /**
   * Upload le résultat OCR dans clean-zone
   * @param {string} documentId - ID du document
   * @param {object} ocrResult - Résultat OCR
   * @returns {Promise<string>} - Chemin MinIO
   */
  async uploadClean(documentId, ocrResult) {
    await this.init()

    const objectName = `${this._datePrefix()}/${documentId}.json`
    const data = JSON.stringify(ocrResult, null, 2)

    await this.client.putObject(ZONES.CLEAN, objectName, data, {
      'Content-Type': 'application/json',
    })
    console.log(`[MinIO] Upload clean: ${ZONES.CLEAN}/${objectName}`)

    return `${ZONES.CLEAN}/${objectName}`
  }

  /**
   * Upload le document validé dans curated-zone
   * @param {string} documentId - ID du document
   * @param {object} validatedData - Données validées
   * @returns {Promise<string>} - Chemin MinIO
   */
  async uploadCurated(documentId, validatedData) {
    await this.init()

    const objectName = `${this._datePrefix()}/${documentId}.json`
    const data = JSON.stringify(validatedData, null, 2)

    await this.client.putObject(ZONES.CURATED, objectName, data, {
      'Content-Type': 'application/json',
    })
    console.log(`[MinIO] Upload curated: ${ZONES.CURATED}/${objectName}`)

    return `${ZONES.CURATED}/${objectName}`
  }

  /**
   * Génère une URL présignée pour télécharger un fichier
   * @param {string} zone - Zone (bucket)
   * @param {string} objectName - Nom de l'objet
   * @param {number} expirySeconds - Durée de validité (défaut 24h)
   * @returns {Promise<string>} - URL présignée
   */
  async getPresignedUrl(zone, objectName, expirySeconds = 86400) {
    await this.init()
    return this.client.presignedGetObject(zone, objectName, expirySeconds)
  }

  /**
   * Liste les fichiers d'une zone
   * @param {string} zone - Zone (bucket)
   * @param {string} prefix - Préfixe optionnel
   * @returns {Promise<Array>} - Liste des objets
   */
  async listObjects(zone, prefix = '') {
    await this.init()
    const objects = []
    const stream = this.client.listObjectsV2(zone, prefix, true)

    return new Promise((resolve, reject) => {
      stream.on('data', (obj) => objects.push(obj))
      stream.on('end', () => resolve(objects))
      stream.on('error', reject)
    })
  }

  /**
   * Statistiques du stockage
   * @returns {Promise<object>} - Stats par zone
   */
  async getStats() {
    await this.init()
    const stats = {}

    for (const zone of Object.values(ZONES)) {
      const objects = await this.listObjects(zone)
      stats[zone] = {
        count: objects.length,
        size: objects.reduce((sum, obj) => sum + (obj.size || 0), 0),
      }
    }

    return stats
  }
}

// Singleton
const storage = new MinioStorage()

export { storage, ZONES }
export default storage
