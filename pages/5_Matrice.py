import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io

st.set_page_config(page_title="Matrice", page_icon="📊", layout="wide")

from utils.ui import apply_styles, require_auth, render_sidebar, page_header
from utils.queries import (
    applications_list, profils_list, droits_list,
    valeurs_list, habilitation_get, habilitation_set,
)
from utils.export import build_xlsx

apply_styles()
require_auth()
selected_etab_id = render_sidebar()
page_header("📊 Matrice des habilitations")

# ── Sélection application ─────────────────────────────────────────────────────
apps = applications_list(selected_etab_id)
if not apps:
    st.info("Aucune application disponible.")
    st.stop()

app_opts        = {a["nom"]: a["id"] for a in apps}
selected_app    = st.selectbox("Application", list(app_opts.keys()), key="mat_app")
selected_app_id = app_opts[selected_app]

profils = profils_list(selected_app_id)
droits  = droits_list(selected_app_id)

if not profils:
    st.info("Aucun profil défini pour cette application.")
    st.stop()
if not droits:
    st.info("Aucun droit défini pour cette application.")
    st.stop()

# ── Caches ────────────────────────────────────────────────────────────────────
valeurs_cache: dict[int, list[str]] = {}
for d in droits:
    if d["type_valeur"] == "liste":
        valeurs_cache[d["id"]] = [v["valeur"] for v in valeurs_list(d["id"])]

hab_cache: dict[tuple, str | None] = {}
for p in profils:
    for d in droits:
        row = habilitation_get(p["id"], d["id"])
        hab_cache[(p["id"], d["id"])] = row["valeur"] if row else None

profil_map = {p["nom"]: p["id"] for p in profils}
droit_map  = {d["nom"]: d        for d in droits}

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_edit, tab_import, tab_lecture = st.tabs(["✏️ Édition", "📥 Import", "🖨️ Vue lecture"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB : ÉDITION
# ─────────────────────────────────────────────────────────────────────────────
with tab_edit:
    # Construire le DataFrame
    rows = {}
    for p in profils:
        row = {}
        for d in droits:
            val = hab_cache[(p["id"], d["id"])]
            if d["type_valeur"] == "booleen":
                row[d["nom"]] = (val == "1")
            else:
                row[d["nom"]] = val if val else "—"
        rows[p["nom"]] = row
    orig_df = pd.DataFrame(rows).T

    # Config colonnes
    col_cfg: dict = {}
    for d in droits:
        if d["type_valeur"] == "booleen":
            col_cfg[d["nom"]] = st.column_config.CheckboxColumn(d["nom"])
        else:
            opts = ["—"] + valeurs_cache.get(d["id"], [])
            col_cfg[d["nom"]] = st.column_config.SelectboxColumn(d["nom"], options=opts)

    st.data_editor(
        orig_df,
        column_config=col_cfg,
        use_container_width=True,
        num_rows="fixed",
        key="matrix_editor",
    )

    # Traiter les modifications
    editor_state = st.session_state.get("matrix_editor", {})
    edited_rows  = editor_state.get("edited_rows", {})
    if edited_rows:
        saved = 0
        for row_idx_str, col_changes in edited_rows.items():
            row_idx = int(row_idx_str)
            if row_idx >= len(orig_df):
                continue
            profil_nom = orig_df.index[row_idx]
            p_id = profil_map.get(profil_nom)
            if not p_id:
                continue
            for droit_nom, new_val in col_changes.items():
                d = droit_map.get(droit_nom)
                if not d:
                    continue
                if d["type_valeur"] == "booleen":
                    db_val = "1" if new_val else "0"
                else:
                    db_val = new_val if new_val and new_val != "—" else None
                habilitation_set(p_id, d["id"], db_val, profil_nom, droit_nom)
                saved += 1
        if saved:
            st.session_state["matrix_editor"]["edited_rows"] = {}
            st.toast(f"✅ {saved} modification(s) sauvegardée(s)", icon="✅")
            st.rerun()

    # Export Excel
    st.markdown("---")
    xlsx = build_xlsx(selected_app, profils, droits, valeurs_cache, hab_cache)
    st.download_button(
        "⬇️ Exporter en Excel (.xlsx)",
        data=xlsx,
        file_name=f"matrice_{selected_app.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB : IMPORT
# ─────────────────────────────────────────────────────────────────────────────
with tab_import:
    st.markdown("""
**Format attendu** (Excel `.xlsx` ou CSV `.csv`) :

| Profil | DroitA | DroitB | … |
|--------|--------|--------|---|
| Admin  | 1      | Lecture | … |
| User   | 0      | —      | … |

- Colonnes : `Profil` (obligatoire), puis un nom de droit par colonne.
- Booléen : `1` / `0` · `Oui` / `Non` · `True` / `False` · `x` / vide.
- Liste : valeur exacte ou vide / `—`.
- Les profils et droits non trouvés sont ignorés.
""")

    uploaded = st.file_uploader("Choisir un fichier", type=["xlsx", "csv"], key="mat_import")
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df_import = pd.read_csv(uploaded, dtype=str).fillna("")
            else:
                df_import = pd.read_excel(uploaded, dtype=str).fillna("")

            if "Profil" not in df_import.columns:
                st.error("Colonne « Profil » introuvable dans le fichier.")
            else:
                droit_cols = [c for c in df_import.columns if c != "Profil" and c in droit_map]
                ignored    = [c for c in df_import.columns if c != "Profil" and c not in droit_map]

                st.write(f"**Droits reconnus :** {', '.join(droit_cols) or '—'}")
                if ignored:
                    st.warning(f"Colonnes ignorées (droit inconnu) : {', '.join(ignored)}")

                if droit_cols:
                    st.dataframe(df_import[["Profil"] + droit_cols], use_container_width=True)

                    if st.button("✅ Importer", type="primary"):
                        _TRUTHY = {"1", "oui", "true", "yes", "x", "✓"}
                        count   = 0
                        errors  = []
                        for _, row in df_import.iterrows():
                            profil_nom = str(row["Profil"]).strip()
                            p_id = profil_map.get(profil_nom)
                            if not p_id:
                                errors.append(f"Profil « {profil_nom} » inconnu.")
                                continue
                            for droit_nom in droit_cols:
                                d    = droit_map[droit_nom]
                                raw  = str(row[droit_nom]).strip()
                                if d["type_valeur"] == "booleen":
                                    db_val = "1" if raw.lower() in _TRUTHY else "0"
                                else:
                                    db_val = raw if raw and raw != "—" else None
                                habilitation_set(p_id, d["id"], db_val, profil_nom, droit_nom)
                                count += 1
                        st.success(f"{count} habilitation(s) importée(s).")
                        if errors:
                            for e in errors[:5]:
                                st.warning(e)
                        st.rerun()
        except Exception as exc:
            st.error(f"Erreur lors de la lecture du fichier : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB : VUE LECTURE / IMPRESSION
# ─────────────────────────────────────────────────────────────────────────────
with tab_lecture:
    # Construire le HTML de la table
    th_style = "background:#37306E;color:#FFF5E9;padding:8px 12px;border:1px solid #ccc;font-family:Arial"
    td_prof  = "background:#042638;color:#FFF5E9;padding:6px 10px;border:1px solid #ccc;font-weight:bold;font-family:Arial"
    td_oui   = "background:#4CBFDC;color:#042638;padding:6px 10px;border:1px solid #ccc;text-align:center;font-family:Arial"
    td_non   = "background:#FFF5E9;color:#042638;padding:6px 10px;border:1px solid #ccc;text-align:center;font-family:Arial"

    header_cells = "".join(f"<th style='{th_style}'>{d['nom']}</th>" for d in droits)
    body_rows    = ""
    for p in profils:
        cells = f"<td style='{td_prof}'>{p['nom']}</td>"
        for d in droits:
            val = hab_cache[(p["id"], d["id"])]
            if d["type_valeur"] == "booleen":
                display = "Oui" if str(val) == "1" else "Non"
                style   = td_oui if str(val) == "1" else td_non
            else:
                display = val if val else "—"
                style   = td_oui if val else td_non
            cells += f"<td style='{style}'>{display}</td>"
        body_rows += f"<tr>{cells}</tr>"

    titre_style = (
        "background:#EA4D49;color:#FFF5E9;padding:10px 14px;"
        "font-family:Arial;font-size:1.1rem;font-weight:bold;"
        "border-bottom:2px solid #37306E"
    )

    html = f"""
<style>
  @media print {{
    body * {{ visibility: hidden !important; }}
    #mat-print, #mat-print * {{ visibility: visible !important; }}
    #mat-print {{ position: absolute; top: 0; left: 0; width: 100%; }}
    .no-print {{ display: none !important; }}
  }}
  .print-btn {{
    background:#EA4D49;color:#FFF5E9;border:none;padding:8px 18px;
    border-radius:4px;font-family:Arial;font-weight:bold;cursor:pointer;
    margin-bottom:12px;font-size:.95rem;
  }}
  .print-btn:hover {{ background:#37306E; }}
  #mat-print table {{ border-collapse:collapse; width:100%; }}
</style>
<button class="print-btn no-print" onclick="window.print()">🖨️ Imprimer</button>
<div id="mat-print">
  <div style="{titre_style}">
    Matrice des habilitations — {selected_app}
  </div>
  <table>
    <thead>
      <tr>
        <th style="{th_style}">Profil</th>
        {header_cells}
      </tr>
    </thead>
    <tbody>
      {body_rows}
    </tbody>
  </table>
</div>
"""
    height = max(300, 60 + len(profils) * 34 + 80)
    components.html(html, height=height, scrolling=True)
