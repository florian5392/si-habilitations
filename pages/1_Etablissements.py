import streamlit as st

st.set_page_config(page_title="Établissements", page_icon="🏢", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header, section_title, paginate, request_delete
from utils.db import run_insert, run_update, audit
from utils.queries import etablissements_list
import mysql.connector

apply_styles()
require_auth()
render_sidebar()
page_header("🏢 Établissements")

# ── Ajout ─────────────────────────────────────────────────────────────────────
with st.expander("Ajouter un établissement", expanded=False):
    with st.form("add_etab"):
        nom = st.text_input("Nom")
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                try:
                    new_id = run_insert("INSERT INTO etablissements (nom) VALUES (%s)", (nom.strip(),))
                    audit("INSERT", "etablissements", new_id, "nom", None, nom.strip())
                    st.success("Établissement ajouté.")
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("Un établissement avec ce nom existe déjà.")
            else:
                st.error("Le nom est obligatoire.")

# ── Liste ─────────────────────────────────────────────────────────────────────
etabs = etablissements_list()

if not etabs:
    st.info("Aucun établissement enregistré.")
else:
    section_title(f"Liste — {len(etabs)} établissement(s)")
    for e in paginate(etabs, "etabs"):
        with st.expander(e["nom"]):
            c1, c2 = st.columns([4, 1])
            new_nom = c1.text_input("Nom", value=e["nom"], key=f"etab_nom_{e['id']}")
            c2.write("")
            c2.write("")
            if c2.button("Modifier", key=f"etab_upd_{e['id']}"):
                if new_nom.strip():
                    try:
                        run_update(
                            "UPDATE etablissements SET nom=%s WHERE id=%s",
                            (new_nom.strip(), e["id"]),
                        )
                        audit("UPDATE", "etablissements", e["id"], "nom", e["nom"], new_nom.strip())
                        st.success("Modifié.")
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("Ce nom est déjà utilisé.")
                else:
                    st.error("Le nom est obligatoire.")
            if st.button("Supprimer", key=f"etab_del_{e['id']}"):
                request_delete(
                    e["nom"],
                    "DELETE FROM etablissements WHERE id=%s",
                    (e["id"],),
                    "etablissements",
                    e["id"],
                )
