"""
analyse_reglements_tools.py
-----------------
Définit les tools MCP liés à l'analyse des règlements 

analyser_reglements : Récupère les paiements via /reglements/, 
croise avec /factures/ pour identifier le client, 
puis calcule le montant total perçu avec une ventilation par mode de paiement 
(Virement, Chèque, etc.) et par client.

detecter_anomalies : Recompose le montant Total TTC exact de chaque facture 
à partir des lignes d'articles (prix_vente_ht * quantite * (1 + taux_tva / 100)), puis le compare aux sommes perçues pour soulever les cas de sur-paiement, 
sous-paiement ou mauvaise affectation de statut.
"""

from fastmcp import FastMCP
from api.myApi import api_get,_extraire_erreur

mcp = FastMCP("Facturation")


# =========================================================
# HELPER POUR LES RÈGLEMENTS ET FACTURES
# =========================================================

def _get_reglements():
    data = api_get("/reglements/")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("items") or data.get("reglements") or []
    return []

def _get_factures():
    data = api_get("/factures/")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("items") or data.get("factures") or []
    return []

def _get_lignes_facture():
    data = api_get("/lignes-facture/")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("items") or data.get("lignes") or []
    return []


# =========================================================
# TOOL 1 : ANALYSER LES RÈGLEMENTS
# =========================================================

@mcp.tool(
    name="analyserReglements",
    description="Analyse globale des règlements : total encaissé, répartition par mode de paiement et par client."
)
def analyser_reglements(id_client: int | None = None) -> dict:
    try:
        reglements = _get_reglements()
        factures = {f["id_facture"]: f for f in _get_factures()}

        total_encaisse = 0.0
        par_mode = {}
        par_client = {}

        for r in reglements:
            id_facture = r.get("id_facture")
            facture = factures.get(id_facture, {})
            client_id = facture.get("id_client")

            # Filtrage optionnel par client
            if id_client is not None and client_id != id_client:
                continue

            montant = float(r.get("montant", 0))
            mode = r.get("mode", "Inconnu")

            total_encaisse += montant
            par_mode[mode] = par_mode.get(mode, 0.0) + montant

            if client_id:
                par_client[client_id] = par_client.get(client_id, 0.0) + montant

        return {
            "ok": True,
            "total_encaisse": round(total_encaisse, 2),
            "nombre_reglements": len(reglements),
            "ventilation_par_mode": par_mode,
            "ventilation_par_client": par_client
        }

    except Exception as err:
        return {
            "ok": False,
            "message": "API error",
            "error": _extraire_erreur(err),
        }


# =========================================================
# TOOL 2 : DÉTECTER LES ANOMALIES DE RÈGLEMENTS
# =========================================================

@mcp.tool(
    name="detecterAnomalies",
    description="Détecte les écarts entre le montant TTC calculé des factures et le total réellement réglé, ainsi que les statuts incohérents."
)
def detecter_anomalies() -> dict:
    try:
        factures = _get_factures()
        lignes = _get_lignes_facture()
        reglements = _get_reglements()

        # 1. Calcul du montant TTC par facture
        montants_ttc_facture = {}
        for l in lignes:
            id_f = l.get("id_facture")
            ht = float(l.get("prix_vente_ht", 0)) * float(l.get("quantite", 0))
            tva = float(l.get("taux_tva", 0)) / 100
            ttc = ht * (1 + tva)
            
            montants_ttc_facture[id_f] = montants_ttc_facture.get(id_f, 0.0) + ttc

        # 2. Somme des règlements par facture
        reglements_par_facture = {}
        for r in reglements:
            id_f = r.get("id_facture")
            reglements_par_facture[id_f] = reglements_par_facture.get(id_f, 0.0) + float(r.get("montant", 0))

        anomalies = []

        # 3. Analyse des écarts
        for f in factures:
            id_f = f.get("id_facture")
            statut = f.get("statut")
            ttc_attendu = round(montants_ttc_facture.get(id_f, 0.0), 2)
            total_paye = round(reglements_par_facture.get(id_f, 0.0), 2)
            ecart = round(total_paye - ttc_attendu, 2)

            # Incohérence de sous-paiement ou sur-paiement
            if abs(ecart) > 0.01:
                anomalies.append({
                    "id_facture": id_f,
                    "type": "SURPAYÉ" if ecart > 0 else "SOUS_PAYÉ",
                    "statut_actuel": statut,
                    "montant_ttc": ttc_attendu,
                    "total_regle": total_paye,
                    "ecart": ecart
                })
            # Incohérence de statut (ex: marquée Payée mais montant insuffisant)
            elif statut == "Payée" and total_paye < ttc_attendu:
                anomalies.append({
                    "id_facture": id_f,
                    "type": "STATUT_INCOHERENT",
                    "statut_actuel": statut,
                    "montant_ttc": ttc_attendu,
                    "total_regle": total_paye,
                    "ecart": ecart
                })

        return {
            "ok": True,
            "count": len(anomalies),
            "anomalies": anomalies
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
    "analyserReglements",
    "detecterAnomalies",
]

print("\n📌 Tools Analyse Règlements enregistrés :")

for tool in TOOLS:
    print(f" • {tool}")