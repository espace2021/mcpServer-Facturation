"""
analyse_clients_tools.py
-----------------
Définit les tools MCP liés à l'analyse des clients : chiffre d'affaires et
retards de paiement.
"""

from collections import defaultdict
from datetime import date, datetime

from fastmcp import FastMCP
from api.myApi import api_get

mcp = FastMCP("Facturation")


# =========================================================
# UTILS
# =========================================================


def _fetch(endpoint: str) -> list:
    """Récupère une liste de données de l'API."""
    data = api_get(endpoint)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        key = endpoint.strip("/").split("/")[-1]
        return data.get("data") or data.get("items") or data.get(key) or []
    return []


def _parse_date(valeur) -> date | None:
    if not valeur:
        return None
    try:
        return datetime.strptime(str(valeur)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# =========================================================
# TOOL 1 : TOP CLIENTS PAR CHIFFRE D'AFFAIRES
# =========================================================

@mcp.tool(
    name="top_clients_ca",
    description="Retourne le classement des clients par chiffre d'affaires (TTC)."
)

def top_clients_ca(
    top_n: int = 10,
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> dict:
    clients = {c.get("id_client"): c for c in _fetch("/clients/")}
    factures = _fetch("/factures/")
    lignes = _fetch("/lignes-facture/")

    # Indexation des lignes par facture
    lignes_par_facture = defaultdict(list)
    for l in lignes:
        lignes_par_facture[l.get("id_facture")].append(l)

    b_debut, b_fin = _parse_date(date_debut), _parse_date(date_fin)
    ca_par_client = defaultdict(float)
    nb_factures = defaultdict(int)

    for f in factures:
        d_fact = _parse_date(f.get("date_facture"))
        if b_debut and (d_fact is None or d_fact < b_debut):
            continue
        if b_fin and (d_fact is None or d_fact > b_fin):
            continue

        id_client = f.get("id_client")
        tot_ttc = 0.0
        for l in lignes_par_facture.get(f.get("id_facture"), []):
            qte = float(l.get("quantite", 0) or 0)
            p_ht = float(l.get("prix_vente_ht", 0) or 0)
            tva = float(l.get("taux_tva", 0) or 0)
            tot_ttc += (qte * p_ht) * (1 + tva / 100)

        ca_par_client[id_client] += tot_ttc
        nb_factures[id_client] += 1

    top = sorted(ca_par_client.items(), key=lambda x: x[1], reverse=True)[:top_n]

    data = []
    for id_cli, val in top:
        c = clients.get(id_cli, {})
        data.append({
            "id_client": c.get("id_client", id_cli),
            "nom": c.get("nom"),
            "entreprise": c.get("entreprise"),
            "ville": c.get("ville"),
            "chiffre_affaires_ttc": round(val, 3),
            "nb_factures": nb_factures[id_cli],
        })

    return {"top_n": top_n, "date_debut": date_debut, "date_fin": date_fin, "count": len(data), "data": data}


# =========================================================
# TOOL 2 : CLIENTS EN RETARD DE PAIEMENT
# =========================================================

@mcp.tool(
    name="clients_retard_paiement",
    description="Retourne la liste des clients ayant au moins une facture impayée en retard."
)

def clients_retard_paiement() -> dict:
    clients = {c.get("id_client"): c for c in _fetch("/clients/")}
    factures = _fetch("/factures/")
    lignes = _fetch("/lignes-facture/")
    reglements = _fetch("/reglements/")

    # Indexation
    lignes_par_facture = defaultdict(list)
    for l in lignes:
        lignes_par_facture[l.get("id_facture")].append(l)

    regles_par_facture = defaultdict(float)
    for r in reglements:
        regles_par_facture[r.get("id_facture")] += float(r.get("montant", 0) or 0)

    aujourd_hui = date.today()
    par_client = defaultdict(lambda: {"total_du": 0.0, "factures": []})

    for f in factures:
        echeance = _parse_date(f.get("echeance"))
        if echeance is None or echeance >= aujourd_hui:
            continue

        id_facture = f.get("id_facture")
        montant_ttc = sum(
            float(l.get("quantite", 0) or 0) * float(l.get("prix_vente_ht", 0) or 0) * (1 + float(l.get("taux_tva", 0) or 0) / 100)
            for l in lignes_par_facture.get(id_facture, [])
        )
        solde = montant_ttc - regles_par_facture.get(id_facture, 0.0)

        if solde <= 0.01:
            continue

        id_client = f.get("id_client")
        retard_jours = (aujourd_hui - echeance).days

        par_client[id_client]["total_du"] += solde
        par_client[id_client]["factures"].append({
            "id_facture": id_facture,
            "date_facture": f.get("date_facture"),
            "echeance": f.get("echeance"),
            "montant_ttc": round(montant_ttc, 3),
            "solde_du": round(solde, 3),
            "jours_retard": retard_jours,
        })

    data = []
    for id_cli, infos in par_client.items():
        c = clients.get(id_cli, {})
        data.append({
            "id_client": c.get("id_client", id_cli),
            "nom": c.get("nom"),
            "entreprise": c.get("entreprise"),
            "ville": c.get("ville"),
            "total_du": round(infos["total_du"], 3),
            "nb_factures_en_retard": len(infos["factures"]),
            "jours_retard_max": max(f["jours_retard"] for f in infos["factures"]),
            "factures": infos["factures"],
        })

    data.sort(key=lambda x: x["total_du"], reverse=True)
    return {"count": len(data), "data": data}


# =========================================================
# TOOLS ENREGISTRÉS
# =========================================================

TOOLS = ["top_clients_ca", "clients_retard_paiement"]

print("\n📌 Tools Analyse Clients enregistrés :")
for tool in TOOLS:
    print(f" • {tool}")