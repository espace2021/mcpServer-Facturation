"""
clients_tools.py
-----------------
Définit les tools MCP pour les clients.
"""

from fastmcp import FastMCP

from api.myApi import api_get, api_post, _extraire_erreur

mcp = FastMCP("Facturation")

def _get_clients():
    """Récupère la liste des clients quelle que soit la structure de réponse."""
    data = api_get("/clients/")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return (
            data.get("data")
            or data.get("items")
            or data.get("clients")
            or []
        )

    return []

# =========================================================
# TOOL 1 : getClientByID
# =========================================================

@mcp.tool(
    name="getClientByID",
    description="Retourne un client à partir de son identifiant."
)
def get_client_by_id(id_client: int) -> dict:

    try:
        clients = _get_clients()

        client = next(
            (c for c in clients if int(c.get("id_client")) == int(id_client)),
            None,
        )

        if client is None:
            return {
                "ok": False,
                "message": f"Aucun client avec l'id {id_client}",
            }

        return {
            "ok": True,
            "data": client,
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }

# =========================================================
# TOOL 2 : searchClients
# =========================================================

@mcp.tool(
    name="searchClients",
    description="Recherche un client par nom, entreprise ou ville."
)
def search_clients(query: str) -> dict:

    try:
        clients = _get_clients()
        q = query.lower().strip()

        resultat = [
            c for c in clients
            if (
                q in str(c.get("nom", "")).lower()
                or q in str(c.get("entreprise", "")).lower()
                or q in str(c.get("ville", "")).lower()
            )
        ]

        return {
            "ok": True,
            "query": query,
            "count": len(resultat),
            "data": resultat,
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }


# =========================================================
# TOOL 3 : createClient
# =========================================================

@mcp.tool(
    name="createClient",
    description="Crée un nouveau client (nom, entreprise, ville)."
)
def create_client(
    nom: str,
    entreprise: str | None = None,
    ville: str | None = None,
) -> dict:

    try:
        body = {
            "nom": nom,
            "entreprise": entreprise,
            "ville": ville,
        }

        client = api_post("/clients/", body)

        return {
            "ok": True,
            "data": client,
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }

# =========================================================
# TOOLS ENREGISTRÉS
# =========================================================

TOOLS = [
    "getClientByID",
    "searchClients",
    "createClient"

]

print("\n📌 Tools Clients enregistrés :")

for tool in TOOLS:
    print(f" • {tool}")