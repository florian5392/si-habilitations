"""
utils/ui.py — Composants d'interface partagés entre toutes les pages.

Contient :
  - La palette de couleurs et le CSS global injecté dans Streamlit
  - Le système d'authentification (login / session state)
  - La sidebar commune (sélecteur établissement + déconnexion)
  - Les helpers de mise en page (page_header, section_title, paginate)
  - Les dialogues modaux réutilisables (suppression, duplication de profil)
"""

import os
import streamlit as st
from utils.db import run_update, audit
from utils.queries import etablissements_list


# ── Palette de couleurs HospiConnect ──────────────────────────────────────────
# Ces constantes sont aussi importées par les pages qui construisent du HTML inline.
CORAIL    = "#EA4D49"
BLEU      = "#37306E"
BLEU_NUIT = "#042638"
TURQUOISE = "#4CBFDC"
BEIGE     = "#FFF5E9"


# ── CSS global ────────────────────────────────────────────────────────────────
# Streamlit ne propose pas d'API native de thématisation complète ; le seul
# moyen de surcharger les styles est d'injecter du CSS via st.markdown avec
# unsafe_allow_html=True. Les sélecteurs ciblent les classes internes de
# Streamlit (préfixe "css") et les data-testid exposés dans le DOM.
CSS = f"""
<style>
    html, body, [class*="css"] {{ font-family: Arial, sans-serif; }}

    /* Sidebar : fond bleu nuit, texte beige */
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

    /* Titres principaux et de section */
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

    /* Cartes de métriques (page d'accueil) */
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

    /* Expanders et boutons */
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

    /* En-têtes de tableaux st.dataframe */
    thead tr th {{
        background-color: {BLEU} !important;
        color: {BEIGE} !important;
    }}

    .stAlert {{ border-radius: 4px; }}
</style>
"""

# Nombre d'éléments par page dans les listes paginées
PAGE_SIZE = 10


def apply_styles():
    """Injecte le CSS global HospiConnect dans la page courante."""
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str):
    """Affiche le titre principal de la page (h1 stylisé)."""
    st.markdown(f'<div class="main-title">{title}</div>', unsafe_allow_html=True)


def section_title(title: str):
    """Affiche un sous-titre de section (h2 stylisé)."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


# ── Authentification ──────────────────────────────────────────────────────────
# Identifiants lus depuis les variables d'environnement (fichier .env).
# En l'absence de variable, les valeurs par défaut sont "admin"/"admin".
_AUTH_USER = os.getenv("AUTH_USERNAME", "admin")
_AUTH_PASS = os.getenv("AUTH_PASSWORD", "admin")


def require_auth():
    """
    Bloque le rendu de la page si l'utilisateur n'est pas connecté.

    Vérifie la clé "authenticated" dans st.session_state (persistante entre
    les réexécutions Streamlit tant que l'onglet reste ouvert).
    st.stop() interrompt immédiatement l'exécution du script courant, ce qui
    empêche tout affichage de contenu protégé.
    """
    if not st.session_state.get("authenticated"):
        _show_login()
        st.stop()


def _show_login():
    """Affiche le formulaire de connexion centré dans la page."""
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
                    # On stocke l'état de connexion dans la session Streamlit.
                    # Ces clés sont lues par require_auth() et render_sidebar().
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"]  = username
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")


# ── Sidebar commune ───────────────────────────────────────────────────────────

def render_sidebar() -> int | None:
    """
    Affiche la sidebar partagée et retourne l'id de l'établissement sélectionné.

    La sidebar contient :
    - Le nom de l'utilisateur connecté
    - Un sélecteur d'établissement (filtre global utilisé par plusieurs pages)
    - Un bouton de déconnexion

    La valeur retournée (None si "— Tous —") est transmise aux requêtes pour
    filtrer les listes d'applications, de profils, etc.
    """
    with st.sidebar:
        st.markdown("## 🔐 SI Habilitations")
        user = st.session_state.get("current_user", "")
        st.markdown(
            f"<small style='color:{TURQUOISE}'>👤 {user}</small>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        etabs      = etablissements_list()
        etab_map   = {e["nom"]: e["id"] for e in etabs}
        etab_names = ["— Tous —"] + list(etab_map.keys())
        sel = st.selectbox(
            "Établissement",
            etab_names,
            key="sidebar_etab",  # clé stable : préserve la sélection entre pages
        )
        selected_etab_id = etab_map.get(sel)  # None si "— Tous —"

        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            # Réinitialisation de l'état de session pour forcer le formulaire de login
            st.session_state["authenticated"] = False
            st.session_state["current_user"]  = None
            st.rerun()

    return selected_etab_id


# ── Pagination ────────────────────────────────────────────────────────────────

def paginate(items: list, key: str) -> list:
    """
    Découpe une liste en pages de PAGE_SIZE éléments et affiche les contrôles
    de navigation. Retourne le sous-ensemble correspondant à la page courante.

    Paramètre key : identifiant unique pour stocker le numéro de page en session
    (chaque liste paginée doit avoir sa propre clé pour ne pas interférer).
    """
    n = len(items)
    if n <= PAGE_SIZE:
        return items  # pas de pagination nécessaire

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
# @st.dialog crée une modale native Streamlit (disponible depuis la v1.32).
# La logique est stockée dans session_state["_pending_delete"] pour survivre
# à la réexécution du script déclenchée par l'ouverture de la modale.

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
    """
    Déclenche la modale de confirmation avant d'exécuter une suppression.

    Le dict _pending_delete contient tout ce qu'il faut pour exécuter la
    suppression sans que la page appelante ait à re-passer ces informations
    lors de la réexécution du script.
    """
    st.session_state["_pending_delete"] = {
        "label": label, "sql": sql, "params": params,
        "table": table, "record_id": record_id,
    }
    _confirm_delete_dialog()


# ── Dialogue de duplication de profil ─────────────────────────────────────────

@st.dialog("Dupliquer le profil")
def _dup_profil_dialog():
    """
    Modale qui copie un profil et toutes ses habilitations sous un nouveau nom.

    La duplication est atomique : profil + toutes ses habilitations sont insérés
    avant de relancer la page. En cas de nom déjà pris (IntegrityError), on
    affiche l'erreur sans interrompre la session.
    """
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
                # Copie ligne à ligne des habilitations du profil source
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
    """Déclenche la modale de duplication pour le profil donné."""
    st.session_state["_dup_profil"] = profil
    _dup_profil_dialog()
