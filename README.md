# TaskManager API

API REST de gestion de tâches façon Trello/Jira simplifié — projet final du cours
*Conception d'API REST avec Flask* (Sujet C).

Un utilisateur crée des **workspaces**, y invite des membres, organise des **projets**
en **colonnes**, et déplace des **tâches** entre ces colonnes. L'accès à un
workspace est réservé à ses membres ; seul le `owner` d'un workspace peut gérer
ses membres.

Le backend suit une architecture en 4 couches (modèles, schémas, services, routes),
organisée en blueprints sous `/api/v1`. Les données sont persistées avec SQLAlchemy
et versionnées via Alembic, sur PostgreSQL aussi bien en local qu'en conteneur.
Marshmallow encadre chaque entrée et chaque sortie de l'API. Côté sécurité :
authentification JWT à deux jetons (accès + rafraîchissement), deux niveaux
d'habilitation par workspace (`owner`, `member`), une limite de tentatives sur la
connexion, CORS configuré et des en-têtes HTTP renforcés. La suite compte 32 tests
automatisés (couverture 91 %) et toutes les erreurs suivent un même format JSON.
La documentation interactive est générée par Flasgger et servie sur `/docs/` en
développement. Le déploiement se fait via Gunicorn dans un conteneur Docker,
piloté par un `docker-compose.yml` qui inclut PostgreSQL.

Les choix de conception (contrat HTTP, codes d'erreur, modèle de données) sont
justifiés dans [`contrat-api.md`](contrat-api.md).

---

## Règles métier

| Règle | Réponse |
|---|---|
| Seuls les membres d'un workspace voient ses projets/colonnes/tâches | `403 FORBIDDEN` |
| Un utilisateur n'est assignable à une tâche que s'il est membre du workspace | `409 NOT_WORKSPACE_MEMBER` |
| Un utilisateur déjà membre ne peut pas être ajouté une seconde fois | `409 ALREADY_MEMBER` |
| Le `owner` d'un workspace ne peut pas être retiré | `409 CANNOT_REMOVE_OWNER` |
| Une tâche ne peut être déplacée que vers une colonne du même projet | `409 INVALID_COLUMN_TARGET` |
| Toute route protégée sans jeton JWT valide | `401 UNAUTHORIZED` |

## Rôles

| Rôle | Portée | Peut |
|---|---|---|
| `owner` | par workspace (le créateur) | Renommer/supprimer le workspace, gérer les membres |
| `member` | par workspace | Voir et gérer les projets, colonnes et tâches du workspace |

---

## Installation 

```powershell
python -m venv venv
venv\Scripts\activate            # macOS/Linux : source venv/bin/activate
pip install -r requirements.txt
```

Copie `.env.example` en `.env` et renseigne tes propres valeurs :

```
SECRET_KEY=une_valeur_aleatoire
DATABASE_URL=postgresql+psycopg://postgres:TON_MOT_DE_PASSE@localhost:5432/taskmanager_db
JWT_SECRET_KEY=une_autre_valeur_aleatoire
```

Crée la base `taskmanager_db` dans PostgreSQL (pgAdmin ou `psql`), puis :

```powershell
set FLASK_APP=run.py
flask db upgrade
flask run
```

## Lancement avec Docker

```powershell
docker compose up
```

Démarre une base PostgreSQL dédiée (conteneur séparé de ta base locale), attend
qu'elle soit prête, applique les migrations, puis lance Gunicorn. API disponible
sur `http://127.0.0.1:5000`. Swagger est désactivé dans le conteneur (config
`prod`), conformément à la règle « `DEBUG=False` en production ».

## Documentation interactive

En mode développement (`flask run`) : `http://127.0.0.1:5000/docs/`

## Tests

```powershell
pytest -v
pytest --cov=app --cov-report=term-missing
```

Les tests utilisent une base SQLite en mémoire recréée à chaque test — aucune
configuration manuelle nécessaire, et `taskmanager_db` n'est jamais touchée.

---

## Endpoints

| Verbe HTTP | Chemin | Qui peut appeler | Code si ça réussit |
|---|---|---|---|
| GET | `/health/` | public | 200 / 503 |
| POST | `/api/v1/auth/register` | public | 201 |
| POST | `/api/v1/auth/login` | public (5/min) | 200 |
| POST | `/api/v1/auth/refresh` | refresh token | 200 |
| GET | `/api/v1/auth/me` | connecté | 200 |
| GET, POST | `/api/v1/workspaces` | connecté | 200 / 201 |
| GET, PATCH, DELETE | `/api/v1/workspaces/<id>` | membre / owner / owner | 200 / 200 / 204 |
| GET, POST | `/api/v1/workspaces/<id>/members` | membre / owner | 200 / 201 |
| DELETE | `/api/v1/workspaces/<id>/members/<user_id>` | owner | 204 |
| GET, POST | `/api/v1/workspaces/<id>/projects` | membre | 200 / 201 |
| GET, PATCH, DELETE | `/api/v1/projects/<id>` | membre | 200 / 200 / 204 |
| GET | `/api/v1/projects/<id>/tasks` | membre | 200 (paginé) |
| GET, POST | `/api/v1/projects/<id>/columns` | membre | 200 / 201 |
| PATCH, DELETE | `/api/v1/columns/<id>` | membre | 200 / 204 |
| GET, POST | `/api/v1/columns/<id>/tasks` | membre | 200 / 201 |
| GET, PATCH, DELETE | `/api/v1/tasks/<id>` | membre | 200 / 200 / 204 |

**Filtres, tri et pagination** sur `GET /api/v1/projects/<id>/tasks` :
```
?column_id=&assignee_id=&priority=&due_date=&sort=-priority&page=1&per_page=20
```
Réponse :
```json
{
  "data": [ {"id": 1, "title": "...", "priority": "high"} ],
  "meta": {"page": 1, "per_page": 20, "total": 47, "total_pages": 3}
}
```

**Erreurs** (format unique pour toute l'API) :
```json
{
  "error": {
    "code": "NOT_WORKSPACE_MEMBER",
    "message": "L'utilisateur assigné n'est pas membre de ce workspace.",
    "status": 409
  }
}
```

---

## Architecture

```
taskmanager-api/
├── app/
│   ├── __init__.py       fabrique create_app() : extensions, blueprints, Swagger
│   ├── config.py         configurations Dev / Test / Prod
│   ├── extensions.py     instances partagées (db, jwt, cors, limiter...)
│   ├── errors.py         format d'erreur JSON unique + handlers globaux
│   ├── models/           User, Workspace, WorkspaceMember, Project, Column, Task
│   ├── schemas/          validation et sérialisation Marshmallow
│   ├── services/         logique métier, indépendante de HTTP
│   └── routes/           blueprints /api/v1 (un fichier par ressource)
├── migrations/           historique Alembic
├── tests/                conftest.py (fixtures) + un fichier par ressource
├── Dockerfile, docker-compose.yml, .dockerignore, entrypoint.sh
├── requirements.txt, .env.example, run.py, pytest.ini
└── contrat-api.md        réponses aux questions de réflexion (étapes 0-1)
```

Une route valide l'entrée avec un schéma, appelle un service, renvoie le JSON avec
un code de statut explicite. Toute règle métier vit dans `app/services/`.

## Variables d'environnement

Voir [`.env.example`](.env.example).

| Variable | Rôle | Exemple |
|---|---|---|
| `SECRET_KEY` | clé secrète Flask | valeur aléatoire |
| `JWT_SECRET_KEY` | signature des jetons JWT | valeur aléatoire |
| `DATABASE_URL` | URL de connexion SQLAlchemy | `postgresql+psycopg://user:pass@host:5432/db` |
| `CORS_ORIGINS` | origines autorisées (CORS) | `*` en dev, domaine du frontend en prod |

## Parcours de démonstration

1. `POST /api/v1/auth/register` — créer un compte
2. `POST /api/v1/auth/login` — récupérer un `access_token`
3. `POST /api/v1/workspaces` — créer un workspace (devient `owner`)
4. `POST /api/v1/workspaces/<id>/members` — inviter un second utilisateur
5. `POST /api/v1/workspaces/<id>/projects` — créer un projet
6. `POST /api/v1/projects/<id>/columns` — créer les colonnes (ex: To Do, Done)
7. `POST /api/v1/columns/<id>/tasks` — créer une tâche, l'assigner
8. `PATCH /api/v1/tasks/<id>` avec `{"column_id": ...}` — déplacer la tâche
9. `GET /api/v1/projects/<id>/tasks?sort=-priority&page=1` — lister, triées et paginées