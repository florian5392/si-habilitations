"""
pages/7_Comparaison.py — Comparaison côte à côte de deux profils.

Permet de sélectionner deux profils d'une même application et d'afficher
un tableau de comparaison droit par droit, avec un code couleur :

  Vert  (B8EDF5) : même valeur pour les deux profils (y compris tous les deux absents)
  Orange (FFD9A0) : les deux profils ont une valeur, mais différente
  Rouge  (F9A8A7) : droit présent pour l'un, absent pour l'autre

Un résumé de trois métriques (identiques / différents / manquants) est affiché
en bas, suivi d'un bouton d'export Excel avec la même palette couleur.
"""

import streamlit as st

st.set_page_config(page_title="Comparaison de profils", page_icon="🔀", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header
from utils.queries import etablissements_list, applications_list, profils_list, get_habilitations_comparaison
from utils.export import build_xlsx_comparaison

apply_styles()
require_auth()
# On récupère la sélection de la sidebar pour pré-positionner le sélecteur
# d'établissement de cette page sur le même choix.
sidebar_etab_id = render_sidebar()
page_header("🔀 Comparaison de profils")

# ── Sélection établissement / application ──────────────────────────────────────
etabs = etablissements_list()
if not etabs:
    st.info("Aucun établissement disponible.")
    st.stop()

etab_map   = {e["nom"]: e["id"] for e in etabs}
etab_names = list(etab_map.keys())

# Retrouver l'index de l'établissement sélectionné en sidebar pour pré-sélectionner
# le même dans le selectbox local (améliore la cohérence UX entre les pages).
default_etab = 0
if sidebar_etab_id:
    for i, e in enumerate(etabs):
        if e["id"] == sidebar_etab_id:
            default_etab = i
            break

col_etab, col_app = st.columns(2)
with col_etab:
    sel_etab = st.selectbox("Établissement", etab_names, index=default_etab, key="cmp_etab")
id_etab = etab_map[sel_etab]

apps = applications_list(id_etab)
if not apps:
    st.info("Aucune application pour cet établissement.")
    st.stop()

app_map = {a["nom"]: a["id"] for a in apps}
with col_app:
    sel_app = st.selectbox("Application", list(app_map.keys()), key="cmp_app")
id_app = app_map[sel_app]

# ── Sélection des deux profils ─────────────────────────────────────────────────
profils = profils_list(id_app)
if len(profils) < 2:
    st.info("Il faut au moins deux profils pour effectuer une comparaison.")
    st.stop()

profil_map   = {p["nom"]: p for p in profils}
profil_names = list(profil_map.keys())

col_l, col_r = st.columns(2)
with col_l:
    sel_p1 = st.selectbox("Profil gauche", profil_names, index=0, key="cmp_p1")
with col_r:
    # Le profil droit démarre sur le second élément pour éviter de pré-sélectionner
    # le même profil des deux côtés.
    sel_p2 = st.selectbox(
        "Profil droit",
        profil_names,
        index=min(1, len(profil_names) - 1),
        key="cmp_p2",
    )

if sel_p1 == sel_p2:
    st.warning("Sélectionnez deux profils différents.")
    st.stop()

p1 = profil_map[sel_p1]
p2 = profil_map[sel_p2]

# ── Récupération des données de comparaison ───────────────────────────────────
# get_habilitations_comparaison retourne tous les droits de l'application avec,
# pour chacun, la valeur du profil 1 (valeur_1) et du profil 2 (valeur_2).
# Un LEFT JOIN est utilisé : valeur_1 ou valeur_2 peut être NULL si le profil
# n'a aucune habilitation définie pour ce droit.
rows = get_habilitations_comparaison(p1["id"], p2["id"], id_app)
if not rows:
    st.info("Aucun droit défini pour cette application.")
    st.stop()

# ── Construction du tableau HTML ──────────────────────────────────────────────
def _fmt(val, type_valeur):
    """Formate une valeur BDD en texte lisible (Oui/Non pour booléens, — pour NULL)."""
    if val is None:
        return "—"
    if type_valeur == "booleen":
        return "Oui" if str(val) == "1" else "Non"
    return val if val else "—"

TH = (
    "background:#37306E;color:#FFF5E9;padding:8px 14px;"
    "border:1px solid #ccc;font-family:Arial;font-weight:bold"
)
TD_LABEL = (
    "padding:7px 12px;border:1px solid #ccc;font-family:Arial;"
    "font-weight:bold;background:#FFF5E9;color:#042638"
)
TD_BASE = "padding:7px 12px;border:1px solid #ccc;font-family:Arial;text-align:center;color:#042638"

# Couleurs de fond des cellules selon le statut de comparaison
COLOR_VERT   = "#B8EDF5"  # identique : bleu clair (dérivé du turquoise HospiConnect)
COLOR_ORANGE = "#FFD9A0"  # différent : orange clair
COLOR_ROUGE  = "#F9A8A7"  # manquant  : rouge clair (dérivé du corail HospiConnect)

nb_identique = nb_different = nb_manquant = 0
body = ""

for row in rows:
    v1   = _fmt(row["valeur_1"], row["type_valeur"])
    v2   = _fmt(row["valeur_2"], row["type_valeur"])
    has1 = row["valeur_1"] is not None  # True = valeur définie en BDD
    has2 = row["valeur_2"] is not None

    # Logique de classement (par ordre de priorité) :
    # 1. Présence asymétrique → Rouge (manquant) : l'un est vide, l'autre non
    # 2. Valeurs identiques  → Vert (ok)
    # 3. Valeurs différentes → Orange (à réviser)
    if has1 != has2:
        bg, statut = COLOR_ROUGE, "❌ Manquant"
        nb_manquant += 1
    elif v1 == v2:
        bg, statut = COLOR_VERT, "✅ Identique"
        nb_identique += 1
    else:
        bg, statut = COLOR_ORANGE, "⚠️ Différent"
        nb_different += 1

    td = f"{TD_BASE};background:{bg}"
    body += (
        f"<tr>"
        f"<td style='{TD_LABEL}'>{row['droit_nom']}</td>"
        f"<td style='{td}'>{v1}</td>"
        f"<td style='{td}'>{v2}</td>"
        f"<td style='{td}'><b>{statut}</b></td>"
        f"</tr>"
    )

header = (
    f"<tr>"
    f"<th style='{TH}'>Droit</th>"
    f"<th style='{TH}'>{sel_p1}</th>"
    f"<th style='{TH}'>{sel_p2}</th>"
    f"<th style='{TH}'>Statut</th>"
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

# ── Résumé ────────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("✅ Identiques", nb_identique)
c2.metric("⚠️ Différents", nb_different)
c3.metric("❌ Manquants", nb_manquant)

# ── Export Excel ───────────────────────────────────────────────────────────────
xlsx = build_xlsx_comparaison(sel_app, sel_p1, sel_p2, rows)
st.download_button(
    "⬇️ Exporter en Excel (.xlsx)",
    data=xlsx,
    file_name=f"comparaison_{sel_p1.replace(' ', '_')}_vs_{sel_p2.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
