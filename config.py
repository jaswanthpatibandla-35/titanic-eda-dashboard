"""
config.py - Centralized configuration for Titanic EDA Project
All paths, constants, and settings managed here. No hardcoded values elsewhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Base Paths ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORTS_DIR = OUTPUT_DIR / "reports"
CLEANED_DATA_DIR = OUTPUT_DIR / "cleaned_data"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# ── Dataset ────────────────────────────────────────────────────────────────────
DATASET_URL = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
RAW_DATA_PATH = DATA_DIR / "titanic_raw.csv"
CLEANED_DATA_PATH = CLEANED_DATA_DIR / "titanic_cleaned.csv"

# ── App / Server ───────────────────────────────────────────────────────────────
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Cache ──────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 3600))  # 1 hour
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", 128))

# ── EDA / Visualisation ────────────────────────────────────────────────────────
RANDOM_SEED = 42
FIGURE_DPI = 150
FIGURE_FORMAT = "png"
PALETTE = "deep"          # seaborn palette
STYLE = "whitegrid"       # seaborn style

# Columns expected in the raw dataset
EXPECTED_COLUMNS = [
    "PassengerId", "Survived", "Pclass", "Name", "Sex",
    "Age", "SibSp", "Parch", "Ticket", "Fare", "Cabin", "Embarked",
]

NUMERIC_FEATURES = ["Age", "Fare", "SibSp", "Parch"]
CATEGORICAL_FEATURES = ["Survived", "Pclass", "Sex", "Embarked"]
TARGET_COLUMN = "Survived"

# ── Ensure output directories exist ───────────────────────────────────────────
for _dir in (DATA_DIR, CHARTS_DIR, REPORTS_DIR, CLEANED_DATA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
