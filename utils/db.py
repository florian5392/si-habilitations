"""
utils/db.py — Couche d'accès à la base de données.

Expose quatre primitives SQL (run_query, run_insert, run_update, audit)
et gère la connexion MySQL de façon transparente via le cache Streamlit.
"""

import os
import streamlit as st
import mysql.connector
from mysql.connector import Error as MySQLError

try:
    from dotenv import load_dotenv
    load_dotenv()  # charge .env en dev local ; ignoré si python-dotenv absent
except ImportError:
    pass


@st.cache_resource
def _create_conn():
    """
    Ouvre la connexion MySQL et la met en cache pour toute la durée de vie du serveur.

    @st.cache_resource est essentiel : Streamlit réexécute le script entier à
    chaque interaction utilisateur. Sans ce cache, une nouvelle connexion serait
    ouverte à chaque clic, épuisant rapidement le pool de connexions MySQL.

    autocommit=True est positionné pour les SELECT (pas de transaction implicite).
    Les mutations (INSERT/UPDATE/DELETE) appellent conn.commit() explicitement
    via run_insert / run_update.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "si_habilitations"),
        autocommit=True,
        connection_timeout=10,
    )


def get_conn():
    """
    Retourne la connexion mise en cache, en la rétablissant si elle a expiré.

    MySQL ferme automatiquement les connexions inactives après `wait_timeout`
    (8 h par défaut). Le ping avec reconnect=True rouvre la socket sans recréer
    l'objet Python, préservant ainsi le cache Streamlit.
    Si le ping échoue malgré 3 tentatives, on vide le cache et on recrée
    une connexion fraîche.
    """
    conn = _create_conn()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except MySQLError:
        # Connexion définitivement perdue : on force la recréation du cache.
        st.cache_resource.clear()
        conn = _create_conn()
    return conn


def run_query(sql, params=None):
    """
    Exécute un SELECT et retourne la liste des lignes sous forme de dicts.

    cursor(dictionary=True) : chaque ligne est un dict {nom_colonne: valeur},
    ce qui rend le code appelant indépendant de l'ordre des colonnes dans la
    requête SQL et améliore lisibilité (row["nom"] plutôt que row[0]).
    """
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    return cur.fetchall()


def run_insert(sql, params=None):
    """Exécute un INSERT et retourne l'id auto-incrémenté de la nouvelle ligne."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    return cur.lastrowid


def run_update(sql, params=None):
    """Exécute un UPDATE ou DELETE (sans valeur de retour significative)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()


def audit(action, table, record_id, champ=None, old_val=None, new_val=None):
    """
    Enregistre une entrée dans le journal d'audit (table audit_log).

    Appelée après chaque mutation métier. Le try/except est intentionnel :
    une erreur d'audit (ex. table manquante, connexion temporaire perdue) ne
    doit jamais bloquer l'opération qui vient de réussir.

    Paramètres :
        action    : "INSERT" | "UPDATE" | "DELETE"
        table     : nom de la table impactée
        record_id : id de la ligne créée / modifiée / supprimée
        champ     : nom du champ modifié (optionnel, utile pour les UPDATE)
        old_val   : valeur avant modification (None pour INSERT)
        new_val   : valeur après modification (None pour DELETE)
    """
    user = st.session_state.get("current_user", "system")
    try:
        run_insert(
            """INSERT INTO audit_log
               (utilisateur, action, table_name, record_id, champ, ancienne_valeur, nouvelle_valeur)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                user, action, table, record_id, champ,
                str(old_val) if old_val is not None else None,
                str(new_val) if new_val is not None else None,
            ),
        )
    except Exception:
        pass
