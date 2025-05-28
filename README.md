# 💼 Multi-Agent Finance Assistant

A powerful **multi-agent financial assistant** built with FastAPI, Streamlit, OpenAI, and real-time finance APIs. It supports intelligent chat and voice-based interaction for portfolio analytics, market research, and financial insights.

---

## ✨ Features

* 📊 **Real-time Market Data** via Polygon, Finnhub, Alpha Vantage, and Yahoo
* 🔍 **Portfolio Analysis**: Exposure, diversification, volatility, and risk
* 🧠 **LLM-Powered Chat Agent** with OpenAI GPT
* 📚 **Retriever Agent** for portfolio search and summaries
* 🔖 **Web Scraping Agent**: News, earnings, and sentiment
* 🎧 **Voice Agent**: Transcribe and speak queries/responses
* 🌐 **Streamlit UI**: Easy-to-use chat and voice dashboard

---

## 🧠 Agent Overview

### 1. 🔍 **API Agent** (`api_agent.py`)

* Fetches **live market data** for stock symbols
* Sources: Polygon.io, Finnhub, Alpha Vantage
* Endpoint: `/market-data`

### 2. 📊 **Analysis Agent** (`analysis_agent.py`)

* Analyzes portfolio risk and diversification
* Computes: Exposure, Volatility, Sector/Regional Breakdown, Risk Score
* Endpoint: `/analyze`

### 3. 🧠 **Language Agent** (`language_agent.py`)

* Uses OpenAI GPT to synthesize responses from:

  * Market data
  * Portfolio analysis
  * Retrieved documents
* Endpoint: `/synthesize`

### 4. 📆 **Retriever Agent** (`retriever_agent.py`)

* Searches portfolio documents by keywords or summary
* Endpoint: `/retrieve`

### 5. 🔍 **Scraping Agent** (`scraping_agent.py`)

* Scrapes financial news, earnings reports, and social sentiment
* Sources: Yahoo Finance, MarketWatch, Financial Modeling Prep (demo)
* Endpoint: `/scrape`

### 6. 🎧 **Voice Agent** (`voice_agent.py`)

* 📻 **Speech-to-Text**: Upload audio files for transcription (OpenAI Whisper)
* 🎤 **Text-to-Speech**: Speak AI responses (OpenAI TTS)
* Endpoints: `/transcribe`, `/synthesize`

---

## 🖋️ Architecture Overview

```
[ Streamlit UI ] --> [ Orchestrator ]
                          |
      ------------------------------------------------
      |      |        |        |        |         |
    [API] [Scraper] [Retriever] [Analysis] [Language] [Voice]
```

---

## 📁 Project Structure

```
.
├── agents/
│   ├── api_agent.py
│   ├── analysis_agent.py
│   ├── language_agent.py
│   ├── retriever_agent.py
│   ├── scraping_agent.py
│   └── voice_agent.py
│
├── config/settings.py
├── orchestrator/main.py
├── streamlit_app/app.py
├── data/portfolio.json
├── .env
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/finance-assistant.git
cd finance-assistant
```

### 2. Install Requirements

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file:

```env
POLYGON_API_KEY=your_key
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
OPENAI_API_KEY=your_key
PORTFOLIO_FILE=data/portfolio.json
```

---

## 💪 Run Agents & UI

### Run All Agents (separately):

```bash
uvicorn orchestrator.main:app --port 8000
uvicorn agents.api_agent:app --port 8001
uvicorn agents.scraping_agent:app --port 8002
uvicorn agents.retriever_agent:app --port 8003
uvicorn agents.analysis_agent:app --port 8004
uvicorn agents.language_agent:app --port 8005
uvicorn agents.voice_agent:app --port 8006
```

### Run Streamlit UI:

```bash
streamlit run streamlit_app/app.py
```

---

## 🔊 Voice Interaction

### 🎧 Upload Audio:

* WAV, MP3, M4A, etc. (< 25MB)
* Transcribed to text via OpenAI Whisper

### 🎤 Generate Voice:

* Use OpenAI TTS to generate spoken response
* Supports Alloy, Echo, Nova, Shimmer, etc.

---

## 🔍 Sample Queries

| Type     | Example                                              |
| -------- | ---------------------------------------------------- |
| Text     | "What's the risk level of my portfolio?"             |
| Voice    | Upload MP3: "How is the semiconductor sector doing?" |
| Market   | "Show me news about AAPL"                            |
| Earnings | "Any surprises in MSFT's earnings?"                  |

---

## 📈 Agent Health Checks

Each agent exposes `/health`:

```
http://localhost:8001/health  # API Agent
http://localhost:8004/health  # Analysis Agent
...etc.
```

Streamlit shows a real-time dashboard with agent status.

---

## 💪 Contributing

1. Fork this repo
2. Create a new branch: `feature/xyz`
3. Commit changes
4. Open Pull Request

---

## 📄 License

MIT License. See `LICENSE` file.

---

## 🌟 Credits

Built by combining the power of:

* OpenAI APIs
* FastAPI microservices
* Streamlit UI
* BeautifulSoup + Aiohttp
* SentenceTransformers / Tfidf
* Alpha Vantage, Finnhub, Polygon, Yahoo Finance APIs
