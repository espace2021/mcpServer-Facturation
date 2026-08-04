"""
myApi.py
-------------
Contient uniquement l'exécution des requêtes HTTP (GET/POST) vers l'API 
Aucune logique de tool MCP ici 
"""
import os
import httpx
from typing import Optional, Union
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("DEPOT_API_URL","https://backendfacturation.onrender.com")  
TIMEOUT = 90  # secondes


def _assert_config() -> None:

    if not API_BASE:
        raise RuntimeError("Missing BASE_URL env var")
  

def api_get(path: str, params: Optional[dict] = None) -> Union[list, dict]:
    _assert_config()
    url = f"{API_BASE}{path}"
    with httpx.Client(timeout=TIMEOUT, http2=False, verify=False, follow_redirects=True) as client:
        res = client.get(url, params=params, headers={"Accept": "application/json"})
    res.raise_for_status()
    data = res.json()
    # L'API peut renvoyer soit une liste directement, soit un dict {"value": [...]}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("value", [])
    return data
   


def api_post(path: str, body: dict) -> Union[list, dict]:
    _assert_config()
    url = f"{API_BASE}{path}"
    with httpx.Client(timeout=TIMEOUT, http2=False, verify=False, follow_redirects=True) as client:
        res = client.post(
            url,
            json=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    res.raise_for_status()
    return res.json()

def _extraire_erreur(err):
    reponse = getattr(err, "response", None)
    if reponse is not None:
        status = getattr(reponse, "status_code", "?")
        try:
            body = reponse.json()
            return f"HTTP {status}: {body}"
        except ValueError:
            text = getattr(reponse, "text", "")
            if text:
                return f"HTTP {status}: {text}"
            return f"HTTP {status}: réponse vide, headers={dict(reponse.headers)}"
    return f"{type(err).__name__}: {str(err) or 'aucun message'}"