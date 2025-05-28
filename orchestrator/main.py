# # import asyncio
# # from fastapi import FastAPI, Request, HTTPException
# # import httpx

# # app = FastAPI()

# # async def get_agent_response(service_url: str, endpoint: str, payload: dict):
# #     url = f"{service_url}{endpoint}"
# #     try:
# #         async with httpx.AsyncClient() as client:
# #             response = await client.post(url, json=payload)
# #             response.raise_for_status()
# #             return response.json()
# #     except Exception as e:
# #         print(f"❌ Error calling {url}: {e}")
# #         return {}  # Return an empty dict if error occurs

# # @app.post("/process")
# # async def process_request(request: Request):
# #     try:
# #         body = await request.json()
# #         user_query = body.get("query", "What is the market outlook today?")
# #         symbols = body.get("symbols", ["AAPL", "TSLA"])

# #         # Step 1: Get market data
# #         market_data_response = await get_agent_response("http://localhost:8001", "/market-data", {"symbols": symbols})
# #         print("✅ Raw Market Data Response:", market_data_response)

# #         # If the API returns {'data': {...}} structure (old version)
# #         market_data = market_data_response.get("data", market_data_response)
# #         print("✅ Processed Market Data:", market_data)

# #         # Step 2: Get analysis results
# #         analysis_results = await get_agent_response("http://localhost:8004", "/analyze", {"market_data": market_data})
# #         print("✅ Analysis Results:", analysis_results)

# #         # Step 3: Retrieve documents
# #         documents = await get_agent_response("http://localhost:8003", "/retrieve", {"query": user_query})
# #         print("✅ Retrieved Documents:", documents)

# #         # Step 4: Call language agent to synthesize final response
# #         language_payload = {
# #             "market_data": market_data,
# #             "analysis_results": analysis_results,
# #             "retrieved_documents": documents if isinstance(documents, list) else [documents],
# #             "query": user_query,
# #             "response_type": "brief"
# #         }

# #         language_response = await get_agent_response("http://localhost:8005", "/synthesize", language_payload)
# #         print("✅ Final Language Response:", language_response)

# #         return {"response": language_response}

# #     except Exception as e:
# #         print(f"❌ Error in /process: {e}")
# #         raise HTTPException(status_code=500, detail=str(e))
# from time import perf_counter
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Dict, List, Optional
# import aiohttp
# import asyncio
# from datetime import datetime
# class OrchestrationRequest(BaseModel):
#     query: str
#     symbols: Optional[List[str]] = []
#     include_analysis: bool = True
#     include_news: bool = False
#     response_type: str = "brief"

# class OrchestrationResponse(BaseModel):
#     query: str
#     market_data: Dict
#     analysis: Dict
#     portfolio_data: Dict
#     news: List[Dict]
#     ai_response: Dict
#     timestamp: str
#     processing_time: Optional[float] = None  # ✅ Add this


# app = FastAPI(title="Trading Agent Orchestrator", description="Coordinates all trading agents")

# class AgentOrchestrator:
#     def __init__(self):
#        self.agent_urls = {
#     "retriever": "http://localhost:8001",
#     "analysis": "http://localhost:8002",
#     "api": "http://localhost:8003",
#     "language": "http://localhost:8004",
#     "scraping": "http://localhost:8005",
#     "voice": "http://localhost:8006"
# }


#     async def process_request(self, request: OrchestrationRequest) -> OrchestrationResponse:
#         """Orchestrate all agents to process a complete request"""
#         start_time = perf_counter()
#         # Step 1: Get portfolio data
#         portfolio_data = await self._call_retriever(request.query)
        
#         # Step 2: Get market data if symbols provided
#         market_data = {}
#         if request.symbols:
#             market_data = await self._call_api_agent(request.symbols)
        
#         # Step 3: Perform analysis if market data available
#         analysis = {}
#         if request.include_analysis and market_data:
#             analysis = await self._call_analysis_agent(market_data)
        
#         # Step 4: Get news if requested
#         news = []
#         if request.include_news and request.symbols:
#             for symbol in request.symbols:
#                 symbol_news = await self._call_scraping_agent(symbol, "news")
#                 news.extend(symbol_news.get("documents", []))
        
#         # Step 5: Generate AI response
#         ai_response = await self._call_language_agent(
#             market_data, analysis, portfolio_data.get("documents", []), 
#             request.query, request.response_type
#         )
        
#         duration = perf_counter() - start_time

#         response = OrchestrationResponse(
#           query=request.query,
#           market_data=market_data,
#           analysis=analysis,
#           portfolio_data=portfolio_data,
#           news=news,  # ← Add comma here
#           ai_response=ai_response,
#           timestamp=datetime.utcnow().isoformat()
# )


#     # Convert to dict and add timing info manually
#         response_dict = response.dict()
#         response_dict["processing_time"] = duration

#         return response_dict
#     async def _call_retriever(self, query: str) -> Dict:
#         """Call retriever agent"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     f"{self.agent_urls['retriever']}/retrieve",
#                     json={"query": query}
#                 ) as response:
#                     return await response.json() if response.status == 200 else {}
#         except:
#             return {}

#     async def _call_api_agent(self, symbols: List[str]) -> Dict:
#         """Call API agent for market data"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     f"{self.agent_urls['api']}/market-data",
#                     json={"symbols": symbols}
#                 ) as response:
#                     return await response.json() if response.status == 200 else {}
#         except:
#             return {}

#     async def _call_analysis_agent(self, market_data: Dict) -> Dict:
#         """Call analysis agent"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     f"{self.agent_urls['analysis']}/analyze",
#                     json={"market_data": market_data}
#                 ) as response:
#                     return await response.json() if response.status == 200 else {}
#         except:
#             return {}

#     async def _call_scraping_agent(self, symbol: str, source: str) -> Dict:
#         """Call scraping agent"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     f"{self.agent_urls['scraping']}/scrape",
#                     json={"target": symbol, "source": source, "limit": 5}
#                 ) as response:
#                     return await response.json() if response.status == 200 else {}
#         except:
#             return {}

#     async def _call_language_agent(self, market_data: Dict, analysis: Dict, 
#                                  documents: List[Dict], query: str, response_type: str) -> Dict:
#         """Call language agent"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     f"{self.agent_urls['language']}/synthesize",
#                     json={
#                         "market_data": market_data,
#                         "analysis_results": analysis,
#                         "retrieved_documents": documents,
#                         "query": query,
#                         "response_type": response_type
#                     }
#                 ) as response:
#                     return await response.json() if response.status == 200 else {}
#         except:
#             return {}

# orchestrator = AgentOrchestrator()

# @app.post("/process", response_model=OrchestrationResponse)
# async def process_trading_request(request: OrchestrationRequest):
#     """Process complete trading request using all agents"""
#     try:
#         return await orchestrator.process_request(request)
#     except Exception as e:
#         print(f"❌ Orchestration error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health_check():
#     """Check health of all agents"""
#     health_status = {}
    
#     for agent_name, url in orchestrator.agent_urls.items():
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
#                     if response.status == 200:
#                         health_status[agent_name] = "healthy"
#                     else:
#                         health_status[agent_name] = "unhealthy"
#         except:
#             health_status[agent_name] = "unreachable"
    
#     return {
#         "status": "healthy" if all(status == "healthy" for status in health_status.values()) else "degraded",
#         "agents": health_status,
#         "timestamp": datetime.utcnow().isoformat()
#     }
from time import perf_counter
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import aiohttp
import asyncio
from datetime import datetime

# ---------------- Models -------------------

class OrchestrationRequest(BaseModel):
    query: str
    symbols: Optional[List[str]] = []
    include_analysis: bool = True
    include_news: bool = False
    response_type: str = "brief"

class OrchestrationResponse(BaseModel):
    query: str
    market_data: Dict
    analysis: Dict
    portfolio_data: Dict
    news: List[Dict]
    ai_response: Dict
    timestamp: str
    processing_time: Optional[float] = None

# ---------------- App Setup -------------------

app = FastAPI(title="Trading Agent Orchestrator", description="Coordinates all trading agents")

# ---------------- Orchestrator -------------------

class AgentOrchestrator:
    def __init__(self):
        self.agent_urls = {
            "retriever": "http://localhost:8001",
            "analysis": "http://localhost:8002",
            "api": "http://localhost:8003",
            "language": "http://localhost:8004",
            "scraping": "http://localhost:8005",
            "voice": "http://localhost:8006"
        }

    async def process_request(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """Orchestrate all agents to process a complete request"""
        start_time = perf_counter()

        # Step 1: Get portfolio data
        portfolio_data = await self._call_retriever(request.query)

        # Step 2: Get market data if symbols are provided
        market_data = {}
        if request.symbols:
            market_data = await self._call_api_agent(request.symbols)

        # Step 3: Perform analysis
        analysis = {}
        if request.include_analysis and market_data:
            analysis = await self._call_analysis_agent(market_data)

        # Step 4: Get news
        news = []
        if request.include_news and request.symbols:
            for symbol in request.symbols:
                symbol_news = await self._call_scraping_agent(symbol, "news")
                news.extend(symbol_news.get("documents", []))

        # Step 5: AI response
        ai_response = await self._call_language_agent(
            market_data, analysis, portfolio_data.get("documents", []), 
            request.query, request.response_type
        )

        duration = perf_counter() - start_time

        return OrchestrationResponse(
            query=request.query,
            market_data=market_data,
            analysis=analysis,
            portfolio_data=portfolio_data,
            news=news,
            ai_response=ai_response,
            timestamp=datetime.utcnow().isoformat(),
            processing_time=round(duration, 3)
        )

    async def _call_retriever(self, query: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_urls['retriever']}/retrieve", json={"query": query}
                ) as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            print(f"❌ Retriever error: {e}")
            return {}

    async def _call_api_agent(self, symbols: List[str]) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_urls['api']}/market-data", json={"symbols": symbols}
                ) as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            print(f"❌ API Agent error: {e}")
            return {}

    async def _call_analysis_agent(self, market_data: Dict) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_urls['analysis']}/analyze", json={"market_data": market_data}
                ) as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            print(f"❌ Analysis Agent error: {e}")
            return {}

    async def _call_scraping_agent(self, symbol: str, source: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_urls['scraping']}/scrape",
                    json={"target": symbol, "source": source, "limit": 5}
                ) as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            print(f"❌ Scraping Agent error for {symbol}: {e}")
            return {}

    async def _call_language_agent(self, market_data: Dict, analysis: Dict, 
                                   documents: List[Dict], query: str, response_type: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_urls['language']}/synthesize",
                    json={
                        "market_data": market_data,
                        "analysis_results": analysis,
                        "retrieved_documents": documents,
                        "query": query,
                        "response_type": response_type
                    }
                ) as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            print(f"❌ Language Agent error: {e}")
            return {}

# ---------------- FastAPI Endpoints -------------------

orchestrator = AgentOrchestrator()

@app.post("/process", response_model=OrchestrationResponse)
async def process_trading_request(request: OrchestrationRequest):
    """Process complete trading request using all agents"""
    try:
        return await orchestrator.process_request(request)
    except Exception as e:
        print(f"❌ Orchestration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Check health of all agents"""
    health_status = {}
    for agent_name, url in orchestrator.agent_urls.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        health_status[agent_name] = "healthy"
                    else:
                        health_status[agent_name] = "unhealthy"
        except Exception as e:
            health_status[agent_name] = f"unreachable: {e}"

    return {
        "status": "healthy" if all(status == "healthy" for status in health_status.values()) else "degraded",
        "agents": health_status,
        "timestamp": datetime.utcnow().isoformat()
    }
