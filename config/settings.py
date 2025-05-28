# # config/settings.py - ADD THIS TO YOUR EXISTING SETTINGS FILE
# import os
# from pydantic_settings import BaseSettings

# from typing import Optional

# class Settings(BaseSettings):
#     # API Keys
#     ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
#     OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
#     PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
#     HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")  # ADD THIS LINE
#     HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")  # ADD THIS LINE

#     # Vector Store Settings
#     VECTOR_STORE_TYPE: str = "faiss"
#     EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

#     # Agent Settings
#     LLM_MODEL: str = "gpt-3.5-turbo"
#     CONFIDENCE_THRESHOLD: float = 0.7

#     # Voice Settings
#     WHISPER_MODEL: str = "base"
#     TTS_MODEL: str = "tts-1"

#     # FastAPI Settings
#     API_HOST: str = "0.0.0.0"
#     API_PORT: int = 8000

#     class Config:
#         env_file = ".env"

# settings = Settings()
import os
from typing import Optional

class Settings:
    # API Keys
    POLYGON_API_KEY: Optional[str] = os.getenv("POLYGON_API_KEY")
    FINNHUB_API_KEY: Optional[str] = os.getenv("FINNHUB_API_KEY")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Model settings
    WHISPER_MODEL: str = "base"
    
    # Portfolio file path
    PORTFOLIO_FILE: str = os.getenv("PORTFOLIO_FILE", "data/portfolio.json")

settings = Settings()