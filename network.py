import aiohttp

QUOTE_URL = "https://workout-api-sepia.vercel.app/"


async def fetch_quote() -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(QUOTE_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                return "Could not fetch a quote."
    except Exception as e:
        return f"Network error: {e}"
