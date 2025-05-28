


from config.settings import settings

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import os
from datetime import datetime

class RetrieveRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class RetrieveResponse(BaseModel):
    documents: List[Dict]
    summary: str
    count: int

app = FastAPI(title="Retriever Agent", description="Dynamic portfolio data retrieval")

class PortfolioRetriever:
    def __init__(self):
        self.portfolio_data = self._load_portfolio()

    def _load_portfolio(self) -> List[Dict]:
        """Load and validate portfolio data"""
        portfolio_file = settings.PORTFOLIO_FILE
        
        # Create default portfolio if file doesn't exist
        if not os.path.exists(portfolio_file):
            default_portfolio = [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "shares": 10,
                    "avg_cost": 150.00,
                    "current_value": 1750.00,
                    "sector": "Technology",
                    "region": "US",
                    "return": 250.00,
                    "return_percent": 16.67
                },
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "shares": 5,
                    "avg_cost": 300.00,
                    "current_value": 1650.00,
                    "sector": "Technology",
                    "region": "US",
                    "return": 150.00,
                    "return_percent": 10.00
                },
                {
                    "symbol": "TSM",
                    "name": "Taiwan Semiconductor",
                    "shares": 20,
                    "avg_cost": 100.00,
                    "current_value": 2200.00,
                    "sector": "Semiconductors",
                    "region": "Asia",
                    "return": 200.00,
                    "return_percent": 10.00
                }
            ]
            
            os.makedirs(os.path.dirname(portfolio_file), exist_ok=True)
            with open(portfolio_file, "w") as f:
                json.dump(default_portfolio, f, indent=2)
            
            return default_portfolio

        try:
            with open(portfolio_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading portfolio: {e}")
            return []

    def search_portfolio(self, query: str, limit: int = 10) -> Dict:
        """Search portfolio based on query"""
        query_lower = query.lower().strip()
        
        # Handle empty or general queries
        if not query_lower or query_lower in ["portfolio", "all", "overview", "summary"]:
            return self._get_portfolio_summary()

        # Search filters
        matching_entries = []
        for entry in self.portfolio_data:
            if self._matches_query(entry, query_lower):
                matching_entries.append(entry)

        # Limit results
        matching_entries = matching_entries[:limit]

        # Calculate summary for filtered results
        if matching_entries:
            total_value = sum(entry.get("current_value", 0) for entry in matching_entries)
            total_return = sum(entry.get("return", 0) for entry in matching_entries)
            
            summary = f"Found {len(matching_entries)} matching holdings. Total value: ${total_value:,.2f}, Total return: ${total_return:,.2f}"
        else:
            summary = f"No holdings found matching '{query}'"

        return {
            "documents": matching_entries,
            "summary": summary,
            "count": len(matching_entries),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _matches_query(self, entry: Dict, query: str) -> bool:
        """Check if entry matches search query"""
        searchable_fields = ["symbol", "name", "sector", "region"]
        
        for field in searchable_fields:
            if field in entry and query in str(entry[field]).lower():
                return True
        
        return False

    def _get_portfolio_summary(self) -> Dict:
        """Get complete portfolio summary"""
        if not self.portfolio_data:
            return {
                "documents": [],
                "summary": "No portfolio data available",
                "count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        total_value = sum(entry.get("current_value", 0) for entry in self.portfolio_data)
        total_return = sum(entry.get("return", 0) for entry in self.portfolio_data)
        total_cost = sum(entry.get("shares", 0) * entry.get("avg_cost", 0) for entry in self.portfolio_data)
        
        return_percent = (total_return / total_cost * 100) if total_cost > 0 else 0

        summary = f"Portfolio Overview: {len(self.portfolio_data)} holdings, Total value: ${total_value:,.2f}, Total return: ${total_return:,.2f} ({return_percent:.1f}%)"

        return {
            "documents": self.portfolio_data,
            "summary": summary,
            "count": len(self.portfolio_data),
            "total_value": total_value,
            "total_return": total_return,
            "return_percent": round(return_percent, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

portfolio_retriever = PortfolioRetriever()

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(request: RetrieveRequest):
    """Retrieve portfolio documents based on query"""
    try:
        result = portfolio_retriever.search_portfolio(request.query, request.limit)
        
        return RetrieveResponse(
            documents=result["documents"],
            summary=result["summary"],
            count=result["count"]
        )
        
    except Exception as e:
        print(f"❌ Error in retriever_agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "retriever_agent"}