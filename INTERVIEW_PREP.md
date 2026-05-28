# NBA Attendance Intelligence Platform
## Resume Bullets & Interview Talking Points

---

## Resume Bullets

Pick 3-4 of these depending on which skills you want to emphasize.

**Data Engineering**
- Built end-to-end NBA attendance analytics pipeline ingesting real data from 3 sources (Basketball-Reference web scraper, Open-Meteo API, manual arena research) across 30 teams and 3 seasons; engineered 42 features from 3,705 real home games

**SQL & Database**
- Designed and populated a MySQL star schema with 5 tables and 3,705+ records; wrote 7 business analytics queries answering questions on day-of-week effects, win streak thresholds, opponent tier premiums, and weather impact

**Machine Learning — Regression**
- Trained XGBoost attendance forecasting model using time-series cross-validation to prevent data leakage; identified season win percentage, weekend/weekday, and opponent tier as top attendance drivers across the league

**Machine Learning — Classification**
- Developed binary classifier (ROC-AUC 0.853) predicting low-attendance risk games using only pre-season schedule information; model enables ticket sales teams to identify promotional intervention targets before the season begins

**Machine Learning — Clustering**
- Applied K-Means clustering (k=8, silhouette 0.198) to segment 3,705 NBA games into demand tiers; identified an "At Risk" cluster of 284 games characterized by weekday scheduling, losing streaks, and weak opponents

**Business Intelligence**
- Quantified key NBA attendance drivers: 3.5pp weekend premium, win streak threshold at 3-4 wins, and interaction effect showing day of week dominates opponent quality — Saturday with a weak opponent outdraws Tuesday with a marquee opponent

---

## Interview Talking Points

### "Walk me through your project"

Lead with the business problem, not the technical approach:

> "I wanted to build something that answered questions a real NBA ticket sales team would actually care about. The central finding is that in the current era where most NBA teams sell out regularly, the interesting analytics question isn't whether games fill up — it's understanding the game-level variation that still exists and what drives it. I pulled real attendance data for all 30 teams across 3 seasons, joined it with weather data and schedule context, and built three models: a regression model to quantify attendance drivers, a clustering model to segment games into demand tiers, and a classifier that can flag at-risk games before the season even starts."

---

### "What were your most interesting findings?"

> "The most non-obvious finding was the interaction between day of week and opponent quality. You'd expect a marquee opponent — Lakers, Celtics — to overcome the weeknight attendance penalty. But the data shows that a weak opponent on Saturday still outdraws a marquee opponent on Tuesday. Day of week is a stronger attendance driver than who's playing. The implication is that teams can't rely on scheduling a big matchup to save a Wednesday night game — the day itself matters more."

---

### "Why was your R² so low on the regression model?"

This will be asked. Have a clean answer ready:

> "The low R² reflects the structure of the data rather than a model failure. Ninety-two percent of games in the dataset are at or near full capacity — there's very little variance for the model to explain in the majority of games. The model's value is in identifying the 7.8% of games that fall meaningfully below capacity, where it achieves useful predictive accuracy. I was intentional about not inflating the R² by removing the sellout teams from the training data — that would have made the metric look better but made the model less honest."

---

### "How did you handle data leakage in the regression model?"

> "I used time-series cross-validation rather than random train-test splits. In a random split you might use a game from March to predict a game from October of the same season — that leaks future information into the past. Time-series CV ensures the model always trains on games that came before the test games chronologically. I also only used features that would be known before tip-off — I explicitly excluded game outcome, points scored, and any statistics generated during the game itself."

---

### "The classifier flagged Boston Celtics games as high risk but they sold out — isn't that wrong?"

> "That's actually one of the most useful findings from the project. The classifier identifies risky game profiles — midweek, weak opponent, back-to-back — but can't account for franchise-level sellout behavior. Boston, Golden State, and Dallas sell out regardless of game profile. The model is most actionable for mid-tier franchises like Brooklyn, Atlanta, and the LA Clippers where those profiles actually translate to attendance risk. In a production environment you'd add a team-level fixed effect or build separate models by franchise tier. The limitation is documented and worth discussing."

---

### "How does this connect to the Cavaliers role specifically?"

> "The job description mentions decision support through ad-hoc analysis and scenario modeling, extracting data from disparate data streams, and communicating with both technical and business stakeholders. This project does all three. The data pipeline combines three real sources into a single analytical dataset — that's the disparate streams requirement. The win streak threshold analysis and day-of-week interaction are exactly the kind of scenario modeling a ticket sales VP would want. And I built two outputs deliberately — the technical notebooks for the analytics team and the README with key findings framed in business language for stakeholders."

---

### "What would you do differently with real Cavaliers internal data?"

> "Three things. First, I'd add actual transaction-level ticket sales data — knowing when tickets sell, at what price, and through which channel would dramatically improve the classifier. Second, I'd add a team-level fixed effect to the regression model to account for franchise-specific sellout behavior — that would improve R² significantly. Third, I'd build a real-time scoring pipeline so the at-risk predictions update as the season progresses and the team's win percentage changes. Right now the classifier only uses pre-season information. With in-season data updating weekly it would get meaningfully more accurate."

---

### On the clustering model

> "The silhouette score kept improving through k=8, which tells you something interesting — the data doesn't have strong natural cluster boundaries, it's more of a continuous distribution. Eight clusters emerged but the meaningful distinction is really between the At Risk cluster at 79% average capacity and everything else above 97%. I was honest about that in the analysis rather than forcing a cleaner story onto the data."

---

## GitHub README Tips

When pushing to GitHub:
- Put the Key Findings table at the very top — recruiters spend 60 seconds on a README
- Link directly to the notebooks in the README so they can view rendered versions on GitHub
- Add a "Data Notes" section being explicit about what's real vs. estimated — shows integrity
- Include the model results table with honest metrics — a weak R² explained well is more impressive than a suspiciously high one with no caveats
