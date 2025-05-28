import yfinance as yf
import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp

class MarketDataIngestion:
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        self.alpha_vantage_key = alpha_vantage_key

    async def get_yahoo_finance_data(self, symbols: List[str]) -> Dict:
        """Fetch data from Yahoo Finance"""
        data = {}
        for symbol in symbols:
            print(f"📈 Fetching data for: {symbol}")
            try:
                ticker = yf.Ticker(symbol)

                # Use fast_info for better reliability
                fast_info = ticker.fast_info
                hist = ticker.history(period="5d")

                data[symbol] = {
                    "current_price": fast_info.get("last_price", 0),
                    "market_cap": fast_info.get("market_cap", 0),
                    "pe_ratio": fast_info.get("pe_ratio", 0),
                    "volume": fast_info.get("last_volume", 0),
                    "history": hist.to_dict(),
                    "sector": "Unknown",  # fast_info doesn't provide this
                    "country": "Unknown"
                }

            except Exception as e:
                print(f"❌ Error fetching data for {symbol}: {e}")
                data[symbol] = {"error": str(e)}

        return data

    async def get_alpha_vantage_data(self, symbol: str) -> Dict:
        """Fetch data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return {"error": "Alpha Vantage API key not provided"}

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    return data
        except Exception as e:
            print(f"❌ Alpha Vantage error for {symbol}: {e}")
            return {"error": str(e)}
