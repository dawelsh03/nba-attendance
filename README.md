# NBA Attendance Project
Game Attendance Analysis
- 30 teams, 3 seasons (2022-23 through 2024-25).

- Analyzing what drives NBA games attendance variation, built with real publicly available data.

# Insights 

- Season win % was the strongest predictor of game attendance across all 14 features in the model.
- Weekend games draw 3.5% more attendance than weekdays (Saturday 98.9% vs. Monday 95.4%).
- A 3-4 game win streak is where attendance crosses the league average. At a 5-6 game win streak, games begin to sellout.
- Day of the week > opponent quality (Tier C on Saturday: 98.3% vs Tier A on Tuesday: 98.0%).
- 7.8% of games fall below 85% capacity (Washington, Charlotte, and Detroit accounted for a majority of these games).
- Using only pre-season schedule information (opponent, day of week, back-to-back status), the model acheived an AUC of 0.853. It can correctly identify most at risk games before the season even begins.

# Questions

1: What drives attendance variation? 
- XGBoost Regression
- 02_models

2: At what win streak does attendance create sellouts? 
- Statistical Analysis
- 01_eda

3: How does day of the week interact with opponent quality? 
- Interaction Heatmap
- 01_eda

4: Do games cluster into natural demand tiers?
- K-Means Clustering
- 02_models

5: Which games are most at risk before the season starts?
- XGBoost Classifier
- 02_models

# Data Sources

1. Basketball-Reference
- Game-by-game attendance, results, opponents for all 30 teams
- Web scraper (`src/scrape_bref.py`)

2. Open-Meteo API
- Historical weather per arena city on each game date
- Free API (`src/collect_weather.py`)

3. Manual research
- Arena capacity and market size
- 30-row CSV (`data/manual/arena_info.csv`)

4. Data Notes
- 3,705 home games
- 42 engineered features
- 1 neutral-site game (San Antonio Spurs vs. Golden State Warriors in Mexico City) removed as it exceeds any NBA arena capacity (68,323).
- Back-to-back calculation is based on home game spacing only, back-to-backs including away games are not included.
- Capacity figures reflect standard seats, teams regularly exceed listed capacity via standing room

# Model Results

Model 1: XGBoost Attendance Regression
- **MAE:** 5.06% (Time Series)
- **R²:** ~ 0
  - Likely due to 92% of games being near capacity ceiling.
  - Model is most valuable for identifying the 7.8% of games with more attendance risk.
- **Top Drivers**
  - Season win %, weekend game, opponent tier, rolling win %, day of week

Model 2: K-Means Game Demand Clustering
- **k=8**
  - Selected by silhouette score (0.198)
- **4 Demand Tiers**
  - High Demand, Moderate Demand, Below Average, At Risk
- **At Risk Cluster**
  -   284 games, 79.6% avg capacity
  -   Characterized by weekday games, losing streaks, weak opponents

Model 3: Low Attendance Classifier
- **ROC-AUC: 0.853**
  - Using only pre-season features (opponent, day, month, back-to-back)
- Most valuable for mid-tier franchises because teams that sellout most games sell out regardless of game profile.
- **Most predictive features**
  - Weekend game, day of week, opponent tier


# Setup

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

## Project Structure

```
nba-attendance-platform/
├── data/
│   ├── raw/                    ← Scraped attendance & weather data
│   ├── processed/              ← Engineered dataset (3,705 × 42)
│   └── manual/                 ← arena_info.csv
├── sql/
│   ├── 01_schema.sql           ← MySQL schema
│   └── 02_queries.sql          ← 7 analytics queries
├── notebooks/
│   ├── 01_eda.ipynb            ← EDA: analysis on specific questions
│   └── 02_models.ipynb         ← ML models: more analysis on specific questions
├── src/
│   ├── scrape_bref.py          ← Basketball-Reference scraper
│   ├── collect_weather.py      ← Open-Meteo weather collector
│   ├── build_features.py       ← Engineering pipeline
│   └── load_to_mysql.py        ← MySQL loader
├── reports/                    ← 10 charts from notebooks
├── .env.example
├── requirements.txt
└── README.md
```

## Tech Stack

Python · pandas · NumPy · scikit-learn · XGBoost · matplotlib · seaborn · MySQL · SQLAlchemy · BeautifulSoup · Jupyter

# Disclaimer

*Built as a portfolio project. Data sourced from public sources. Not affiliated with the NBA.*
