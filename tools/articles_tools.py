"""
articles_tools.py
-----------------
Définit les tools MCP pour les articles.
"""

from fastmcp import FastMCP

from api.myApi import api_get, _extraire_erreur

mcp = FastMCP("Facturation")



def _get_articles():
    """Récupère la liste des articles quelle que soit la structure de réponse."""
    data = api_get("/articles/")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return (
            data.get("data")
            or data.get("items")
            or data.get("articles")
            or []
        )

    return []


# =========================================================
# TOOL 1 : GET ARTICLE PAR ID
# =========================================================

@mcp.tool(
    name="getArticleByID",
    description="Retourne un article à partir de son identifiant."
)
def get_article_by_id(id_article: int) -> dict:

    try:
        articles = _get_articles()

        article = next(
            (
                a for a in articles
                if int(a.get("id_article")) == int(id_article)
            ),
            None,
        )

        if article is None:
            return {
                "ok": False,
                "message": f"Aucun article avec l'id {id_article}"
            }

        return {
            "ok": True,
            "data": article
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }


# =========================================================
# TOOL 2 : FILTRAGE PAR PRIX DE VENTE
# =========================================================

@mcp.tool(
    name="filterArticlesByPriceRange",
    description="Retourne les articles compris entre prix_min et prix_max."
)
def filter_articles_by_price_range(
    prix_min: float | None = None,
    prix_max: float | None = None,
) -> dict:

    try:
        articles = _get_articles()

        resultat = []

        for article in articles:

            prix = article.get("prix_vente")

            if prix is None:
                continue

            prix = float(prix)

            if prix_min is not None and prix < prix_min:
                continue

            if prix_max is not None and prix > prix_max:
                continue

            resultat.append(article)

        return {
            "ok": True,
            "count": len(resultat),
            "prix_min": prix_min,
            "prix_max": prix_max,
            "data": resultat,
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }


# =========================================================
# TOOL 3 : RECHERCHE D'ARTICLES
# =========================================================

@mcp.tool(
    name="searchArticles",
    description="Recherche un article par désignation, catégorie ou identifiant."
)
def search_articles(query: str) -> dict:

    try:
        articles = _get_articles()

        q = query.lower().strip()

        resultat = []

        for article in articles:

            if (
                q in str(article.get("designation", "")).lower()
                or q in str(article.get("categorie", "")).lower()
                or q in str(article.get("id_article", "")).lower()
            ):
                resultat.append(article)

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
# TOOL : ARTICLES EN RUPTURE DE STOCK
# =========================================================

@mcp.tool(
    name="getArticleRuptureStock",
    description="Retourne la liste des articles dont le stock est égal à 0."
)
def get_article_rupture_stock() -> dict:
    try:
        articles = _get_articles()

        articles_rupture = [
            article
            for article in articles
            if int(article.get("stock", 0)) == 0
        ]

        return {
            "ok": True,
            "count": len(articles_rupture),
            "data": articles_rupture,
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
    "getArticleByID",
    "filterArticlesByPriceRange",
    "searchArticles",
    "getArticleRuptureStock",
]

print("\n📌 Tools Articles enregistrés :")

for tool in TOOLS:
    print(f" • {tool}")