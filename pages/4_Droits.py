"""
pages/4_Droits.py — CRUD des droits et de leurs valeurs possibles.

Un droit est lié à une application. Il peut être de deux types :
  - "booleen" : la valeur est 0 ou 1 (case à cocher dans la matrice)
  - "liste"   : la valeur est choisie parmi une liste prédéfinie de valeurs
                (valeurs_liste), ex. Lecture / Écriture / Administration

Les valeurs de liste sont éditables inline (modification ou suppression
unitaire, ajout d'une nouvelle valeur).
"""

import streamlit as st
import mysql.connector

st.set_page_config(page_title="Droits", page_icon="🔑", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header, section_title, paginate, request_delete
from utils.db import run_insert, run_update, audit
from utils.queries import applications_list, droits_list, valeurs_list

apply_styles()
require_auth()
selected_etab_id = render_sidebar()
page_header("🔑 Droits")

apps = applications_list(selected_etab_id)
if not apps:
    st.info("Aucune application disponible. Créez-en une d'abord.")
    st.stop()

app_opts        = {a["nom"]: a["id"] for a in apps}
selected_app    = st.selectbox("Application", list(app_opts.keys()), key="droits_app")
selected_app_id = app_opts[selected_app]

# ── Ajout ─────────────────────────────────────────────────────────────────────
with st.expander("Ajouter un droit", expanded=False):
    with st.form("add_droit"):
        nom       = st.text_input("Nom du droit")
        desc      = st.text_area("Description")
        type_val  = st.selectbox("Type de valeur", ["booleen", "liste"])
        val_input = st.text_input(
            "Valeurs possibles (séparées par des virgules)",
            help="Uniquement pour le type « liste » — ex : Lecture,Écriture,Admin",
        )
        if st.form_submit_button("Ajouter"):
            if nom.strip():
                try:
                    droit_id = run_insert(
                        "INSERT INTO droits (id_application, nom, description, type_valeur) VALUES (%s,%s,%s,%s)",
                        (selected_app_id, nom.strip(), desc.strip(), type_val),
                    )
                    audit("INSERT", "droits", droit_id, "nom", None, nom.strip())
                    # On insère les valeurs de liste dès la création du droit,
                    # en respectant l'ordre de saisie (champ "ordre").
                    if type_val == "liste" and val_input.strip():
                        for i, v in enumerate(val_input.split(",")):
                            v = v.strip()
                            if v:
                                run_insert(
                                    "INSERT INTO valeurs_liste (id_droit, valeur, ordre) VALUES (%s,%s,%s)",
                                    (droit_id, v, i),
                                )
                    st.success("Droit ajouté.")
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("Un droit avec ce nom existe déjà pour cette application.")
            else:
                st.error("Le nom est obligatoire.")

# ── Liste ─────────────────────────────────────────────────────────────────────
droits = droits_list(selected_app_id)

if not droits:
    st.info("Aucun droit pour cette application.")
else:
    section_title(f"Liste — {len(droits)} droit(s)")
    for d in paginate(droits, f"droits_{selected_app_id}"):
        badge = "🔘 Booléen" if d["type_valeur"] == "booleen" else "📋 Liste"
        with st.expander(f"{d['nom']}  {badge}"):
            new_nom  = st.text_input("Nom",         value=d["nom"],              key=f"droit_nom_{d['id']}")
            new_desc = st.text_area("Description",  value=d["description"] or "", key=f"droit_desc_{d['id']}")
            new_type = st.selectbox(
                "Type", ["booleen", "liste"],
                index=0 if d["type_valeur"] == "booleen" else 1,
                key=f"droit_type_{d['id']}",
            )

            # ── Gestion des valeurs de liste ───────────────────────────────────
            if d["type_valeur"] == "liste":
                st.markdown("**Valeurs de la liste**")
                vals = valeurs_list(d["id"])
                for v in vals:
                    vc1, vc2 = st.columns([5, 1])
                    new_v = vc1.text_input("", value=v["valeur"], key=f"val_{v['id']}", label_visibility="collapsed")
                    if vc2.button("✕", key=f"val_del_{v['id']}"):
                        run_update("DELETE FROM valeurs_liste WHERE id=%s", (v["id"],))
                        audit("DELETE", "valeurs_liste", v["id"])
                        st.rerun()
                    # La modification est détectée inline (sans bouton dédié) :
                    # si la valeur a changé, on sauvegarde immédiatement.
                    if new_v != v["valeur"] and new_v.strip():
                        run_update("UPDATE valeurs_liste SET valeur=%s WHERE id=%s", (new_v.strip(), v["id"]))
                        audit("UPDATE", "valeurs_liste", v["id"], "valeur", v["valeur"], new_v.strip())

                # Formulaire d'ajout d'une nouvelle valeur à la liste existante
                c_add1, c_add2 = st.columns([5, 1])
                new_v_input = c_add1.text_input("Nouvelle valeur", key=f"droit_newval_{d['id']}")
                c_add2.write("")
                c_add2.write("")
                if c_add2.button("＋", key=f"droit_addval_{d['id']}"):
                    if new_v_input.strip():
                        try:
                            run_insert(
                                "INSERT INTO valeurs_liste (id_droit, valeur, ordre) VALUES (%s,%s,%s)",
                                (d["id"], new_v_input.strip(), len(vals)),
                            )
                            st.rerun()
                        except mysql.connector.IntegrityError:
                            st.error("Cette valeur existe déjà.")

            # ── Modification / suppression du droit ───────────────────────────
            c1, c2 = st.columns(2)
            if c1.button("Modifier", key=f"droit_upd_{d['id']}"):
                if new_nom.strip():
                    try:
                        run_update(
                            "UPDATE droits SET nom=%s, description=%s, type_valeur=%s WHERE id=%s",
                            (new_nom.strip(), new_desc.strip(), new_type, d["id"]),
                        )
                        audit("UPDATE", "droits", d["id"], "nom", d["nom"], new_nom.strip())
                        st.success("Modifié.")
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("Ce nom est déjà utilisé pour cette application.")
                else:
                    st.error("Le nom est obligatoire.")
            if c2.button("Supprimer", key=f"droit_del_{d['id']}"):
                request_delete(
                    d["nom"],
                    "DELETE FROM droits WHERE id=%s",
                    (d["id"],),
                    "droits",
                    d["id"],
                )
