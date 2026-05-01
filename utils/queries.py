from utils.db import run_query, run_insert, run_update, audit


def etablissements_list():
    return run_query("SELECT id, nom FROM etablissements ORDER BY nom")


def applications_list(id_etab=None):
    if id_etab:
        return run_query(
            "SELECT id, nom, editeur, domaine, id_etablissement FROM applications "
            "WHERE id_etablissement=%s ORDER BY nom",
            (id_etab,),
        )
    return run_query(
        "SELECT id, nom, editeur, domaine, id_etablissement FROM applications ORDER BY nom"
    )


def profils_list(id_app):
    return run_query(
        "SELECT id, nom, description FROM profils WHERE id_application=%s ORDER BY nom",
        (id_app,),
    )


def droits_list(id_app):
    return run_query(
        "SELECT id, nom, description, type_valeur FROM droits WHERE id_application=%s ORDER BY nom",
        (id_app,),
    )


def valeurs_list(id_droit):
    return run_query(
        "SELECT id, valeur, ordre FROM valeurs_liste WHERE id_droit=%s ORDER BY ordre",
        (id_droit,),
    )


def habilitation_get(id_profil, id_droit):
    rows = run_query(
        "SELECT id, valeur FROM habilitations WHERE id_profil=%s AND id_droit=%s",
        (id_profil, id_droit),
    )
    return rows[0] if rows else None


def habilitation_set(id_profil, id_droit, valeur, profil_nom="", droit_nom=""):
    existing = habilitation_get(id_profil, id_droit)
    old_val = existing["valeur"] if existing else None
    if old_val == valeur:
        return
    if existing:
        run_update(
            "UPDATE habilitations SET valeur=%s WHERE id=%s",
            (valeur, existing["id"]),
        )
        audit("UPDATE", "habilitations", existing["id"], f"{profil_nom}/{droit_nom}", old_val, valeur)
    else:
        new_id = run_insert(
            "INSERT INTO habilitations (id_profil, id_droit, valeur) VALUES (%s,%s,%s)",
            (id_profil, id_droit, valeur),
        )
        audit("INSERT", "habilitations", new_id, f"{profil_nom}/{droit_nom}", None, valeur)


def stats_globales():
    row = run_query("""
        SELECT
          (SELECT COUNT(*) FROM etablissements) AS nb_etab,
          (SELECT COUNT(*) FROM applications)   AS nb_app,
          (SELECT COUNT(*) FROM profils)        AS nb_profils,
          (SELECT COUNT(*) FROM droits)         AS nb_droits
    """)
    return row[0] if row else {}
