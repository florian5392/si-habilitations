# SI Habilitations

Outil open source de construction et de gestion des **matrices d'habilitations du Système d'Information**, par application, multi-établissements.

Il permet de modéliser, visualiser et exporter les droits accordés à chaque profil utilisateur sur chaque application métier, dans un contexte multi-sites.

> Conçu dans le cadre du programme **HospiConnect** (ANS — Agence du Numérique en Santé).

---

## Fonctionnalités

- Gestion des **établissements**, **applications**, **profils** et **droits** (CRUD complet avec confirmation avant suppression et pagination)
- **Contraintes d'intégrité** : unicité des noms, suppressions en cascade automatiques
- **Matrice interactive** (page dédiée) : `data_editor` Streamlit avec checkbox (booléen) et liste déroulante
- **Import** de matrice depuis Excel (`.xlsx`) ou CSV
- **Export Excel** (`.xlsx`) avec mise en forme couleur HospiConnect
- **Vue lecture / impression** navigateur (HTML + `window.print()`)
- **Duplication de profil** avec toutes ses habilitations
- **Journal d'audit** : traçabilité de chaque création, modification, suppression (qui, quand, avant, après)
- **Authentification** par login/mot de passe (configurable via `.env`)
- **Reconnexion BDD automatique** en cas de timeout MySQL
- Architecture **multipage Streamlit** (`pages/`) avec module partagé `utils/`
- Interface avec palette couleurs HospiConnect (Arial, corail, bleu nuit, turquoise)

---

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) ≥ 20
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2

---

## Déploiement

```bash
git clone <url-du-dépôt>
cd si-habilitations
docker-compose up --build
```

L'application est accessible sur [http://localhost:8501](http://localhost:8501).  
La base de données MySQL est exposée sur le port `3306`.

---

## Structure du projet

```
si-habilitations/
├── app.py                      # Page d'accueil (tableau de bord)
├── pages/
│   ├── 1_Etablissements.py     # CRUD établissements
│   ├── 2_Applications.py       # CRUD applications
│   ├── 3_Profils.py            # CRUD profils + duplication
│   ├── 4_Droits.py             # CRUD droits + valeurs liste
│   ├── 5_Matrice.py            # Matrice interactive, import, export, impression
│   └── 6_Historique.py         # Journal d'audit
├── utils/
│   ├── db.py                   # Connexion MySQL + helpers SQL + audit
│   ├── queries.py              # Requêtes métier
│   ├── export.py               # Génération du fichier Excel
│   └── ui.py                   # CSS, auth, sidebar, pagination, dialogues
├── init.sql                    # Schéma MySQL (exécuté au premier démarrage)
├── docker-compose.yml          # Orchestration des services (app + db)
├── Dockerfile                  # Image Docker de l'application
├── requirements.txt            # Dépendances Python
├── .env                        # Variables d'environnement (ne pas committer)
├── .env.example                # Modèle de configuration
└── README.md                   # Ce fichier
```

---

## Variables d'environnement

| Variable      | Valeur par défaut  | Description                  |
|---------------|--------------------|------------------------------|
| Variable        | Valeur par défaut  | Description                       |
|-----------------|--------------------|-----------------------------------|
| `DB_HOST`       | `db`               | Hôte MySQL                        |
| `DB_USER`       | `root`             | Utilisateur MySQL                 |
| `DB_PASSWORD`   | `root`             | Mot de passe MySQL                |
| `DB_NAME`       | `si_habilitations` | Nom de la base de données         |
| `AUTH_USERNAME` | `admin`            | Identifiant de connexion à l'app  |
| `AUTH_PASSWORD` | `admin`            | Mot de passe de connexion à l'app |

Copiez `.env.example` en `.env` et adaptez les valeurs avant le premier lancement.
Le fichier `.env` est dans `.gitignore` et ne doit pas être commité.

---

## Stack technique

| Composant   | Technologie                  |
|-------------|------------------------------|
| Frontend    | Streamlit                    |
| Backend     | Python 3.11                  |
| Base de données | MySQL 8.0               |
| Export      | openpyxl                     |
| Conteneurisation | Docker + Docker Compose |

---

## Licence

MIT — libre d'utilisation, de modification et de redistribution.
