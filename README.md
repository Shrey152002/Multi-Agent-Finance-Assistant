# Multi-Agent-Finance-Assistant
A powerful multi-agent financial assistant system built using FastAPI, Streamlit, OpenAI, and real-time financial APIs. This application supports intelligent query handling, live market data ingestion, voice interaction, risk analysis, document scraping, and more.

🚀 Features
📈 Live Market Data from Polygon.io, Finnhub, Alpha Vantage, and Yahoo Finance.

🔍 Portfolio Analysis for diversification, exposure, and risk metrics.

🧠 LLM-Powered Language Agent for financial reasoning and synthesis.

📑 Retriever Agent to query stored portfolio data.

📰 Scraping Agent for real-time news, earnings, and sentiment.

🗣️ Voice Agent supporting audio transcription (Whisper) and TTS.

🎧 Streamlit Dashboard for interactive chat and voice-based finance Q&A.

🧩 Architecture
less
Copy
Edit
[ Streamlit UI ] --> [ Orchestrator Service ]
                           |
    -----------------------------------------------------
    |       |           |          |         |         |
[API Agent][Retriever][Analysis][Language][Scraping][Voice]
📁 Project Structure
bash
Copy
Edit
finance-assistant/
│
├── agents/
│   ├── analysis_agent.py
│   ├── api_agent.py
│   ├── language_agent.py
│   ├── retriever_agent.py
│   ├── scraping_agent.py
│   └── voice_agent.py
│
├── config/
│   └── settings.py         # Environment variable settings
│
├── data/
│   ├── portfolio.json      # Default portfolio
│
├── data_ingestion/
│   ├── document_loader.py
│   └── embedding_service.py
│
├── orchestrator/
│   ├── main.py             # Orchestrates all agents
│
├── streamlit_app/
│   ├── app.py              # Main Streamlit interface
│
├── .env                    # API keys
├── requirements.txt
└── README.md
⚙️ Setup Instructions
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/yourusername/finance-assistant.git
cd finance-assistant
2. Install Requirements
bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the root directory:

env
Copy
Edit
POLYGON_API_KEY=your_polygon_api_key
FINNHUB_API_KEY=your_finnhub_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
OPENAI_API_KEY=your_openai_api_key
PORTFOLIO_FILE=data/portfolio.json
🧪 Run Services
Each agent runs independently on a port:

bash
Copy
Edit
# Run orchestrator
uvicorn orchestrator.main:app --port 8000

# Run agents
uvicorn agents.api_agent:app --port 8001
uvicorn agents.scraping_agent:app --port 8002
uvicorn agents.retriever_agent:app --port 8003
uvicorn agents.analysis_agent:app --port 8004
uvicorn agents.language_agent:app --port 8005
uvicorn agents.voice_agent:app --port 8006
🌐 Run the Frontend
bash
Copy
Edit
streamlit run streamlit_app/app.py
You can then access the UI at http://localhost:8501.

🗣️ Voice Interaction
The voice agent uses OpenAI Whisper for transcription and TTS-1 for speech synthesis. Ensure audio files are under 25MB and in supported formats (WAV, MP3, M4A, etc.).

🧪 Example Use Cases
"Show me the risk exposure in my tech holdings."

"What is the latest news about NVIDIA?"

"Summarize my portfolio performance."

Upload audio: "How is the stock market doing today?" ➝ Get analysis ➝ Listen to voice output.

📊 Agent Health
Each agent provides a /health endpoint:

http://localhost:8001/health

http://localhost:8002/health

...

Use these to monitor service status in the Streamlit sidebar.

✅ TODOs / Improvements
 Deploy using Docker Compose or Kubernetes.

 Enhance document scraping (e.g., real SEC API).

 Add persistent vector store for document embeddings.

 Enable OAuth2 for user-based portfolios.

🤝 Contributing
Fork the repository.

Create your branch (git checkout -b feature/xyz)

Commit changes (git commit -am 'Add xyz')

Push (git push origin feature/xyz)

Create a Pull Request.

📄 License
This project is licensed under the MIT License.

