# Trackflation: Uncovering Technological Inflation in Elite Athletics

[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Causal Inference](https://img.shields.io/badge/Method-Causal%20Inference-blue)](notebooks/did_shoe_analysis.ipynb)
[![Forecasting](https://img.shields.io/badge/Model-Prophet%20%2B%20Conformal-orange)](src/forecaster.py)

**Trackflation** is an end-to-end analytical suite designed to quantify the "inflation" of track and field performance over the last 50 years. By combining **Causal Inference (Difference-in-Differences)**, **Survival Analysis**, and **Bayesian Forecasting**, we isolate the impact of equipment innovation (e.g., Carbon Plates) from biological evolution.

---

## 🚀 Executive Summary: The "So What?"

Since the launch of the Nike Vaporfly in 2017, distance running times have plummeted at a rate that defies historical biological trends. This study confirms that we are living in an era of **Technological Inflation**:
- **The Shoe Effect**: Carbon-plated technology has provided a **~1.5% efficiency gain** in the marathon, equivalent to shaving nearly **2 minutes** off a sub-2:04 performance through equipment alone.
- **The Death of Longevity**: World records are now **3x more likely to fall** in any given year compared to the pre-2017 era, driven by the rapid diffusion of high-stack foam and "super spikes."
- **Approaching the Ceiling**: While technology has provided a temporary "step-down" in times, projections for 2046 show **diminishing returns** as performances approach the absolute physiological limits of human muscle fiber and cardiovascular output.

---

## 📊 Visual Evidence

### 1. Cumulative Improvement % by Event
Endurance events (Marathon, 10,000m) have seen significantly higher relative gains compared to explosive sprints, highlighting the disproportional benefit of energy-return technology in distance running.
![Improvement Comparison Line](improvement_comparison_line.png)

### 2. Total Improvement (1974 vs 2026)
![Improvement Comparison Bar](improvement_comparison_bar.png)

---

## 🔮 20-Year Tapered Projections (2026-2046)

Using **Logistic Growth** and **Rolling Window Conformal Prediction**, we project the most realistic World Records for 2046, accounting for biological ceilings.

| Event        | 2000       | 2026 (Actual WR) | **2046 AI Projection** |
|:-------------|:-----------|:-----------------|:-----------------------|
| **100m**     | 9.85s      | 9.58s            | **9.50s**              |
| **Marathon** | 2:05:56    | 1:59:30          | **1:58:07**            |
| **5000m**    | 13:01.11   | 12:35.36         | **12:29.44**           |

---

## 🛠️ Production-Grade Architecture

The codebase is structured for scalability and reproducibility:
- `src/config.py`: Centralized management of biological floors and historical benchmarks.
- `src/cli.py`: Unified command-line interface for multi-event analysis.
- `src/forecaster.py`: Advanced forecasting engine using Prophet with Conformal Prediction.
- `notebooks/`: Specialized causal studies (DiD, ITS, Synthetic Control) and Monte Carlo simulations.

---

## ⚙️ Reproducibility & Setup

Total environment parity is guaranteed via **Poetry**.

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Run Analysis for an Event**:
   ```bash
   poetry run trackflation run-event --event "marathon"
   ```

3. **Generate Global Comparisons**:
   ```bash
   poetry run trackflation compare-all
   ```

4. **Explore Advanced Causal Models**:
   - [Difference-in-Differences Study](notebooks/did_shoe_analysis.ipynb)
   - [Monte Carlo Ceiling Sensitivity](notebooks/monte_carlo_ceiling.ipynb)
   - [Record Breaking Hazard Model](notebooks/record_hazard_model.ipynb)

---

## 🧪 Methodology Overview
- **Causal Inference**: We use **Difference-in-Differences (DiD)** and **Synthetic Control** to isolate the treatment effect of shoe technology.
- **Uncertainty Quantification**: **Conformal Prediction** ensures that our projection intervals have frequentist coverage guarantees without assuming a specific error distribution.
- **Sensitivity Analysis**: **Monte Carlo** simulations sample biological floors from physiological distributions to represent our uncertainty about the human limit.
