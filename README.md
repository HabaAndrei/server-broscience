# Broscience — Server

FastAPI backend for the **Broscience** fitness & nutrition app. It powers AI‑assisted food image analysis, personalised nutrition plan generation, and high‑speed food/recipe search.

> This repository is the API. The mobile client lives in [`expo-broscience`](../expo-broscience) and points at this server via `EXPO_PUBLIC_SERVER_ADDRESS`.

---

## Features

- **`POST /nutrition-plan`** — Generates a personalised daily nutrition plan (calories, protein, carbs, fat, health score) from the user's profile and goal using OpenAI structured outputs.
- **`POST /analyze-image`** — Accepts a base64 meal image and returns ingredients, per‑ingredient nutrients, totals, and a health score. Ingredient nutrient lookups run concurrently via a thread pool for low latency.
- **`GET /search-food`** — Fuzzy/typo‑tolerant search over a foods catalogue (FatSecret dataset, ~hundreds of thousands of items) backed by **Meilisearch**. Normalises serving units (oz → g) and validates macros before returning.
- **`GET /search-recipe`** — Filtered, paginated recipe search (filter by macro ranges, ingredients, etc.) backed by Meilisearch.
- **`GET /search-recipe/{recipe_id}`** — Fetch a single recipe by id.
- **Firebase Admin** integration for shared auth/Firestore with the mobile client.
- **Singleton clients** for OpenAI, Meilisearch, Firestore and FatSecret to keep cold‑start cheap.

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI + Uvicorn |
| Dependency mgmt | Pipenv (`Pipfile` / `Pipfile.lock`) |
| Search | Meilisearch |
| LLM | OpenAI (structured outputs, vision) |
| Auth / DB | Firebase Admin (Firestore) |
| Food data | FatSecret API + local JSONL catalogue |
| Container | Docker + docker‑compose |

---

## Project layout

```
.
├── main.py                  # FastAPI app + route handlers
├── config.py                # pydantic-settings, loads .env
├── generators/              # LLM-powered features
│   ├── fitness_guide.py     #   nutrition plan generation
│   └── food_analyzer.py     #   image -> ingredients + nutrients
├── services/                # search orchestration
│   ├── search_food_service.py
│   ├── search_recipe_service.py
│   └── meilisearch_query_service.py
├── providers/               # external clients (singletons)
│   ├── openai_client.py
│   ├── meilisearch_client.py
│   ├── firebase_client.py
│   ├── fatsecret_client.py
│   └── schemas.py           # Pydantic request/response models
├── food_details/            # local JSONL data
│   ├── foods.jsonl
│   ├── recipes.jsonl
│   └── general_details_recipes.jsonl
├── utils/                   # helpers (number coercion, goals)
├── Dockerfile
├── docker-compose.yml
├── Pipfile / Pipfile.lock
└── .env.example
```

---

## Prerequisites

- **Python 3.13** (see `Pipfile`)
- **Pipenv** — `pip install --user pipenv`
- **Docker** + **docker‑compose** (optional, for the containerised path)
- A running **Meilisearch** instance — local Docker is fine (see below)
- An **OpenAI** API key
- A **Firebase** project (service‑account JSON) — same project the mobile client uses
- Optional: **FatSecret** developer credentials (consumer key/secret)

---

## Quick start

### 1. Clone and configure env

```bash
git clone <your-repo-url> server-broscience
cd server-broscience
cp .env.example .env
```

Fill `.env`:

| Variable | What it is |
|---|---|
| `OPENAI_API_KEY` | OpenAI key (used by `gpt-4o-mini` for plan generation, image analysis, nutrient lookup) |
| `MEILISEARCH_URL` | e.g. `http://127.0.0.1:7700` |
| `MEILISEARCH_PASSWORD` | Master key configured for your Meilisearch instance |
| `GOOGLE_SERVICE_ACCOUNT_*` | All 11 fields from a Firebase service‑account JSON. Keep `\n` literals inside the private key — the code converts them at runtime. |
| `FATSECRET_CONSUMER_KEY` / `FATSECRET_CONSUMER_SECRET` | FatSecret OAuth credentials |

> **Tip — Firebase service account:** in the Firebase console, *Project settings → Service accounts → Generate new private key*. Map each top‑level JSON field to its `GOOGLE_SERVICE_ACCOUNT_*` counterpart in `.env`.

### 2. Start Meilisearch (local)

```bash
docker run -d --name meili \
  -p 7700:7700 \
  -e MEILI_MASTER_KEY="masterKeyChangeMe" \
  -v $(pwd)/.meili_data:/meili_data \
  getmeili/meilisearch:latest
```

Then set in `.env`:

```
MEILISEARCH_URL=http://127.0.0.1:7700
MEILISEARCH_PASSWORD=masterKeyChangeMe
```

### 3. Index the food + recipe data

The app reads from Meilisearch at request time, so you must seed indexes once from the bundled JSONL files in `food_details/`:

```bash
pipenv install
pipenv shell

python -c "from providers.meilisearch_client import Meilisearch; Meilisearch().store_foods()"
python -c "from providers.meilisearch_client import Meilisearch; Meilisearch().store_recipes()"
```

(Re‑running these will drop and recreate the indexes — safe.)

### 4. Run the API

**Option A — Pipenv (local dev, hot reload):**

```bash
pipenv install
pipenv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Option B — Docker Compose:**

```bash
docker compose up --build
```

The API is now on **http://127.0.0.1:8000**. Interactive docs at **http://127.0.0.1:8000/docs**.

---

## API reference

| Method | Path | Body / Query | Description |
|---|---|---|---|
| `GET`  | `/` | — | Health check |
| `POST` | `/nutrition-plan` | `NutritionRequest` (gender, workouts, height, weight, age, goal) | Daily plan: calories / protein / carbs / fat / healthScore |
| `POST` | `/analyze-image` | `AnalyzeImageRequest` (`image`: base64) | Ingredients + per‑ingredient and total macros + health score |
| `GET`  | `/search-food` | `?input=<query>` | Fuzzy food search, returns validated FatSecret items |
| `GET`  | `/search-recipe` | `?input=<query>&filter=<json>&pagination=<json>` | Recipe search with macro filters and pagination |
| `GET`  | `/search-recipe/{recipe_id}` | — | Single recipe by id |

All responses follow the shape `{ "is_resolved": bool, "data"?: ..., "err"?: ... }`.

See [`providers/schemas.py`](providers/schemas.py) for exact request/response models.

---

## Running with the mobile client

1. Start this server (`:8000`).
2. In the [`expo-broscience`](../expo-broscience) repo, set in its `.env`:
   ```
   EXPO_PUBLIC_SERVER_ADDRESS="http://<your-LAN-ip>:8000"
   ```
   Use your machine's LAN IP (e.g. `192.168.1.42`) when testing on a real device — `127.0.0.1` only works for the iOS simulator.
3. Run `npx expo start`.

Both projects must use the **same Firebase project** (the mobile client uses Firebase Auth/Firestore SDK; the server uses Firebase Admin against the same project).

---

## Development tips

- `CORS` is wide open by default in [`main.py`](main.py) — tighten `allow_origins` before shipping.
- The Meilisearch client and Firestore admin are singletons; importing them is cheap.
- `food_analyzer.get_ingredients_details` parallelises per‑ingredient nutrient lookups with a 10‑worker thread pool. If you hit OpenAI rate limits, drop the worker count.
- `model_structure_outputs` (default `gpt-4o-mini`) is configurable in [`config.py`](config.py).

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Failed to initialize Firestore Admin` | Missing or malformed `GOOGLE_SERVICE_ACCOUNT_*` vars. The private key needs `\n` escapes preserved. |
| Empty `/search-food` results | Indexes not seeded — run the `store_foods()` / `store_recipes()` snippets in step 3. |
| `meilisearch.errors.MeilisearchApiError` | Wrong `MEILISEARCH_PASSWORD` or URL. Check your container is up: `curl $MEILISEARCH_URL/health`. |
| OpenAI 429s on `/analyze-image` | Concurrent ingredient lookups; reduce the `ThreadPoolExecutor(10)` size in `food_analyzer.py`. |

---

## License

Private project — all rights reserved unless a license file is added.
