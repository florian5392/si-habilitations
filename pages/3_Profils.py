"""
pages/3_Profils.py — CRUD des profils utilisateurs + duplication.

Un profil est lié à une application (FK id_application). Il représente un rôle
fonctionnel (ex. "Médecin", "Infirmier", "Admin") auquel on associe des droits
dans la matrice des habilitations.

La fonctionnalité de duplication copie un profil existant avec toutes ses
habilitations vers un nouveau nom — utile pour créer une variante légèrement
différente sans tout resaisir.
"""

import streamlit as st
import mysql.connector

st.set_page_config(page_title="Profils", page_icon="👥", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header, section_title, paginate, request_delete, request_dup_profil
from utils.db import run_insert, run_update, audit
from utils.queries import applications_list, profils_list

apply_styles()
require_auth()
selected_etab_id = render_sidebar()
page_header("👥 Profils")

# On charge les applications filtrées par l'établissement sélectionné en sidebar.
apps = applications_list(selected_etab_id)
if not apps:
    st.info("Aucune application disponible. Créez-en une d'abord.")
    st.stop()

app_opts        = {a["nom"]: a["id"] for a in apps}
selected_app    = st.selectbox("Application", list(app_opts.keys()), key="profils_app")
selected_app_id = app_opts[selected_app]

# ── Ajout ─────────────────────────────────────────────────────────────────────
with st.expander("Ajouter un profil", expanded=False):
    with st.form("add_profil"):
        nom  = st.text_input("Nom du profil")
        desc = st.text_area("Description")
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                try:
                    new_id = run_insert(
                        "INSERT INTO profils (id_application, nom, description) VALUES (%s,%s,%s)",
                        (selected_app_id, nom.strip(), desc.strip()),
                    )
                    audit("INSERT", "profils", new_id, "nom", None, nom.strip())
                    st.success("Profil ajouté.")
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("Un profil avec ce nom existe déjà pour cette application.")
            else:
                st.error("Le nom est obligatoire.")

# ── Liste ─────────────────────────────────────────────────────────────────────
profils = profils_list(selected_app_id)

if not profils:
    st.info("Aucun profil pour cette application.")
else:
    section_title(f"Liste — {len(profils)} profil(s)")
    # La clé de pagination inclut selected_app_id pour que la page se réinitialise
    # à 1 quand on change d'application.
    for p in paginate(profils, f"profils_{selected_app_id}"):
        with st.expander(p["nom"]):
            new_nom  = st.text_input("Nom",         value=p["nom"],              key=f"prof_nom_{p['id']}")
            new_desc = st.text_area("Description",  value=p["description"] or "", key=f"prof_desc_{p['id']}")

            c1, c2, c3 = st.columns(3)
            if c1.button("Modifier", key=f"prof_upd_{p['id']}"):
                if new_nom.strip():
                    try:
                        run_update(
                            "UPDATE profils SET nom=%s, description=%s WHERE id=%s",
                            (new_nom.strip(), new_desc.strip(), p["id"]),
                        )
                        audit("UPDATE", "profils", p["id"], "nom", p["nom"], new_nom.strip())
                        st.success("Modifié.")
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("Ce nom est déjà utilisé pour cette application.")
                else:
                    st.error("Le nom est obligatoire.")
            if c2.button("Dupliquer", key=f"prof_dup_{p['id']}"):
                # On passe id_application explicitement car la requête profils_list
                # ne le retourne pas dans le dict (optimisation du SELECT).
                request_dup_profil({**p, "id_application": selected_app_id})
            if c3.button("Supprimer", key=f"prof_del_{p['id']}"):
                request_delete(
                    p["nom"],
                    "DELETE FROM profils WHERE id=%s",
                    (p["id"],),
                    "profils",
                    p["id"],
                )
