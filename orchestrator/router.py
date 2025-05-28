import httpx

async def get_agent_response(service_name: str, endpoint: str, payload: dict):
    url = f"http://{service_name}:8000{endpoint}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"❌ Request error calling {url}: {e}")
        return {}
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error calling {url}: {e.response.status_code} - {e.response.text}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error calling {url}: {e}")
        return {}
