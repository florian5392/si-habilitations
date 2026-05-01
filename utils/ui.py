import os
import streamlit as st
from utils.db import run_update, audit
from utils.queries import etablissements_list

# ── Palette ───────────────────────────────────────────────────────────────────
CORAIL      = "#EA4D49"
BLEU        = "#37306E"
BLEU_NUIT   = "#042638"
TURQUOISE   = "#4CBFDC"
BEIGE       = "#FFF5E9"

CSS = f"""
<style>
    html, body, [class*="css"] {{ font-family: Arial, sans-serif; }}

    section[data-testid="stSidebar"] {{
        background-color: {BLEU_NUIT};
    }}
    section[data-testid="stSidebar"] * {{
        color: {BEIGE} !important;
    }}
    section[data-testid="stSidebar"] label {{
        color: {TURQUOISE} !important;
        font-weight: bold;
    }}

    .main-title {{
        color: {BLEU};
        font-size: 2rem;
        font-weight: bold;
        border-bottom: 3px solid {CORAIL};
        padding-bottom: .4rem;
        margin-bottom: 1.5rem;
    }}
    .section-title {{
        color: {BLEU};
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 1rem;
    }}
    .metric-card {{
        background: {BEIGE};
        border-left: 4px solid {CORAIL};
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-bottom: .5rem;
    }}
    .metric-card .value {{
        font-size: 2rem;
        font-weight: bold;
        color: {BLEU};
    }}
    .metric-card .label {{
        color: #666;
        font-size: .9rem;
    }}
    .stExpander {{ border: 1px solid {TURQUOISE}; border-radius: 6px; }}
    .stButton > button {{
        background-color: {CORAIL};
        color: {BEIGE};
        border: none;
        border-radius: 4px;
        font-family: Arial, sans-serif;
        font-weight: bold;
    }}
    .stButton > button:hover {{
        background-color: {BLEU};
        color: {BEIGE};
    }}
    thead tr th {{
        background-color: {BLEU} !important;
        color: {BEIGE} !important;
    }}
    .stAlert {{ border-radius: 4px; }}
</style>
"""

PAGE_SIZE = 10


def apply_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str):
    st.markdown(f'<div class="main-title">{title}</div>', unsafe_allow_html=True)


def section_title(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


# ── Authentification ──────────────────────────────────────────────────────────
_AUTH_USER = os.getenv("AUTH_USERNAME", "admin")
_AUTH_PASS = os.getenv("AUTH_PASSWORD", "admin")


def require_auth():
    if not st.session_state.get("authenticated"):
        _show_login()
        st.stop()


def _show_login():
    apply_styles()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-title">🔐 SI Habilitations</div>', unsafe_allow_html=True)
        st.markdown("##### Connexion")
        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", use_container_width=True):
                if username == _AUTH_USER and password == _AUTH_PASS:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"]  = username
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar() -> int | None:
    """Renders shared sidebar content and returns selected_etab_id (or None)."""
    with st.sidebar:
        st.markdown("## 🔐 SI Habilitations")
        user = st.session_state.get("current_user", "")
        st.markdown(
            f"<small style='color:{TURQUOISE}'>👤 {user}</small>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        etabs = etablissements_list()
        etab_map  = {e["nom"]: e["id"] for e in etabs}
        etab_names = ["— Tous —"] + list(etab_map.keys())
        sel = st.selectbox(
            "Établissement",
            etab_names,
            key="sidebar_etab",
        )
        selected_etab_id = etab_map.get(sel)

        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["current_user"]  = None
            st.rerun()

    return selected_etab_id


# ── Pagination ────────────────────────────────────────────────────────────────
def paginate(items: list, key: str) -> list:
    n = len(items)
    if n <= PAGE_SIZE:
        return items
    total_pages = (n + PAGE_SIZE - 1) // PAGE_SIZE
    pkey = f"_page_{key}"
    if pkey not in st.session_state:
        st.session_state[pkey] = 1
    page = st.session_state[pkey]

    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("◀", key=f"_prev_{key}", disabled=(page <= 1)):
        st.session_state[pkey] -= 1
        st.rerun()
    c2.markdown(
        f"<p style='text-align:center;color:{BLEU};font-weight:bold;margin:0;padding:6px 0'>"
        f"Page {page} / {total_pages} &nbsp;·&nbsp; {n} éléments</p>",
        unsafe_allow_html=True,
    )
    if c3.button("▶", key=f"_next_{key}", disabled=(page >= total_pages)):
        st.session_state[pkey] += 1
        st.rerun()

    start = (page - 1) * PAGE_SIZE
    return items[start : start + PAGE_SIZE]


# ── Dialogue de confirmation de suppression ───────────────────────────────────
@st.dialog("Confirmer la suppression")
def _confirm_delete_dialog():
    action = st.session_state.get("_pending_delete")
    if not action:
        st.rerun()
        return
    st.warning(f"Supprimer **{action['label']}** ?")
    st.caption("Cette action est irréversible. Les enregistrements associés seront également supprimés.")
    c1, c2 = st.columns(2)
    if c1.button("Confirmer", type="primary", use_container_width=True):
        run_update(action["sql"], action["params"])
        audit("DELETE", action["table"], action["record_id"])
        st.session_state.pop("_pending_delete", None)
        st.rerun()
    if c2.button("Annuler", use_container_width=True):
        st.session_state.pop("_pending_delete", None)
        st.rerun()


def request_delete(label: str, sql: str, params: tuple, table: str, record_id: int):
    st.session_state["_pending_delete"] = {
        "label": label, "sql": sql, "params": params,
        "table": table, "record_id": record_id,
    }
    _confirm_delete_dialog()


# ── Dialogue de duplication de profil ─────────────────────────────────────────
@st.dialog("Dupliquer le profil")
def _dup_profil_dialog():
    from utils.db import run_insert as _insert
    src = st.session_state.get("_dup_profil")
    if not src:
        st.rerun()
        return
    st.info(f"Copier **{src['nom']}** avec toutes ses habilitations.")
    new_nom = st.text_input("Nom du nouveau profil", value=f"{src['nom']} (copie)")
    if st.button("Créer la copie", type="primary", use_container_width=True):
        if new_nom.strip():
            try:
                import mysql.connector
                new_id = _insert(
                    "INSERT INTO profils (id_application, nom, description) VALUES (%s,%s,%s)",
                    (src["id_application"], new_nom.strip(), src.get("description", "")),
                )
                from utils.db import run_query as _q
                habs = _q(
                    "SELECT id_droit, valeur FROM habilitations WHERE id_profil=%s",
                    (src["id"],),
                )
                for h in habs:
                    _insert(
                        "INSERT INTO habilitations (id_profil, id_droit, valeur) VALUES (%s,%s,%s)",
                        (new_id, h["id_droit"], h["valeur"]),
                    )
                audit("INSERT", "profils", new_id, "duplication", None, f"copie de #{src['id']}")
                st.session_state.pop("_dup_profil", None)
                st.success(f"Profil « {new_nom} » créé avec {len(habs)} habilitations.")
                st.rerun()
            except mysql.connector.IntegrityError:
                st.error("Ce nom existe déjà pour cette application.")
        else:
            st.error("Le nom est obligatoire.")
    if st.button("Annuler", use_container_width=True):
        st.session_state.pop("_dup_profil", None)
        st.rerun()


def request_dup_profil(profil: dict):
    st.session_state["_dup_profil"] = profil
    _dup_profil_dialog()
