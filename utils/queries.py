"""
utils/queries.py — Requêtes métier de l'application.

Toutes les fonctions appellent run_query / run_insert / run_update depuis db.py
et retournent des listes de dicts (ou un dict unique pour les fonctions *_get).
Aucune logique d'affichage ici : ce module est purement orienté données.
"""

from utils.db import run_query, run_insert, run_update, audit


# ── Référentiels de base ───────────────────────────────────────────────────────

def etablissements_list():
    """Retourne tous les établissements triés par nom."""
    return run_query("SELECT id, nom FROM etablissements ORDER BY nom")


def applications_list(id_etab=None):
    """
    Retourne les applications, filtrées par établissement si id_etab est fourni.
    Sans filtre, retourne toutes les applications de tous les établissements.
    """
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
    """Retourne les profils d'une application, triés par nom."""
    return run_query(
        "SELECT id, nom, description FROM profils WHERE id_application=%s ORDER BY nom",
        (id_app,),
    )


def droits_list(id_app):
    """Retourne les droits d'une application avec leur type (booleen ou liste)."""
    return run_query(
        "SELECT id, nom, description, type_valeur FROM droits WHERE id_application=%s ORDER BY nom",
        (id_app,),
    )


def valeurs_list(id_droit):
    """Retourne les valeurs possibles d'un droit de type liste, triées par ordre."""
    return run_query(
        "SELECT id, valeur, ordre FROM valeurs_liste WHERE id_droit=%s ORDER BY ordre",
        (id_droit,),
    )


# ── Habilitations (matrice) ────────────────────────────────────────────────────

def habilitation_get(id_profil, id_droit):
    """
    Retourne l'habilitation d'un profil pour un droit donné, ou None si absente.
    Utilisée pour lire une cellule individuelle de la matrice.
    """
    rows = run_query(
        "SELECT id, valeur FROM habilitations WHERE id_profil=%s AND id_droit=%s",
        (id_profil, id_droit),
    )
    return rows[0] if rows else None


def habilitation_set(id_profil, id_droit, valeur, profil_nom="", droit_nom=""):
    """
    Crée ou met à jour une habilitation (upsert manuel).

    Compare la nouvelle valeur à l'existante pour éviter les écritures inutiles
    et les entrées d'audit redondantes. Si la valeur est identique, on ne touche
    à rien (optimisation importante lors des imports massifs).
    """
    existing = habilitation_get(id_profil, id_droit)
    old_val = existing["valeur"] if existing else None
    if old_val == valeur:
        return  # aucun changement réel, on évite une écriture et un audit inutiles
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


# ── Statistiques globales (tableau de bord) ────────────────────────────────────

def stats_globales():
    """
    Retourne un dict de métriques globales pour la page d'accueil.

    Le taux de complétude est calculé en deux requêtes séparées pour des raisons
    de lisibilité : la première charge les comptages simples, la seconde agrège
    les données de complétude via une sous-requête par application.
    """
    row = run_query("""
        SELECT
          (SELECT COUNT(*) FROM etablissements) AS nb_etab,
          (SELECT COUNT(*) FROM applications)   AS nb_app,
          (SELECT COUNT(*) FROM profils)        AS nb_profils,
          (SELECT COUNT(*) FROM droits)         AS nb_droits
    """)
    stats = row[0] if row else {}

    # Calcul du taux global : somme des cellules renseignées / somme des cellules théoriques
    # Une cellule théorique = 1 intersection profil × droit pour une application donnée.
    comp = run_query("""
        SELECT
          SUM(nb_p * nb_d) AS cellules_totales,
          SUM(nb_rens)     AS cellules_renseignees
        FROM (
          SELECT
            (SELECT COUNT(*) FROM profils WHERE id_application = a.id) AS nb_p,
            (SELECT COUNT(*) FROM droits  WHERE id_application = a.id) AS nb_d,
            (SELECT COUNT(*) FROM habilitations h
              JOIN profils p ON h.id_profil = p.id
              WHERE p.id_application = a.id
                AND h.valeur IS NOT NULL AND h.valeur != '') AS nb_rens
          FROM applications a
        ) sub
    """)
    if comp and comp[0]["cellules_totales"]:
        stats["taux_completude"] = round(
            100.0 * (comp[0]["cellules_renseignees"] or 0) / comp[0]["cellules_totales"],
            1,
        )
    else:
        stats["taux_completude"] = 0.0

    return stats


# ── Comparaison de profils ─────────────────────────────────────────────────────

def get_profils_by_etablissement(id_etablissement):
    """
    Retourne les noms de profils distincts présents sur un établissement,
    toutes applications confondues.

    DISTINCT sur p.nom : un profil "Administrateur" peut exister sur plusieurs
    applications du même établissement. On retourne le nom une seule fois pour
    alimenter le sélecteur de la vue transversale.
    """
    return run_query(
        """SELECT DISTINCT p.nom
           FROM profils p
           JOIN applications a ON p.id_application = a.id
           WHERE a.id_etablissement = %s
           ORDER BY p.nom""",
        (id_etablissement,),
    )


def get_habilitations_comparaison(id_profil_1, id_profil_2, id_application):
    """
    Retourne, pour chaque droit de l'application, la valeur des deux profils.

    Le double LEFT JOIN garantit que tous les droits apparaissent dans le
    résultat, même si l'un des profils n'a aucune habilitation définie pour
    ce droit (valeur NULL dans ce cas, matérialisée comme "absent").
    """
    return run_query(
        """SELECT
             d.id          AS id_droit,
             d.nom         AS droit_nom,
             d.type_valeur,
             h1.valeur     AS valeur_1,
             h2.valeur     AS valeur_2
           FROM droits d
           LEFT JOIN habilitations h1 ON h1.id_droit = d.id AND h1.id_profil = %s
           LEFT JOIN habilitations h2 ON h2.id_droit = d.id AND h2.id_profil = %s
           WHERE d.id_application = %s
           ORDER BY d.nom""",
        (id_profil_1, id_profil_2, id_application),
    )


def get_habilitations_transversales(nom_profil, id_etablissement):
    """
    Retourne toutes les habilitations d'un profil (par nom) sur toutes les
    applications d'un établissement, groupées par application.

    La jointure sur p.nom (et non p.id) permet de récupérer plusieurs profils
    homonymes sur des applications différentes — cas réel où un même rôle
    "Administrateur" existe dans plusieurs logiciels du même établissement.
    """
    return run_query(
        """SELECT
             a.id   AS id_app,
             a.nom  AS app_nom,
             d.nom  AS droit_nom,
             d.type_valeur,
             h.valeur
           FROM profils p
           JOIN applications a ON p.id_application = a.id
           JOIN droits d ON d.id_application = a.id
           LEFT JOIN habilitations h ON h.id_profil = p.id AND h.id_droit = d.id
           WHERE p.nom = %s AND a.id_etablissement = %s
           ORDER BY a.nom, d.nom""",
        (nom_profil, id_etablissement),
    )


def get_completude_par_application(id_etablissement=None):
    """
    Retourne le taux de complétude pour chaque application.

    Cellules totales  = nb_profils × nb_droits de l'application.
    Cellules renseignées = habilitations avec valeur non NULL et non vide.

    Le filtre établissement est optionnel (None = tous les établissements).
    Le tri est effectué côté Python (voir app.py) car les alias de colonnes
    calculées par sous-requêtes MySQL peuvent poser des ambiguïtés de types
    selon la version du connecteur.
    """
    where = "WHERE a.id_etablissement = %s" if id_etablissement else ""
    params = (id_etablissement,) if id_etablissement else ()
    return run_query(
        f"""SELECT
              e.nom  AS etab_nom,
              a.id   AS id_app,
              a.nom  AS app_nom,
              (SELECT COUNT(*) FROM profils WHERE id_application = a.id) AS nb_profils,
              (SELECT COUNT(*) FROM droits  WHERE id_application = a.id) AS nb_droits,
              (SELECT COUNT(*) FROM profils WHERE id_application = a.id) *
              (SELECT COUNT(*) FROM droits  WHERE id_application = a.id) AS cellules_totales,
              (SELECT COUNT(*) FROM habilitations h
                JOIN profils p ON h.id_profil = p.id
                WHERE p.id_application = a.id
                  AND h.valeur IS NOT NULL AND h.valeur != '') AS cellules_renseignees
            FROM applications a
            JOIN etablissements e ON a.id_etablissement = e.id
            {where}""",
        params,
    )
