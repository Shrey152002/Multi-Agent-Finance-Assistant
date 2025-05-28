
from config.settings import settings

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import aiohttp
import asyncio
from datetime import datetime

class MarketDataRequest(BaseModel):
    symbols: List[str]

app = FastAPI(title="API Agent", description="Fetches live market data from multiple sources")

class MarketDataService:
    def __init__(self):
        self.polygon_key = settings.POLYGON_API_KEY
        self.finnhub_key = settings.FINNHUB_API_KEY
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY

    async def get_polygon_data(self, symbol: str) -> Dict:
        """Get real-time data from Polygon.io"""
        if not self.polygon_key:
            return {"error": "Polygon API key not configured"}
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {"apikey": self.polygon_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        return {
                            "current_price": result["c"],
                            "open": result["o"],
                            "high": result["h"],
                            "low": result["l"],
                            "volume": result["v"],
                            "source": "polygon"
                        }
                return {"error": f"Failed to fetch from Polygon: {response.status}"}

    async def get_finnhub_data(self, symbol: str) -> Dict:
        """Get real-time data from Finnhub"""
        if not self.finnhub_key:
            return {"error": "Finnhub API key not configured"}
        
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol, "token": self.finnhub_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("c"):
                        return {
                            "current_price": data["c"],
                            "open": data["o"],
                            "high": data["h"],
                            "low": data["l"],
                            "prev_close": data["pc"],
                            "source": "finnhub"
                        }
                return {"error": f"Failed to fetch from Finnhub: {response.status}"}

    async def get_alpha_vantage_data(self, symbol: str) -> Dict:
        """Get data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return {"error": "Alpha Vantage API key not configured"}
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("Global Quote", {})
                    if quote:
                        return {
                            "current_price": float(quote.get("05. price", 0)),
                            "open": float(quote.get("02. open", 0)),
                            "high": float(quote.get("03. high", 0)),
                            "low": float(quote.get("04. low", 0)),
                            "volume": int(quote.get("06. volume", 0)),
                            "source": "alpha_vantage"
                        }
                return {"error": f"Failed to fetch from Alpha Vantage: {response.status}"}

market_service = MarketDataService()

@app.post("/market-data", response_model=Dict[str, Dict])
async def get_market_data(request: MarketDataRequest):
    """Fetch live market data with fallback sources"""
    try:
        print(f"📥 Fetching data for symbols: {request.symbols}")
        results = {}
        
        for symbol in request.symbols:
            symbol = symbol.upper().strip()
            
            # Try multiple sources with fallback
            data = await market_service.get_polygon_data(symbol)
            
            if "error" in data:
                data = await market_service.get_finnhub_data(symbol)
                
            if "error" in data:
                data = await market_service.get_alpha_vantage_data(symbol)
            
            # Add timestamp and symbol info
            if "error" not in data:
                data.update({
                    "symbol": symbol,
                    "timestamp": datetime.utcnow().isoformat(),
                    "change": round(data.get("current_price", 0) - data.get("prev_close", data.get("current_price", 0)), 2),
                    "change_percent": round(((data.get("current_price", 0) - data.get("prev_close", data.get("current_price", 0))) / data.get("prev_close", 1)) * 100, 2)
                })
            
            results[symbol] = data

        print(f"✅ Successfully fetched data for {len([r for r in results.values() if 'error' not in r])} symbols")
        return results

    except Exception as e:
        print(f"❌ Error in get_market_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api_agent"}