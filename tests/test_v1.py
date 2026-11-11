"""Tests de sécurité, du contrat versionné et des cas d'indisponibilité de /v1."""
from pathlib import Path

import pytest

from api.securite import charger_cles
from api.v1 import charger_metriques

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "sentiment.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit par le workflow CI")

CLE_CLIENT = "cle-client-de-test-123456"
CLE_ADMIN = "cle-admin-de-test-123456"


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("API_KEYS", f"{CLE_CLIENT}:client,{CLE_ADMIN}:admin")
    with TestClient(app) as test_client:
        yield test_client


def test_charger_cles_absentes(monkeypatch):
    monkeypatch.delenv("API_KEYS", raising=False)
    assert charger_cles() == {}


def test_charger_cles_valides(monkeypatch):
    monkeypatch.setenv("API_KEYS", f"{CLE_CLIENT}:client,{CLE_ADMIN}:admin")
    assert charger_cles() == {CLE_CLIENT: "client", CLE_ADMIN: "admin"}


@pytest.mark.parametrize("configuration", [
    "entree-mal-formee",
    "trop-court:client",
    f"{CLE_CLIENT}:lecteur",
    f"{CLE_CLIENT}:client,{CLE_CLIENT}:admin",
])
def test_charger_cles_refuse_configuration_invalide(monkeypatch, configuration):
    monkeypatch.setenv("API_KEYS", configuration)
    with pytest.raises(ValueError):
        charger_cles()


def test_routes_v1_refusent_cle_absente_ou_invalide(client):
    assert client.post("/v1/predict", json={"text": "Très bon produit"}).status_code == 401
    assert client.post("/v1/predict", headers={"X-API-Key": "invalide"},
                       json={"text": "Très bon produit"}).status_code == 401


def test_route_prediction_accepte_une_cle_client(client):
    response = client.post("/v1/predict", headers={"X-API-Key": CLE_CLIENT},
                           json={"text": "Livraison rapide, produit conforme, très satisfait"})
    assert response.status_code == 200
    assert response.json()["label"] in {"POSITIVE", "NEGATIVE", "INDETERMINE"}


def test_route_admin_refuse_le_role_client(client):
    response = client.get("/v1/modele", headers={"X-API-Key": CLE_CLIENT})
    assert response.status_code == 403
    assert response.json()["detail"]["erreur"]["code"] == "ACCES_REFUSE"


def test_route_admin_renvoie_modele_seuil_et_metriques(client):
    response = client.get("/v1/modele", headers={"X-API-Key": CLE_ADMIN})
    assert response.status_code == 200
    assert response.json()["seuil_abstention"] == 0.60
    assert "model" in response.json()
    assert isinstance(response.json()["metriques"], dict)


def test_routes_v1_repondent_503_si_modele_absent(client, monkeypatch):
    from api.main import app

    monkeypatch.setattr(app.state, "classifier", None)
    assert client.post("/v1/predict", headers={"X-API-Key": CLE_CLIENT},
                       json={"text": "Avis valide"}).status_code == 503
    assert client.get("/v1/modele", headers={"X-API-Key": CLE_ADMIN}).status_code == 503


def test_route_prediction_masque_les_erreurs_internes(client, monkeypatch):
    from api.main import app

    class ModeleEnPanne:
        def predict(self, text):
            raise RuntimeError("secret interne")

    monkeypatch.setattr(app.state, "classifier", ModeleEnPanne())
    response = client.post("/v1/predict", headers={"X-API-Key": CLE_CLIENT},
                           json={"text": "Avis valide"})
    assert response.status_code == 500
    assert "secret interne" not in response.text


def test_charger_metriques_fichier_valide(tmp_path):
    fichier = tmp_path / "metrics.json"
    fichier.write_text('{"f1_macro": 0.87}', encoding="utf-8")
    assert charger_metriques(fichier) == {"f1_macro": 0.87}


@pytest.mark.parametrize("contenu", ["{", "[]"])
def test_charger_metriques_json_invalide_ou_non_objet(tmp_path, contenu):
    fichier = tmp_path / "metrics.json"
    fichier.write_text(contenu, encoding="utf-8")
    assert charger_metriques(fichier) == {}


def test_charger_metriques_fichier_absent(tmp_path):
    assert charger_metriques(tmp_path / "absent.json") == {}
