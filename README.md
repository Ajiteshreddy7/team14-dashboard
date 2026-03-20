# 🏠 HUD FMR Rent Intelligence Dashboard — Team 14

A Streamlit-based interactive dashboard that transforms HUD Fair Market Rent (FMR) data into actionable insights for HR professionals, remote workers, and anyone navigating relocation or compensation decisions.

---

## 🚀 Live Demo

**[View the live dashboard →](https://jdwexuavexhpsoogak3jjk.streamlit.app)**

> Hosted on Streamlit Community Cloud. No installation required.

---

## 📌 Overview

This dashboard pulls from HUD's official FMR dataset to help users:

- Compare rental costs across geographic markets
- Analyze hiring trends and labor market conditions by region
- Estimate salary adjustments for remote or relocating employees
- Explore historical and projected rental market trends

---

## ✨ Features

| Module | Description |
|---|---|
| **Rent Index** | Visualize and compare Fair Market Rents across cities, counties, and metro areas |
| **Hiring Market** | Explore employment and hiring trends by location |
| **Relocation Analysis** | Side-by-side cost-of-living comparisons to support relocation decisions |
| **Salary Calculator** | Adjust remote compensation based on geographic cost differentials |
| **Market Trends** | Historical trends and forward-looking insights for rental and labor markets |

---

## 🛠️ Tech Stack

- **Python 3.x**
- **[Streamlit](https://streamlit.io/)** — dashboard framework
- **[Pandas](https://pandas.pydata.org/)** — data processing
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — environment variable management
- **HUD FMR 2025 Dataset** (`fi2025.xlsx`)

---

## 📁 Project Structure

```
team14-dashboard/
├── app.py                  # Main Streamlit application entry point
├── test_api.py             # API integration tests for HUD data
├── .env                    # Environment variables (not committed)
├── .gitignore
│
├── components/
│   ├── hiring_market.py    # Hiring market analysis
│   ├── relocation.py       # Relocation cost comparison
│   ├── rent_index.py       # Rent index visualization
│   ├── salary_calc.py      # Salary adjustment calculator
│   └── trends.py           # Market trend analysis
│
└── data/
    ├── fmr_data.py         # FMR data loader and processor
    └── fi2025.xlsx         # HUD Fair Market Rent 2025 dataset
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ajiteshreddy7/team14-dashboard.git
cd team14-dashboard
```

### 2. Install dependencies

```bash
pip install streamlit pandas python-dotenv openpyxl
```

> **Tip:** It's recommended to use a virtual environment:
> ```bash
> python -m venv venv
> source venv/bin/activate      # macOS/Linux
> venv\Scripts\activate         # Windows
> pip install streamlit pandas python-dotenv openpyxl
> ```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
HUD_API_KEY=your_hud_api_key_here
```

> 🔑 You can obtain a free HUD API key at [https://www.huduser.gov/portal/dataset/fmr-api.html](https://www.huduser.gov/portal/dataset/fmr-api.html)

### 4. Run the dashboard

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🚀 Usage

1. Launch the app with `streamlit run app.py`
2. Use the sidebar to navigate between modules (Rent Index, Hiring Market, Relocation, Salary Calculator, Trends)
3. Select a region, metro area, or county to filter the data
4. Explore visualizations and use the Salary Calculator to model compensation scenarios

---

## 📊 Data Source

This dashboard uses **HUD Fair Market Rent (FMR) data** from the U.S. Department of Housing and Urban Development. FMR data represents the 40th percentile of gross rents for standard quality units within a metropolitan area or non-metropolitan county.

- Official HUD FMR dataset: [https://www.huduser.gov/portal/datasets/fmr.html](https://www.huduser.gov/portal/datasets/fmr.html)

---

## 👥 Team

**Team 14** — Built as part of a data visualization and analytics project.

---

## 📄 License

This project is for academic and research purposes. Data sourced from HUD is publicly available and free to use.
