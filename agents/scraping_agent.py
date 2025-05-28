


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class ScrapingRequest(BaseModel):
    target: str  # ticker symbol or search query
    source: str  # news, earnings, filings, or social
    limit: int = 10

class ScrapingResponse(BaseModel):
    documents: List[Dict]
    count: int
    source: str
    timestamp: str

app = FastAPI(title="Scraping Agent", description="Live financial data scraping service")

class FinancialScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def scrape_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Scrape financial news from multiple sources"""
        documents = []
        
        # Yahoo Finance News
        yahoo_docs = await self._scrape_yahoo_news(symbol, limit//2)
        documents.extend(yahoo_docs)
        
        # MarketWatch News
        marketwatch_docs = await self._scrape_marketwatch_news(symbol, limit//2)
        documents.extend(marketwatch_docs)
        
        return documents[:limit]

    async def _scrape_yahoo_news(self, symbol: str, limit: int) -> List[Dict]:
        """Scrape Yahoo Finance news"""
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = []
                        news_items = soup.find_all('h3', class_='Mb(5px)')[:limit]
                        
                        for item in news_items:
                            link = item.find('a')
                            if link:
                                articles.append({
                                    'title': link.get_text().strip(),
                                    'url': f"https://finance.yahoo.com{link.get('href')}",
                                    'source': 'Yahoo Finance',
                                    'symbol': symbol,
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'content': link.get_text().strip()[:300] + "..."
                                })
                        
                        return articles
        except Exception as e:
            print(f"❌ Yahoo scraping error: {e}")
            return []

    async def _scrape_marketwatch_news(self, symbol: str, limit: int) -> List[Dict]:
        """Scrape MarketWatch news"""
        try:
            url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        articles = []
                        news_items = soup.find_all('a', class_='link')[:limit]
                        
                        for item in news_items:
                            if item.get_text().strip():
                                articles.append({
                                    'title': item.get_text().strip(),
                                    'url': item.get('href'),
                                    'source': 'MarketWatch',
                                    'symbol': symbol,
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'content': item.get_text().strip()[:300] + "..."
                                })
                        
                        return articles
        except Exception as e:
            print(f"❌ MarketWatch scraping error: {e}")
            return []

    async def scrape_earnings(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Scrape earnings information"""
        try:
            # Using free API for earnings calendar
            url = f"https://financialmodelingprep.com/api/v3/earning_calendar?symbol={symbol}&apikey=demo"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        documents = []
                        for item in data[:limit]:
                            documents.append({
                                'title': f"Earnings Report - {item.get('symbol', symbol)}",
                                'date': item.get('date'),
                                'eps_estimate': item.get('epsEstimated'),
                                'eps_actual': item.get('eps'),
                                'revenue_estimate': item.get('revenueEstimated'),
                                'revenue_actual': item.get('revenue'),
                                'source': 'Financial Modeling Prep',
                                'symbol': symbol,
                                'timestamp': datetime.utcnow().isoformat(),
                                'content': f"Earnings data for {symbol}: EPS estimate {item.get('epsEstimated')}, actual {item.get('eps')}"
                            })
                        
                        return documents
        except Exception as e:
            print(f"❌ Earnings scraping error: {e}")
            return []

    async def scrape_social_sentiment(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Scrape social media sentiment (mock implementation)"""
        # In a real implementation, you'd integrate with Twitter API, Reddit API, etc.
        mock_sentiments = [
            {"platform": "Twitter", "sentiment": "bullish", "mentions": 1250},
            {"platform": "Reddit", "sentiment": "neutral", "mentions": 890},
            {"platform": "StockTwits", "sentiment": "bearish", "mentions": 650}
        ]
        
        documents = []
        for sentiment in mock_sentiments:
            documents.append({
                'title': f"{symbol} Social Sentiment - {sentiment['platform']}",
                'platform': sentiment['platform'],
                'sentiment': sentiment['sentiment'],
                'mentions': sentiment['mentions'],
                'source': 'Social Media Aggregator',
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'content': f"{symbol} showing {sentiment['sentiment']} sentiment on {sentiment['platform']} with {sentiment['mentions']} mentions"
            })
        
        return documents

scraper = FinancialScraper()

@app.post("/scrape", response_model=ScrapingResponse)
async def scrape_documents(request: ScrapingRequest):
    """Scrape financial documents based on target and source"""
    try:
        documents = []
        
        if request.source == "news":
            documents = await scraper.scrape_news(request.target, request.limit)
        elif request.source == "earnings":
            documents = await scraper.scrape_earnings(request.target, request.limit)
        elif request.source == "social":
            documents = await scraper.scrape_social_sentiment(request.target, request.limit)
        else:
            raise HTTPException(status_code=400, detail="Invalid source type. Use: news, earnings, or social")
        
        return ScrapingResponse(
            documents=documents,
            count=len(documents),
            source=request.source,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scraping_agent"}