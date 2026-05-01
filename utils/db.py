import os
import streamlit as st
import mysql.connector
from mysql.connector import Error as MySQLError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@st.cache_resource
def _create_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "si_habilitations"),
        autocommit=True,
        connection_timeout=10,
    )


def get_conn():
    conn = _create_conn()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except MySQLError:
        st.cache_resource.clear()
        conn = _create_conn()
    return conn


def run_query(sql, params=None):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    return cur.fetchall()


def run_insert(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    return cur.lastrowid


def run_update(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()


def audit(action, table, record_id, champ=None, old_val=None, new_val=None):
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
