"""
pages/8_Vue_transversale.py — Vue d'un profil sur toutes les applications.

Permet de visualiser en un seul écran l'ensemble des habilitations d'un profil
(identifié par son nom) sur toutes les applications d'un établissement.

Cas d'usage : vérifier qu'un rôle "Médecin" a les mêmes droits cohérents sur
l'ensemble du SI de l'établissement, sans avoir à naviguer application par application.

Si plusieurs profils portent le même nom sur des applications différentes
(cas courant en multi-applicatif), ils sont tous affichés et regroupés
par application avec des couleurs de fond alternées.
"""

import streamlit as st

st.set_page_config(page_title="Vue transversale", page_icon="📐", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header
from utils.queries import (
    etablissements_list,
    get_profils_by_etablissement,
    get_habilitations_transversales,
)
from utils.export import build_xlsx_transversale

apply_styles()
require_auth()
sidebar_etab_id = render_sidebar()
page_header("📐 Vue transversale par profil")

# ── Sélection de l'établissement ──────────────────────────────────────────────
etabs = etablissements_list()
if not etabs:
    st.info("Aucun établissement disponible.")
    st.stop()

etab_map   = {e["nom"]: e["id"] for e in etabs}
etab_names = list(etab_map.keys())

# Pré-sélection cohérente avec la sidebar (même logique que 7_Comparaison.py)
default_etab = 0
if sidebar_etab_id:
    for i, e in enumerate(etabs):
        if e["id"] == sidebar_etab_id:
            default_etab = i
            break

sel_etab = st.selectbox("Établissement", etab_names, index=default_etab, key="tvx_etab")
id_etab  = etab_map[sel_etab]

# ── Sélection du profil ────────────────────────────────────────────────────────
# get_profils_by_etablissement retourne les noms distincts de profils sur toutes
# les applications de l'établissement (DISTINCT sur p.nom).
profil_rows = get_profils_by_etablissement(id_etab)
if not profil_rows:
    st.info("Aucun profil défini pour cet établissement.")
    st.stop()

profil_names = [p["nom"] for p in profil_rows]
sel_profil   = st.selectbox("Profil", profil_names, key="tvx_profil")

# ── Données transversales ─────────────────────────────────────────────────────
# La requête retourne une ligne par (application, droit), triée par a.nom puis d.nom.
# Cet ordre est essentiel pour que le regroupement visuel par application soit cohérent.
rows = get_habilitations_transversales(sel_profil, id_etab)
if not rows:
    st.info("Aucune donnée pour ce profil sur cet établissement.")
    st.stop()

# ── Tableau HTML avec alternance de couleur par application ────────────────────
TH = (
    "background:#37306E;color:#FFF5E9;padding:8px 14px;"
    "border:1px solid #ccc;font-family:Arial;font-weight:bold"
)
TD_BASE = "padding:7px 12px;border:1px solid #ccc;font-family:Arial;color:#042638"

# Deux tons de fond pour alterner entre les groupes d'applications
BG_APP = ["#EBF5FB", "#FFF5E9"]  # bleu clair / beige


def _fmt(val, type_valeur):
    """Formate une valeur BDD en texte lisible."""
    if val is None:
        return "—"
    if type_valeur == "booleen":
        return "Oui" if str(val) == "1" else "Non"
    return val if val else "—"


header = (
    f"<tr>"
    f"<th style='{TH}'>Application</th>"
    f"<th style='{TH}'>Droit</th>"
    f"<th style='{TH}'>Valeur</th>"
    f"</tr>"
)

body        = ""
current_app = None  # application en cours de traitement pour la détection de changement
app_idx     = 0     # compteur de groupes pour l'alternance de couleur

for row in rows:
    # Détection de changement de groupe d'application : on bascule la couleur de fond
    if row["app_nom"] != current_app:
        current_app = row["app_nom"]
        bg_row = BG_APP[app_idx % 2]
        app_idx += 1

    val    = _fmt(row["valeur"], row["type_valeur"])
    # Valeur "active" : turquoise pour une valeur renseignée, gris clair pour absente.
    # "0" est considéré absent pour les booléens (droit non accordé).
    is_set = row["valeur"] is not None and row["valeur"] not in ("", "0")
    bg_val = "#4CBFDC" if is_set else "#F0F0F0"

    body += (
        f"<tr>"
        f"<td style='{TD_BASE};background:{bg_row}'>{row['app_nom']}</td>"
        f"<td style='{TD_BASE};background:{bg_row}'>{row['droit_nom']}</td>"
        f"<td style='{TD_BASE};background:{bg_val};text-align:center'>{val}</td>"
        f"</tr>"
    )

st.markdown(
    f"<div style='overflow-x:auto'>"
    f"<table style='border-collapse:collapse;width:100%'>"
    f"<thead>{header}</thead>"
    f"<tbody>{body}</tbody>"
    f"</table></div>",
    unsafe_allow_html=True,
)

# ── Export Excel ───────────────────────────────────────────────────────────────
st.markdown("---")
xlsx = build_xlsx_transversale(sel_profil, sel_etab, rows)
st.download_button(
    "⬇️ Exporter en Excel (.xlsx)",
    data=xlsx,
    file_name=f"transversale_{sel_profil.replace(' ', '_')}_{sel_etab.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
