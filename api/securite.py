"""Lecture et vérification des clés d'API du service versionné."""
import os
from collections.abc import Mapping

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

_ENTETE_CLE = APIKeyHeader(name="X-API-Key", auto_error=False)
ROLES_VALIDES = {"client", "admin"}


def charger_cles() -> dict[str, str]:
    """Lit API_KEYS au format clé:role,clé:role et refuse une configuration invalide."""
    configuration = os.environ.get("API_KEYS", "").strip()
    cles: dict[str, str] = {}
    if not configuration:
        return cles
    for entree in configuration.split(","):
        morceaux = entree.strip().rsplit(":", 1)
        if len(morceaux) != 2:
            raise ValueError("API_KEYS doit utiliser le format clé:role")
        cle, role = morceaux[0].strip(), morceaux[1].strip()
        if len(cle) < 16 or role not in ROLES_VALIDES:
            raise ValueError("API_KEYS contient une clé trop courte ou un rôle invalide")
        if cle in cles:
            raise ValueError("API_KEYS contient une clé en double")
        cles[cle] = role
    return cles


async def role_requis(cle: str | None = Security(_ENTETE_CLE)) -> str:
    cles: Mapping[str, str] = charger_cles()
    if cle is None:
        raise HTTPException(401, detail={"erreur": {"code": "NON_AUTHENTIFIE", "message": "Clé d'API manquante : en-tête X-API-Key", "champs": []}})
    role = cles.get(cle)
    if role is None:
        raise HTTPException(401, detail={"erreur": {"code": "NON_AUTHENTIFIE", "message": "Clé d'API invalide", "champs": []}})
    return role


def exiger_role(role_attendu: str):
    async def verifier(role: str = Depends(role_requis)) -> str:
        if role_attendu == "admin" and role != "admin":
            raise HTTPException(403, detail={"erreur": {"code": "ACCES_REFUSE", "message": "Accès refusé au rôle client", "champs": []}})
        return role
    return verifier
