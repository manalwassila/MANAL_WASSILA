"""API REST du classifier de sentiment (TP3, corrigée au TP4).

Lancer : uvicorn api.main:app --reload
Doc    : http://localhost:8000/docs
"""
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.model import Prediction, SentimentClassifier, load_model
from api.schemas import HealthResponse, PredictRequest, PredictResponse
from api.securite import charger_cles
from api.v1 import router as v1_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sentiment_api")
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Charge le modèle une seule fois, avant la première requête."""
    logger.info("Démarrage de l'API...")
    nb_cles = len(charger_cles())
    if not nb_cles:
        logger.warning("Aucune clé dans API_KEYS : les routes /v1 protégées répondront 401")
    app.state.classifier = load_model()
    logger.info("Modèle chargé avec succès : %s ; %d clé(s) d'API", app.state.classifier.model_name, nb_cles)
    yield
    logger.info("Arrêt de l'API")


app = FastAPI(
    title="Sentiment Analysis API",
    description="Classifie le sentiment d'un avis en français (modèle du TP2).",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS : indispensable pour un frontend web (TP5). En production, lister les domaines autorisés.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origine.strip() for origine in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",") if origine.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def _classifier() -> SentimentClassifier:
    clf: SentimentClassifier | None = getattr(app.state, "classifier", None)
    if clf is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return clf


app.include_router(v1_router)


@app.get("/", summary="Accueil")
async def root() -> dict[str, str]:
    return {"message": "Sentiment Analysis API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, summary="Santé de l'API")
async def health_check() -> dict[str, str]:
    """Répond 200 si le modèle est chargé, 503 sinon."""
    return {"status": "OK", "model": _classifier().model_name}


@app.post("/predict", response_model=PredictResponse, summary="Classifier un texte")
async def predict(request: PredictRequest) -> Prediction:
    """Renvoie POSITIVE, NEGATIVE, ou INDETERMINE sous le seuil d'abstention, et la confiance.

    - 422 : texte vide, fait de blancs ou trop long : refusé par le schéma, toujours sous la même forme
    - 503 : modèle non chargé
    - 500 : toute erreur du modèle, quelle qu'elle soit (journalisée, jamais renvoyée au client)
    """
    clf = _classifier()
    try:
        result = clf.predict(request.text)
    except Exception:
        logger.exception("Erreur lors de la prédiction")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur") from None
    logger.info("predict: %r -> %s (%.2f)", request.text[:50], result["label"], result["score"])
    return result


if __name__ == "__main__":  # pragma: no cover  (lancement manuel : jamais exécuté sous pytest)
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
