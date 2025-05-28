

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import openai
from openai import AsyncOpenAI
from config.settings import settings

class LanguageRequest(BaseModel):
    market_data: Dict
    analysis_results: Dict
    retrieved_documents: List[Dict]
    query: str
    response_type: str = "brief"

class LanguageResponse(BaseModel):
    response: str
    confidence: float
    sources: List[str]
    reasoning: str

app = FastAPI(title="Language Agent", description="Enhanced LLM synthesis agent")

class LanguageService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def generate_response(self, request: LanguageRequest) -> LanguageResponse:
        """Generate intelligent response using market data and analysis"""
        if not self.client:
            return LanguageResponse(
                response="OpenAI API key not configured",
                confidence=0.0,
                sources=[],
                reasoning="API unavailable"
            )

        context = self._prepare_context(
            request.market_data,
            request.analysis_results,
            request.retrieved_documents
        )

        system_prompt = """You are a professional financial analyst AI. Provide accurate, 
        data-driven insights based on real market data. Be concise but comprehensive.
        Always mention data sources and confidence levels."""

        user_prompt = f"""
        Query: {request.query}
        
        Market Data: {context['market']}
        Analysis: {context['analysis']}
        Documents: {context['documents']}
        
        Response type: {request.response_type}
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300 if request.response_type == "brief" else 800,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            
            return LanguageResponse(
                response=content,
                confidence=0.85,
                sources=self._extract_sources(request.retrieved_documents),
                reasoning="Analysis based on live market data and portfolio analysis"
            )

        except Exception as e:
            return LanguageResponse(
                response=f"Unable to generate response: {str(e)}",
                confidence=0.0,
                sources=[],
                reasoning="API error"
            )

    def _prepare_context(self, market_data: Dict, analysis_results: Dict, documents: List[Dict]) -> Dict:
        """Prepare structured context for LLM"""
        context = {"market": "", "analysis": "", "documents": ""}
        
        # Market data context
        if market_data:
            market_summary = []
            for symbol, data in market_data.items():
                if isinstance(data, dict) and "current_price" in data:
                    change = data.get("change", 0)
                    change_pct = data.get("change_percent", 0)
                    market_summary.append(f"{symbol}: ${data['current_price']:.2f} ({change:+.2f}, {change_pct:+.1f}%)")
            context["market"] = "; ".join(market_summary)

        # Analysis context
        if analysis_results:
            analysis = analysis_results.get("analysis", {})
            context["analysis"] = f"Risk Score: {analysis.get('risk_score', 'N/A')}, Volatility: {analysis.get('volatility', 'N/A')}%, Diversification: {analysis.get('sector_diversification', 'N/A')}"

        # Documents context
        if documents:
            doc_summaries = []
            for doc in documents[:3]:
                content = doc.get("content", "")[:150]
                if content:
                    doc_summaries.append(content + "...")
            context["documents"] = "; ".join(doc_summaries)

        return context

    def _extract_sources(self, docs: List[Dict]) -> List[str]:
        """Extract source information from documents"""
        sources = []
        for doc in docs[:5]:
            if isinstance(doc, dict):
                metadata = doc.get("metadata", {})
                if "source" in metadata:
                    sources.append(metadata["source"])
                elif "url" in metadata:
                    sources.append(metadata["url"])
        return sources

language_service = LanguageService()

@app.post("/synthesize", response_model=LanguageResponse)
async def synthesize_response(request: LanguageRequest):
    """Generate intelligent response using market data and analysis"""
    try:
        return await language_service.generate_response(request)
    except Exception as e:
        print(f"❌ Language synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "language_agent"}