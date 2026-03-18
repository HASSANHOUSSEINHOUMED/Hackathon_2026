"""
Détecteur d'anomalies statistiques via IsolationForest.
"""
import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("validation.statistical")

MODEL_PATH = Path("model_history.pkl")


class StatDetector:
    """Détection d'anomalies statistiques sur les montants des factures."""

    def __init__(self) -> None:
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.trained = False

    def _extract_features(self, document: dict) -> np.ndarray:
        """Extrait les features numériques d'un document."""
        entities = document.get("entities", {})
        montant_ht = float(entities.get("montant_ht") or 0)
        montant_ttc = float(entities.get("montant_ttc") or 0)
        tva = float(entities.get("tva") or 0)
        ratio_tva = tva / montant_ht if montant_ht > 0 else 0
        nb_lignes = int(entities.get("nb_lignes", 1))
        return np.array([montant_ttc, montant_ht, ratio_tva, nb_lignes])

    def fit(self, historical_data: list[dict]) -> None:
        """
        Entraîne le modèle sur des données historiques.

        Args:
            historical_data: liste de documents avec entities
        """
        if len(historical_data) < 10:
            logger.warning("Pas assez de données pour l'entraînement (%d)", len(historical_data))
            return

        features = np.array([self._extract_features(d) for d in historical_data])
        features = features[~np.isnan(features).any(axis=1)]
        features = features[~np.isinf(features).any(axis=1)]

        if len(features) < 10:
            logger.warning("Pas assez de features valides (%d)", len(features))
            return

        self.scaler.fit(features)
        scaled = self.scaler.transform(features)
        self.model.fit(scaled)
        self.trained = True

        joblib.dump({"model": self.model, "scaler": self.scaler}, MODEL_PATH)
        logger.info("Modèle entraîné sur %d échantillons et sauvegardé", len(features))

    def predict(self, document: dict) -> dict:
        """
        Prédit si un document contient une anomalie statistique.

        Returns:
            {"is_anomaly": bool, "anomaly_score": float, "explanation": str}
        """
        if not self.trained:
            return {"is_anomaly": False, "anomaly_score": 0.0, "explanation": "Modèle non entraîné"}

        features = self._extract_features(document).reshape(1, -1)
        if np.isnan(features).any() or np.isinf(features).any():
            return {"is_anomaly": False, "anomaly_score": 0.0, "explanation": "Données incomplètes"}

        scaled = self.scaler.transform(features)
        prediction = self.model.predict(scaled)[0]  # -1 = anomaly, 1 = normal
        score = self.model.score_samples(scaled)[0]

        is_anomaly = prediction == -1
        explanation = "Normal"
        if is_anomaly:
            montant = features[0][0]
            explanation = f"Montant TTC ({montant:.2f}€) statistiquement anormal (score: {score:.3f})"

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(score), 4),
            "explanation": explanation,
        }

    def load_or_train(self, dataset_path: str | None = None) -> None:
        """Charge un modèle existant ou entraîne sur le dataset."""
        if MODEL_PATH.exists():
            try:
                data = joblib.load(MODEL_PATH)
                self.model = data["model"]
                self.scaler = data["scaler"]
                self.trained = True
                logger.info("Modèle chargé depuis %s", MODEL_PATH)
                return
            except Exception as e:
                logger.warning("Erreur chargement modèle : %s", e)

        if dataset_path:
            import json
            path = Path(dataset_path)
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                docs = [{"entities": d.get("expected_fields", {})} for d in data]
                self.fit(docs)
