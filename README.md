# SI Habilitations

Outil open source de construction et de gestion des **matrices d'habilitations du Système d'Information**, par application, multi-établissements.

Il permet de modéliser, visualiser et exporter les droits accordés à chaque profil utilisateur sur chaque application métier, dans un contexte multi-sites.

> Conçu dans le cadre du programme **HospiConnect** (ANS — Agence du Numérique en Santé).

---

## Fonctionnalités

- Gestion des **établissements** (multi-sites)
- Gestion des **applications** (avec éditeur et domaine fonctionnel)
- Gestion des **profils** par application
- Gestion des **droits** par application (booléen ou liste de valeurs)
- **Matrice interactive** profils × droits : checkbox pour les booléens, liste déroulante pour les valeurs
- **Export Excel** (.xlsx) avec mise en forme couleur
- Interface responsive avec palette couleurs HospiConnect

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
├── app.py               # Application Streamlit principale
├── init.sql             # Schéma MySQL (créé au premier démarrage)
├── docker-compose.yml   # Orchestration des services (app + db)
├── Dockerfile           # Image Docker de l'application
├── requirements.txt     # Dépendances Python
└── README.md            # Ce fichier
```

---

## Variables d'environnement

| Variable      | Valeur par défaut  | Description                  |
|---------------|--------------------|------------------------------|
| `DB_HOST`     | `db`               | Hôte MySQL                   |
| `DB_USER`     | `root`             | Utilisateur MySQL            |
| `DB_PASSWORD` | `root`             | Mot de passe MySQL           |
| `DB_NAME`     | `si_habilitations` | Nom de la base de données    |

Ces variables peuvent être surchargées dans `docker-compose.yml` ou via un fichier `.env`.

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
