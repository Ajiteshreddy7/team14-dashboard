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

## 🤖 Enable AI features (free — Groq)

The dashboard ships with a grounded AI layer (Insight Cards, Fairness Check, Relocation Verdict, and a Natural-Language Query box). These features stay quietly offline unless you provide an API key.

The default provider is **Groq**, which offers a free tier that's more than enough for classroom or demo use.

### 1. Get a free Groq API key

1. Go to [console.groq.com/keys](https://console.groq.com/keys) and sign in (GitHub / Google).
2. Click **Create API Key**, copy the value (it starts with `gsk_...`).

### 2. Add the key to Streamlit Cloud

In your Streamlit Cloud app: **App settings → Secrets → Edit** and add:

```toml
OPENAI_API_KEY = "gsk_your_groq_key_here"
# The two lines below are the defaults; only include them if you want to override.
# OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
# CHATBOT_MODEL   = "llama-3.3-70b-versatile"
```

Save. The app will re-deploy automatically and AI features will light up.

### Run locally

Create `.streamlit/secrets.toml` with the same content (and keep that file out of git — it's already in `.gitignore`).

### Switch providers (optional)

Because the code uses the OpenAI-compatible client, you can point it at any OpenAI-compatible API by changing just the two optional secrets:

| Provider | `OPENAI_BASE_URL` | `CHATBOT_MODEL` | Notes |
|---|---|---|---|
| Groq (default, free) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | Fast & free. |
| Google Gemini (free tier) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-1.5-flash` | Use a Google AI Studio key. |
| OpenAI (paid) | *(leave empty)* | `gpt-4o-mini` | Requires funded OpenAI account. |
| Local Ollama | `http://localhost:11434/v1` | `llama3.2:3b` | Local only, not for Streamlit Cloud. |

If no key is configured, every AI widget renders a neutral "AI features are offline" message and the rest of the dashboard works normally.

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
