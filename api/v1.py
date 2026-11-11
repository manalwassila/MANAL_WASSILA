"""Routes versionnées de l'API de sentiment."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from api.model import Prediction
from api.schemas import PredictRequest, PredictResponse
from api.securite import exiger_role

router = APIRouter(prefix="/v1", tags=["v1"])


def charger_metriques(chemin: Path) -> dict[str, object]:
    """Lit les métriques suivies, sans faire échouer la route si le fichier manque."""
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return contenu if isinstance(contenu, dict) else {}


@router.post("/predict", response_model=PredictResponse)
async def prediction_v1(body: PredictRequest, request: Request,
                        _role: str = Depends(exiger_role("client"))) -> Prediction:
    """Classifie un avis après authentification du client."""
    classifier = getattr(request.app.state, "classifier", None)
    if classifier is None:
        raise HTTPException(503, detail="Modèle non chargé")
    try:
        return classifier.predict(body.text)
    except Exception:
        from logging import getLogger

        getLogger("sentiment_api").exception("Erreur lors de la prédiction v1")
        raise HTTPException(500, detail="Erreur interne du serveur") from None


@router.get("/modele", dependencies=[Depends(exiger_role("admin"))])
async def modele_v1(request: Request) -> dict[str, object]:
    """Expose les informations de diagnostic aux administrateurs uniquement."""
    from api.model import SEUIL_ABSTENTION

    classifier = getattr(request.app.state, "classifier", None)
    if classifier is None:
        raise HTTPException(503, detail="Modèle non chargé")
    racine = Path(__file__).resolve().parents[1]
    chemin_metriques = racine / "models" / "metrics.json"
    metriques = charger_metriques(chemin_metriques)
    return {"model": classifier.model_name, "seuil_abstention": SEUIL_ABSTENTION,
            "metriques": metriques}
