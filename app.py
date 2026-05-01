import streamlit as st

st.set_page_config(
    page_title="SI Habilitations — Accueil",
    page_icon="🔐",
    layout="wide",
)

from utils.ui import apply_styles, require_auth, render_sidebar, page_header
from utils.queries import stats_globales

apply_styles()
require_auth()
render_sidebar()

page_header("Tableau de bord")

stats = stats_globales()

c1, c2, c3, c4 = st.columns(4)
metrics = [
    (c1, stats.get("nb_etab",    0), "Établissements", "🏢"),
    (c2, stats.get("nb_app",     0), "Applications",   "📱"),
    (c3, stats.get("nb_profils", 0), "Profils",        "👥"),
    (c4, stats.get("nb_droits",  0), "Droits",         "🔑"),
]
for col, val, label, icon in metrics:
    col.markdown(
        f"""<div class="metric-card">
              <div class="value">{icon} {val}</div>
              <div class="label">{label}</div>
            </div>""",
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

> Conçu dans le cadre du programme **HospiConnect** (ANS — Agence du Numérique en Santé).
""")
