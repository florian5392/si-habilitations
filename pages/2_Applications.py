import streamlit as st

st.set_page_config(page_title="Applications", page_icon="📱", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header, section_title, paginate, request_delete
from utils.db import run_insert, run_update, audit
from utils.queries import etablissements_list, applications_list
import mysql.connector

apply_styles()
require_auth()
selected_etab_id = render_sidebar()
page_header("📱 Applications")

etabs = etablissements_list()
if not etabs:
    st.warning("Aucun établissement. Créez-en un d'abord.")
    st.stop()

etab_map      = {e["id"]: e["nom"] for e in etabs}
etab_opts     = {e["nom"]: e["id"] for e in etabs}
etab_keys     = list(etab_opts.keys())

# ── Ajout ─────────────────────────────────────────────────────────────────────
with st.expander("Ajouter une application", expanded=False):
    with st.form("add_app"):
        nom      = st.text_input("Nom")
        editeur  = st.text_input("Éditeur")
        domaine  = st.text_input("Domaine")
        etab_sel = st.selectbox("Établissement", etab_keys, key="add_app_etab")
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                try:
                    new_id = run_insert(
                        "INSERT INTO applications (nom, editeur, domaine, id_etablissement) VALUES (%s,%s,%s,%s)",
                        (nom.strip(), editeur.strip(), domaine.strip(), etab_opts[etab_sel]),
                    )
                    audit("INSERT", "applications", new_id, "nom", None, nom.strip())
                    st.success("Application ajoutée.")
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("Une application avec ce nom existe déjà pour cet établissement.")
            else:
                st.error("Le nom est obligatoire.")

# ── Liste ─────────────────────────────────────────────────────────────────────
apps = applications_list(selected_etab_id)

if not apps:
    st.info("Aucune application" + (" pour cet établissement." if selected_etab_id else "."))
else:
    section_title(f"Liste — {len(apps)} application(s)")
    for app in paginate(apps, "apps"):
        etab_nom = etab_map.get(app.get("id_etablissement"), "?")
        label    = app["nom"] if selected_etab_id else f"{app['nom']} — {etab_nom}"
        with st.expander(label):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            new_nom  = c1.text_input("Nom",        value=app["nom"]     or "", key=f"app_nom_{app['id']}")
            new_edit = c2.text_input("Éditeur",    value=app["editeur"] or "", key=f"app_edit_{app['id']}")
            new_dom  = c3.text_input("Domaine",    value=app["domaine"] or "", key=f"app_dom_{app['id']}")
            cur_etab = etab_map.get(app.get("id_etablissement"), etab_keys[0])
            cur_idx  = etab_keys.index(cur_etab) if cur_etab in etab_keys else 0
            new_etab = c4.selectbox("Établissement", etab_keys, index=cur_idx, key=f"app_etab_{app['id']}")

            col1, col2 = st.columns(2)
            if col1.button("Modifier", key=f"app_upd_{app['id']}"):
                if new_nom.strip():
                    try:
                        run_update(
                            "UPDATE applications SET nom=%s, editeur=%s, domaine=%s, id_etablissement=%s WHERE id=%s",
                            (new_nom.strip(), new_edit.strip(), new_dom.strip(), etab_opts[new_etab], app["id"]),
                        )
                        audit("UPDATE", "applications", app["id"], "nom", app["nom"], new_nom.strip())
                        st.success("Modifié.")
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("Ce nom est déjà utilisé pour cet établissement.")
                else:
                    st.error("Le nom est obligatoire.")
            if col2.button("Supprimer", key=f"app_del_{app['id']}"):
                request_delete(
                    app["nom"],
                    "DELETE FROM applications WHERE id=%s",
                    (app["id"],),
                    "applications",
                    app["id"],
                )
