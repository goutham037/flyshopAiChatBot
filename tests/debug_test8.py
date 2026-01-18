
import httpx
import json
import asyncio

API_URL = "http://127.0.0.1:8000/mvp/query"

async def debug_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Debugging Test #8: 'Show quotation details for FS1234' (+919999999999)")
        payload = {
            "mobile": "+919999999999",
            "query": "Show quotation details for FS1234"
        }
        response = await client.post(API_URL, json=payload)
        print("Status:", response.status_code)
        print("Response:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(debug_test())
