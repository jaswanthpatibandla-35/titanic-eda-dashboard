# 🚢 Titanic EDA — Production-Ready Exploratory Data Analysis

A fully modular, deployment-ready EDA project built around the **Titanic dataset**.  
Ships with a **FastAPI** backend, **11 publication-quality visualisations**, an interactive HTML dashboard, Docker support, and a clean JSON API.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Data Dictionary](#data-dictionary)
4. [Quick Start (Local)](#quick-start-local)
5. [API Reference](#api-reference)
6. [Docker Deployment](#docker-deployment)
7. [Cloud Deployment](#cloud-deployment)
8. [EDA Highlights](#eda-highlights)
9. [Code Quality](#code-quality)
10. [Contributing](#contributing)

---

## Project Overview

| Item | Detail |
|---|---|
| **Dataset** | Titanic passenger manifest — 891 rows × 12 columns |
| **Framework** | FastAPI + Uvicorn / Gunicorn |
| **Analysis libs** | Pandas, NumPy, SciPy |
| **Visualisation** | Matplotlib, Seaborn (11 charts) |
| **Python** | 3.11+ |
| **Containerisation** | Docker + Docker Compose |
| **Deployment targets** | AWS EC2/ECS, Heroku, Render, Railway |

---

## Project Structure

```
titanic_eda/
├── app.py                  # FastAPI application & route definitions
├── main.py                 # CLI entry point (batch EDA without web server)
├── config.py               # Centralised configuration (all paths & constants)
├── gunicorn.conf.py        # Production Gunicorn settings
├── requirements.txt        # Pinned dependencies
├── Dockerfile              # Multi-stage production Docker image
├── docker-compose.yml      # Orchestration (app + optional nginx)
├── .env.example            # Environment variable template
├── .dockerignore
│
├── data/                   # Raw dataset (auto-downloaded on first run)
│   └── titanic_raw.csv
│
├── src/                    # Core Python modules
│   ├── __init__.py
│   ├── data_loader.py      # Load, validate, and optimise dataset
│   ├── eda_analysis.py     # Statistical analysis functions
│   ├── visualizations.py   # All chart generation (11 charts)
│   └── utils.py            # Logging, caching, helpers
│
├── templates/
│   └── dashboard.html      # Interactive web dashboard
│
├── static/                 # CSS / JS assets (served at /static)
│
├── notebooks/
│   └── titanic_eda.ipynb   # Jupyter walkthrough (generate with main.py)
│
└── output/
    ├── charts/             # Generated PNG visualisations
    ├── reports/            # JSON quality report
    └── cleaned_data/       # Processed CSV exports
```

---

## Data Dictionary

| Column | Type | Description |
|---|---|---|
| `PassengerId` | int | Unique passenger identifier (1-indexed) |
| `Survived` | int | Target: 0 = did not survive, 1 = survived |
| `Pclass` | int | Ticket class: 1 = 1st, 2 = 2nd, 3 = 3rd |
| `Name` | str | Full name (includes title, maiden name) |
| `Sex` | str | Passenger sex: `male` / `female` |
| `Age` | float | Age in years; fractional if < 1; `.5` if estimated |
| `SibSp` | int | # siblings / spouses aboard |
| `Parch` | int | # parents / children aboard |
| `Ticket` | str | Alphanumeric ticket number |
| `Fare` | float | Fare paid in British pounds (£) |
| `Cabin` | str | Cabin number — first letter encodes deck |
| `Embarked` | str | Port: `C` = Cherbourg, `Q` = Queenstown, `S` = Southampton |

**Engineered features** (computed in `eda_analysis.engineer_features`):

| Column | Description |
|---|---|
| `FamilySize` | `SibSp + Parch + 1` |
| `IsAlone` | 1 if travelling solo |
| `Title` | Extracted from Name (Mr, Mrs, Miss, Master, Rare) |
| `Deck` | First letter of Cabin; `U` = unknown |
| `FareBand` | Quartile-binned fare (Q1–Q4) |

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- `pip` or `conda`

### 1 — Clone & set up environment

```bash
git clone https://github.com/youruser/titanic-eda.git
cd titanic-eda

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2 — Configure environment variables

```bash
cp .env.example .env
# Edit .env if needed — defaults work for local development
```

### 3a — Run the web server

```bash
python app.py
# Open http://localhost:8000
```

The app downloads the dataset and generates all charts on first startup (~15 s).

### 3b — Run CLI-only (no server)

```bash
python main.py                    # Full EDA pipeline
python main.py --force-download   # Re-download dataset
python main.py --no-charts        # Stats only (faster)
```

### 4 — Run tests

```bash
pytest tests/ -v
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Interactive HTML dashboard |
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/summary` | Dataset shape, dtypes, describe stats |
| `GET` | `/api/missing` | Per-column missing value report |
| `GET` | `/api/correlation?method=pearson` | Correlation matrix |
| `GET` | `/api/survival` | Survival rates by sex, class, port |
| `GET` | `/api/charts` | List of chart URLs |
| `POST` | `/api/run-eda` | Re-trigger full EDA pipeline |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc documentation |

Full interactive API docs: **http://localhost:8000/api/docs**

---

## Docker Deployment

### Build & run with Docker Compose

```bash
# Copy env file
cp .env.example .env

# Build and start
docker compose up --build -d

# Check logs
docker compose logs -f titanic-eda

# Stop
docker compose down
```

The dashboard will be available at **http://localhost:8000**.

### Build image only

```bash
docker build -t titanic-eda:latest .
docker run -p 8000:8000 --env-file .env titanic-eda:latest
```

---

## Cloud Deployment

### AWS EC2

```bash
# On EC2 instance (Amazon Linux 2 / Ubuntu):
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Pull or copy your image, then:
docker compose up -d

# Open port 8000 in your Security Group (or use Nginx on port 80)
```

### Heroku

```bash
heroku create titanic-eda
heroku stack:set container
git push heroku main
heroku open
```

`Procfile` (create if deploying to Heroku without Docker):
```
web: gunicorn -c gunicorn.conf.py app:app
```

### Render / Railway

1. Connect your GitHub repository.
2. Set `Start Command` to `gunicorn -c gunicorn.conf.py app:app`.
3. Add environment variables from `.env.example`.
4. Deploy — both platforms auto-detect `requirements.txt`.

---

## EDA Highlights

| # | Chart | Key Insight |
|---|---|---|
| 01 | Survival Overview | 38.4% survived — severe class imbalance in the target |
| 02 | Age Distribution | Children < 10 had highest survival; age ~28 is modal |
| 03 | Fare by Class | 1st class fares span £6–£512; extreme right skew → log scale |
| 04 | Survival by Sex & Class | Women: 74%; Men: 19% — "women and children first" evident |
| 05 | Correlation Heatmap | Fare ↔ Pclass (−0.55), Pclass ↔ Survived (−0.34) |
| 06 | Missing Value Map | Cabin 77% missing; Age 20%; Embarked < 1% |
| 07 | Age × Fare Scatter | High-fare survivors cluster top-left (young, expensive ticket) |
| 08 | Embarkation Ports | Cherbourg passengers: 55% survival vs 34% Southampton |
| 09 | Family Size | FamilySize 2–4 optimal; solo and large (7+) had low survival |
| 10 | Pair Grid | Age and Fare show clearest distributional separation by survival |
| 11 | Title vs. Survival | Mrs > Miss > Master > Mr mirrors gender/age gradient |

---

## Code Quality

- **Type hints** throughout all modules
- **Docstrings** (Google style) for every function
- **No hardcoded paths** — all paths resolved through `config.py`
- **`ruff`** for linting: `ruff check .`
- **`black`** for formatting: `black .`
- **`mypy`** for type checking: `mypy src/ app.py`
- Efficient pandas operations — no `.iterrows()`, no redundant copies
- LRU caching on expensive analysis results

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-analysis`
3. Run tests: `pytest`
4. Submit a pull request

---

*Built with ❤️ using FastAPI, Pandas, and Seaborn.*
