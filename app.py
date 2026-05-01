"""
app.py — Page d'accueil : tableau de bord et suivi de complétude.

Cette page est le point d'entrée de l'application Streamlit multipage.
Elle doit appeler st.set_page_config() en tout premier, avant tout autre
import, car Streamlit impose que cette fonction soit la première instruction.
"""

import streamlit as st

st.set_page_config(
    page_title="SI Habilitations — Accueil",
    page_icon="🔐",
    layout="wide",
)

from utils.ui import apply_styles, require_auth, render_sidebar, page_header
from utils.queries import stats_globales, etablissements_list, get_completude_par_application

apply_styles()
require_auth()
render_sidebar()  # retourne selected_etab_id, non utilisé ici (filtre dédié plus bas)

page_header("Tableau de bord")

# ── Métriques globales ────────────────────────────────────────────────────────
# stats_globales() exécute deux requêtes SQL et retourne un dict avec :
# nb_etab, nb_app, nb_profils, nb_droits, taux_completude
stats = stats_globales()

c1, c2, c3, c4 = st.columns(4)
taux = stats.get("taux_completude", 0.0)
metrics = [
    (c1, stats.get("nb_etab",    0), "Établissements",  "🏢"),
    (c2, stats.get("nb_app",     0), "Applications",    "📱"),
    (c3, stats.get("nb_profils", 0), "Profils",         "👥"),
    (c4, f"{taux} %",               "Complétude globale", "📊"),
]
for col, val, label, icon in metrics:
    # Les cartes sont rendues en HTML brut pour contourner les limites
    # de st.metric (pas de personnalisation de couleur dans Streamlit).
    col.markdown(
        f"""<div class="metric-card">
              <div class="value">{icon} {val}</div>
              <div class="label">{label}</div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Filtre établissement ──────────────────────────────────────────────────────
# Ce filtre est local à la page d'accueil (indépendant du sélecteur de la sidebar).
etabs      = etablissements_list()
etab_map   = {e["nom"]: e["id"] for e in etabs}
etab_names = ["— Tous —"] + list(etab_map.keys())
sel_etab   = st.selectbox("Filtrer par établissement", etab_names, key="dash_etab")
filter_etab_id = etab_map.get(sel_etab)  # None si "— Tous —"

# ── Tableau de complétude ─────────────────────────────────────────────────────
completude_rows = get_completude_par_application(filter_etab_id)

if not completude_rows:
    st.info("Aucune application trouvée.")
else:
    # Tri Python par taux croissant (complétude la plus faible en premier).
    # Les applis sans structure (cellules_totales = 0 ou None) sont reléguées
    # en fin de liste via le taux fictif 1.1 (> 100 %), ce qui les isole
    # visuellement des applis à compléter.
    completude_rows.sort(
        key=lambda r: (r["cellules_renseignees"] or 0) / (r["cellules_totales"] or 1)
        if r["cellules_totales"]
        else 1.1
    )

    def _bar_color(pct):
        """Retourne la couleur de la barre de progression selon le seuil."""
        if pct < 50:
            return "#EA4D49"   # rouge : à compléter en priorité
        if pct < 80:
            return "#FFA500"   # orange : en cours
        return "#28A745"       # vert : satisfaisant

    # Styles inline pour le tableau HTML (Streamlit ne propose pas de table
    # avec cellules personnalisées ni barres de progression natives).
    TH = (
        "background:#37306E;color:#FFF5E9;padding:8px 12px;"
        "border:1px solid #ccc;font-family:Arial;font-weight:bold;white-space:nowrap"
    )
    TD = "padding:7px 10px;border:1px solid #ccc;font-family:Arial;color:#042638"

    headers = [
        "Établissement", "Application", "Profils", "Droits",
        "Renseignées", "Totales", "% Complétude",
    ]
    header_html = "".join(f"<th style='{TH}'>{h}</th>" for h in headers)

    body = ""
    for r in completude_rows:
        tot  = r["cellules_totales"] or 0
        rens = r["cellules_renseignees"] or 0
        pct  = round(100.0 * rens / tot, 1) if tot > 0 else 0.0
        color = _bar_color(pct)

        # Barre de progression HTML : div extérieur (fond gris) + div intérieur
        # (couleur variable) dont la largeur est exprimée en % de complétude.
        bar = (
            f"<div style='background:#eee;border-radius:4px;height:10px;margin-top:4px'>"
            f"<div style='background:{color};width:{pct}%;height:10px;border-radius:4px'></div>"
            f"</div>"
        )
        body += (
            f"<tr>"
            f"<td style='{TD}'>{r['etab_nom']}</td>"
            f"<td style='{TD}'>{r['app_nom']}</td>"
            f"<td style='{TD};text-align:center'>{r['nb_profils']}</td>"
            f"<td style='{TD};text-align:center'>{r['nb_droits']}</td>"
            f"<td style='{TD};text-align:center'>{rens}</td>"
            f"<td style='{TD};text-align:center'>{tot}</td>"
            f"<td style='{TD};min-width:140px'><b style='color:{color}'>{pct} %</b>{bar}</td>"
            f"</tr>"
        )

    st.markdown(
        f"<div style='overflow-x:auto'>"
        f"<table style='border-collapse:collapse;width:100%'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown("""
**SI Habilitations** est un outil open source de construction et de gestion des matrices
d'habilitations du Système d'Information, par application, multi-établissements.

Utilisez le menu latéral pour naviguer entre les sections :

| Page | Description |
|---|---|
| 🏢 Établissements | Gérer les sites / établissements |
| 📱 Applications | Gérer les applications métier |
| 👥 Profils | Définir les profils utilisateurs par application |
| 🔑 Droits | Définir les droits et leurs valeurs possibles |
| 📊 Matrice | Visualiser, éditer, importer et exporter les habilitations |
| 📋 Historique | Consulter le journal des modifications |
| 🔀 Comparaison | Comparer deux profils côte à côte |
| 📐 Vue transversale | Vision d'un profil sur toutes les applications |

> Conçu dans le cadre du programme **HospiConnect** (ANS — Agence du Numérique en Santé).
""")
