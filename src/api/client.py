# API client skeleton
import aiohttp
import asyncio
import json
import logging

logger = logging.getLogger("mordor-api")

class MordorAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://relaxing-needed-vulture.ngrok-free.app/api"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.headers = {"Content-Type": "application/json"}

    async def authenticate(self) -> bool:
        """
        Exchange API key for a bearer token.
        """
        url = f"{self.base_url}/auth"
        payload = {"api_key": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.token = data.get("token")
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        logger.info("Authentication successful.")
                        return True
                    text = await resp.text()
                    logger.error(f"Auth failed {resp.status}: {text}")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"Auth request error: {e}")
            return False

    async def receive_transcripts(self):
        """
        Stream transcripts from the API as an async generator.
        """
        if not self.token:
            logger.error("Not authenticated. Call authenticate() first.")
            return
        url = f"{self.base_url}/v1/transcripts/stream"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Stream failed {resp.status}: {text}")
                        return
                    async for line in resp.content:
                        if not line:
                            continue
                        try:
                            yield json.loads(line.decode('utf-8'))
                        except json.JSONDecodeError as je:
                            logger.error(f"JSON parse error: {je}")
        except aiohttp.ClientError as e:
            logger.error(f"Stream connection error: {e}")

    async def submit_processed_result(self, result: dict) -> dict:
        """
        Submit processed transcript result back to API.
        """
        if not self.token:
            logger.error("Not authenticated. Call authenticate() first.")
            return {"error": "Not authenticated"}
        url = f"{self.base_url}/v1/transcripts/process"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=result) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Submit failed {resp.status}: {text}")
                        return {"error": text}
                    return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"Submit request error: {e}")
            return {"error": str(e)}

    async def get_stats(self) -> dict:
        """
        Retrieve processing statistics from the API.
        """
        if not self.token:
            logger.error("Not authenticated. Call authenticate() first.")
            return {"error": "Not authenticated"}
        url = f"{self.base_url}/v1/stats"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Stats failed {resp.status}: {text}")
                        return {"error": text}
                    return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"Stats request error: {e}")
            return {"error": str(e)}
