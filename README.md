# SI Habilitations

Outil open source de construction et de gestion des **matrices d'habilitations du Système d'Information**, par application, multi-établissements.

Il permet de modéliser, visualiser, comparer et exporter les droits accordés à chaque profil utilisateur sur chaque application métier, dans un contexte multi-sites.

> Conçu dans le cadre du programme **HospiConnect** (ANS — Agence du Numérique en Santé).

---

## Fonctionnalités

### Référentiels (CRUD complet)
- **Établissements** : gestion des sites / unités organisationnelles
- **Applications** : gestion des applications métier, rattachées à un établissement
- **Profils** : rôles utilisateurs par application (ex. Médecin, Infirmier, Admin)
- **Droits** : permissions par application, en mode booléen (oui/non) ou liste de valeurs
- Confirmation modale avant toute suppression · Pagination des listes · Contraintes d'unicité par contexte

### Matrice des habilitations
- **Édition interactive** : `st.data_editor` avec cases à cocher (booléen) et listes déroulantes
- **Import** depuis Excel (`.xlsx`) ou CSV — reconnaissance automatique des colonnes
- **Export Excel** (`.xlsx`) avec mise en forme palette HospiConnect
- **Vue lecture / impression** navigateur (HTML + `window.print()`)
- **Duplication de profil** : copie un profil avec toutes ses habilitations vers un nouveau nom

### Comparaison de profils *(page 7)*
- Sélecteur établissement → application → deux profils côte à côte
- Tableau droit par droit avec code couleur :
  - 🟦 **Identique** : même valeur pour les deux profils
  - 🟧 **Différent** : valeurs différentes mais toutes deux définies
  - 🟥 **Manquant** : droit présent pour l'un, absent pour l'autre
- Résumé en bas (3 compteurs) · Export Excel avec la même palette couleur

### Vue transversale par profil *(page 8)*
- Sélecteur établissement → profil (toutes applications confondues)
- Tableau unique regroupant toutes les habilitations du profil sur toutes les applications
- Alternance de couleur par groupe d'application pour faciliter la lecture
- Gère les profils homonymes sur plusieurs applications (affichés tous)
- Export Excel

### Tableau de bord de complétude *(page d'accueil)*
- 4 métriques globales : établissements · applications · profils · **taux de complétude global**
- Tableau de complétude par application avec filtre établissement :
  - Colonnes : Établissement, Application, Profils, Droits, Cellules renseignées, Cellules totales, % Complétude
  - Barre de progression colorée : 🔴 < 50 % · 🟠 50–80 % · 🟢 > 80 %
  - Tri par complétude croissante (matrices à compléter en premier)

### Traçabilité & sécurité
- **Journal d'audit** : chaque création, modification et suppression est enregistrée (qui, quand, avant/après), filtrable et exportable en CSV
- **Authentification** par login / mot de passe configurable via `.env`
- **Reconnexion BDD automatique** en cas de timeout MySQL (ping avec reconnect)

---

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) ≥ 20
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2

---

## Lancer l'application

### Première installation

```bash
# 1. Cloner le dépôt
git clone <url-du-dépôt>
cd si-habilitations

# 2. Créer le fichier de configuration
cp .env.example .env
# Éditer .env pour changer les mots de passe (recommandé)

# 3. Démarrer les conteneurs (construction de l'image + init BDD)
docker-compose up --build
```

L'application est accessible sur **http://localhost:8501**.  
La base de données MySQL est exposée sur le port **3306**.

### Démarrages suivants

```bash
docker-compose up
```

### Arrêter l'application

```bash
docker-compose down
```

### Réinitialiser la base de données

> ⚠️ Supprime toutes les données.

```bash
docker-compose down -v   # supprime le volume db_data
docker-compose up --build
```

### Identifiants par défaut

| Champ | Valeur |
|---|---|
| Identifiant | `admin` |
| Mot de passe | `changeme` |

Modifiables dans `.env` via `AUTH_USERNAME` et `AUTH_PASSWORD`.

---

## Structure du projet

```
si-habilitations/
├── app.py                        # Page d'accueil — tableau de bord & complétude
├── pages/
│   ├── 1_Etablissements.py       # CRUD établissements
│   ├── 2_Applications.py         # CRUD applications
│   ├── 3_Profils.py              # CRUD profils + duplication
│   ├── 4_Droits.py               # CRUD droits + valeurs de liste
│   ├── 5_Matrice.py              # Matrice interactive, import, export, impression
│   ├── 6_Historique.py           # Journal d'audit filtrable + export CSV
│   ├── 7_Comparaison.py          # Comparaison côte à côte de deux profils
│   └── 8_Vue_transversale.py     # Vision d'un profil sur toutes les applications
├── utils/
│   ├── db.py                     # Connexion MySQL · helpers SQL · audit
│   ├── queries.py                # Toutes les requêtes métier
│   ├── export.py                 # Génération Excel (matrice, comparaison, transversale)
│   └── ui.py                     # CSS · auth · sidebar · pagination · dialogues modaux
├── init.sql                      # Schéma MySQL (exécuté une seule fois au premier démarrage)
├── docker-compose.yml            # Orchestration des services app + db
├── Dockerfile                    # Image Docker de l'application Python
├── requirements.txt              # Dépendances Python
├── pyrightconfig.json            # Désactive Pylance (mysql-connector sans stubs de types)
├── .env                          # Variables d'environnement — NE PAS COMMITTER
├── .env.example                  # Modèle de configuration
└── README.md                     # Ce fichier
```

---

## Variables d'environnement

| Variable        | Valeur par défaut  | Description                       |
|-----------------|--------------------|-----------------------------------|
| `DB_HOST`       | `db`               | Hôte MySQL (nom du service Docker)|
| `DB_USER`       | `root`             | Utilisateur MySQL                 |
| `DB_PASSWORD`   | `changeme`         | Mot de passe MySQL                |
| `DB_NAME`       | `si_habilitations` | Nom de la base de données         |
| `AUTH_USERNAME` | `admin`            | Identifiant de connexion à l'app  |
| `AUTH_PASSWORD` | `changeme`         | Mot de passe de connexion à l'app |

Copiez `.env.example` en `.env` et adaptez les valeurs avant le premier lancement.  
Le fichier `.env` est dans `.gitignore` et ne doit **jamais** être commité.

---

## Stack technique

| Composant        | Technologie              |
|------------------|--------------------------|
| Interface        | Streamlit                |
| Backend          | Python 3.11              |
| Base de données  | MySQL 8.0                |
| Export           | openpyxl                 |
| Conteneurisation | Docker + Docker Compose  |

---

## Architecture Streamlit multipage

Streamlit détecte automatiquement les fichiers dans `pages/` et les affiche dans la sidebar selon leur préfixe numérique. Chaque page :

1. Appelle `st.set_page_config()` en première instruction
2. Importe et appelle `apply_styles()`, `require_auth()`, `render_sidebar()` depuis `utils/ui.py`
3. Accède à la base de données uniquement via les fonctions de `utils/queries.py`

Le module `utils/db.py` maintient une connexion MySQL unique partagée via `@st.cache_resource`, qui survit aux réexécutions du script (déclenchées à chaque interaction utilisateur) et se reconnecte automatiquement après un timeout.

---

## Licence

MIT — libre d'utilisation, de modification et de redistribution.
