

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import numpy as np
from datetime import datetime

class AnalysisRequest(BaseModel):
    market_data: Dict

class AnalysisResponse(BaseModel):
    analysis: Dict
    summary: str

app = FastAPI(title="Analysis Agent", description="Performs risk and diversification analysis")

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_market(request: AnalysisRequest):
    """Analyze portfolio risk and diversification metrics"""
    try:
        data = request.market_data
        if not data:
            raise ValueError("No market data provided")

        # Calculate portfolio metrics
        prices = []
        sectors = {}
        regions = {}
        
        for symbol, info in data.items():
            if isinstance(info, dict) and "current_price" in info:
                prices.append(info["current_price"])
                
                # Sector analysis (mock data - in production, get from company info API)
                sector = info.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + info["current_price"]
                
                # Regional analysis
                region = info.get("region", "US")
                regions[region] = regions.get(region, 0) + info["current_price"]

        if not prices:
            return AnalysisResponse(
                analysis={
                    "total_exposure": 0,
                    "sector_diversification": 0,
                    "regional_diversification": 0,
                    "risk_score": 0,
                    "volatility": 0
                },
                summary="No valid market data available for analysis"
            )

        # Calculate metrics
        total_exposure = sum(prices)
        sector_count = len(sectors)
        region_count = len(regions)
        
        # Risk metrics
        volatility = np.std(prices) / np.mean(prices) if len(prices) > 1 else 0
        risk_score = min(volatility * 10, 10)  # Scale to 0-10
        
        # Diversification ratios
        sector_div = min(sector_count / 10, 1.0)  # Ideal: 10+ sectors
        regional_div = min(region_count / 5, 1.0)  # Ideal: 5+ regions

        analysis = {
            "total_exposure": round(total_exposure, 2),
            "sector_diversification": round(sector_div, 2),
            "regional_diversification": round(regional_div, 2),
            "risk_score": round(risk_score, 2),
            "volatility": round(volatility * 100, 2),
            "sector_breakdown": sectors,
            "regional_breakdown": regions,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Generate summary
        risk_level = "Low" if risk_score < 3 else "Medium" if risk_score < 7 else "High"
        summary = f"{risk_level} risk portfolio with {sector_count} sectors and {region_count} regions. Volatility: {volatility*100:.1f}%"

        return AnalysisResponse(analysis=analysis, summary=summary)

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analysis_agent"}

