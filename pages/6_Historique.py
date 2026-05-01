import streamlit as st
import pandas as pd

st.set_page_config(page_title="Historique", page_icon="📋", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header, section_title
from utils.db import run_query

apply_styles()
require_auth()
render_sidebar()
page_header("📋 Historique des modifications")

# ── Filtres ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
tables = ["— Toutes —", "etablissements", "applications", "profils", "droits", "valeurs_liste", "habilitations"]
actions = ["— Toutes —", "INSERT", "UPDATE", "DELETE"]

sel_table  = c1.selectbox("Table", tables)
sel_action = c2.selectbox("Action", actions)
limit      = c3.number_input("Nombre de lignes", min_value=10, max_value=500, value=100, step=10)

# ── Requête ───────────────────────────────────────────────────────────────────
where_parts = []
params      = []

if sel_table != "— Toutes —":
    where_parts.append("table_name = %s")
    params.append(sel_table)
if sel_action != "— Toutes —":
    where_parts.append("action = %s")
    params.append(sel_action)

where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
params.append(int(limit))

rows = run_query(
    f"SELECT created_at, utilisateur, action, table_name, record_id, champ, ancienne_valeur, nouvelle_valeur "
    f"FROM audit_log {where} ORDER BY created_at DESC LIMIT %s",
    params,
)

# ── Affichage ─────────────────────────────────────────────────────────────────
if not rows:
    st.info("Aucune entrée dans le journal.")
else:
    section_title(f"{len(rows)} entrée(s)")
    df = pd.DataFrame(rows)
    df.columns = ["Date/Heure", "Utilisateur", "Action", "Table", "ID", "Champ", "Ancienne valeur", "Nouvelle valeur"]
    df["Date/Heure"] = pd.to_datetime(df["Date/Heure"]).dt.strftime("%d/%m/%Y %H:%M:%S")

    # Coloriser la colonne Action
    def color_action(val):
        colors = {"INSERT": "background-color:#d4edda", "UPDATE": "background-color:#fff3cd", "DELETE": "background-color:#f8d7da"}
        return colors.get(val, "")

    st.dataframe(
        df.style.applymap(color_action, subset=["Action"]),
        use_container_width=True,
        hide_index=True,
    )

    # Export CSV du journal
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exporter le journal (.csv)",
        data=csv,
        file_name="audit_log.csv",
        mime="text/csv",
    )
