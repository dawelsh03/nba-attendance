# NBA Attendance Intelligence Platform
### League-wide game attendance analysis — 30 teams, 3 seasons (2022-23 through 2024-25)

A complete end-to-end data science project analyzing what drives NBA game-level attendance variation, built with real publicly available data. Developed as a portfolio project targeting a Data Scientist role with a professional sports organization.

---

## Key Findings

| Finding | Result | Business Implication |
|---|---|---|
| Season win % is the top attendance driver | Highest feature importance in XGBoost model | Teams in winning seasons can reduce promotional spend |
| Weekend games draw 3.5pp more than weekdays | Saturday 98.9% vs Monday 95.4% | Weeknight games are the primary promotional window |
| Win streak threshold | Attendance crosses league avg at 3-4 wins, near-sellout at 5-6 | Pause discounts at game 3 of any winning streak |
| Day of week > opponent quality | Tier C on Saturday (98.3%) outdraws Tier A on Tuesday (98.0%) | Schedule cannot rely on marquee opponents to save weeknight games |
| 7.8% of games fall below 85% capacity | Concentrated in 5-6 franchises | Washington, Charlotte, Detroit account for majority of at-risk games |
| Pre-season risk classifier AUC = 0.853 | Using only schedule information | At-risk games identifiable before season starts |

---

## Business Questions Answered

| # | Question | Method | Notebook |
|---|---|---|---|
| Q1 | What drives game-to-game attendance variation? | XGBoost regression + feature importance | 02_models |
| Q2 | At what win streak should teams stop discounting? | Statistical analysis + bucketing | 01_eda |
| Q3 | How does day of week interact with opponent quality? | Interaction heatmap | 01_eda |
| Q4 | Do games cluster into natural demand tiers? | K-Means clustering (k=8) | 02_models |
| Q5 | Which games are most at risk before the season starts? | XGBoost binary classifier | 02_models |

---

## Data Sources — All Real

| Source | Data | Method |
|---|---|---|
| Basketball-Reference | Game-by-game attendance, results, opponents — all 30 teams | Web scraper (`src/scrape_bref.py`) |
| Open-Meteo API | Historical weather per arena city on each game date | Free API (`src/collect_weather.py`) |
| Manual research | Arena capacity and market size | 30-row CSV (`data/manual/arena_info.csv`) |

**Total dataset:** 3,705 real home games × 42 engineered features

**Data notes:**
- One neutral-site game (San Antonio vs. Mexico City, 68,323 attendance) removed as it exceeds any NBA arena capacity
- Back-to-back calculation is based on home game spacing — true back-to-backs including away games would require full schedule data
- Capacity figures reflect standard configuration; teams regularly exceed listed capacity via standing room

---

## Model Results

### Model 1 — XGBoost Attendance Regression
- **MAE:** 5.06 percentage points (5-fold time-series CV)
- **R²:** ~0.00 — reflects data structure: 92% of games are near capacity ceiling
- **Key insight:** Model most valuable for identifying the 7.8% of games with meaningful attendance risk, not predicting the majority of sellouts
- **Top drivers:** Season win %, weekend game, opponent tier, rolling win %, day of week

### Model 2 — K-Means Game Demand Clustering
- **k=8** selected by silhouette score (0.198)
- **4 demand tiers identified:** High Demand, Moderate Demand, Below Average, At Risk
- **At Risk cluster:** 284 games, 79.6% avg capacity — characterized by weekday games, losing streaks, weak opponents

### Model 3 — Low Attendance Classifier
- **ROC-AUC: 0.853** using only pre-season features (opponent, day, month, back-to-back)
- **Limitation:** Most actionable for mid-tier franchises; perennial sellout teams (Boston, Golden State, Dallas) sell out regardless of game profile
- **Most predictive features:** Weekend game, day of week, opponent tier

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create MySQL database
# Open MySQL Workbench and run sql/01_schema.sql

# 3. Configure credentials
cp .env.example .env
# Edit .env with your MySQL password

# 4. Collect data (run in order — takes ~20 minutes)
python3 src/scrape_bref.py        # 90 requests, 3s delay each
python3 src/collect_weather.py    # Free Open-Meteo API
python3 src/build_features.py     # Joins all sources, engineers features
python3 src/load_to_mysql.py      # Loads into MySQL star schema

# 5. Run analysis
jupyter notebook
# Open notebooks/01_eda.ipynb then notebooks/02_models.ipynb
```

---

## Project Structure

```
nba-attendance-platform/
├── data/
│   ├── raw/                    ← scraped attendance + weather data
│   ├── processed/              ← feature-engineered dataset (3,705 × 42)
│   └── manual/                 ← arena_info.csv (30 rows, manually researched)
├── sql/
│   ├── 01_schema.sql           ← MySQL star schema (5 tables)
│   └── 02_queries.sql          ← 7 business analytics queries
├── notebooks/
│   ├── 01_eda.ipynb            ← EDA: Q2, Q3 + attendance distribution analysis
│   └── 02_models.ipynb         ← ML models: Q1, Q4, Q5
├── src/
│   ├── scrape_bref.py          ← Basketball-Reference scraper (all 30 teams)
│   ├── collect_weather.py      ← Open-Meteo weather collector
│   ├── build_features.py       ← Feature engineering pipeline
│   └── load_to_mysql.py        ← MySQL loader with star schema
├── reports/                    ← 10 saved charts from notebooks
├── .env.example
├── requirements.txt
└── README.md
```

---

## Tech Stack

Python · pandas · NumPy · scikit-learn · XGBoost · matplotlib · seaborn · MySQL · SQLAlchemy · BeautifulSoup · Jupyter

---

*Built as a portfolio project. Data sourced from public sources. Not affiliated with the NBA.*
