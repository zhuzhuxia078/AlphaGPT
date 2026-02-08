import aiohttp
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from ..config import Config
from .base import DataProvider

class BirdeyeProvider(DataProvider):
    def __init__(self):
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {
            "X-API-KEY": Config.BIRDEYE_API_KEY,
            # 指定链，否则部分接口会返回 400
            "x-chain": Config.CHAIN,
            "accept": "application/json"
        }
        self.semaphore = asyncio.Semaphore(Config.CONCURRENCY)

    async def get_trending_tokens(self, limit=20):
        url = f"{self.base_url}/defi/token_trending"
        params = {
            "sort_by": "rank",
            "sort_type": "asc",
            "offset": "0",
            "limit": str(limit)
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_list = data.get('data', {}).get('tokens', [])

                        results = []
                        for t in raw_list:
                            results.append({
                                'address': t['address'],
                                'symbol': t.get('symbol', 'UNKNOWN'),
                                'name': t.get('name', 'UNKNOWN'),
                                'decimals': t.get('decimals', 6),
                                'liquidity': t.get('liquidity', 0),
                                'fdv': t.get('fdv', 0)
                            })
                        return results
                    else:
                        try:
                            body = await resp.text()
                        except Exception:
                            body = "<no body>"
                        logger.error(f"Birdeye Trending Error: {resp.status} | body={body}")
                        return []
            except Exception as e:
                logger.error(f"Birdeye Trending Exception: {e}")
                return []

    async def get_token_history(self, session, address, days=Config.HISTORY_DAYS):
        # Birdeye单次返回约 1000 条，长时间段需要分页，否则只能拿到早期数据。
        seconds_per_bar = 60 if Config.TIMEFRAME == "1m" else 900  # 15min=900s
        chunk_bars = 900  # 每段最多抓 900 根，防止超过上限
        chunk_seconds = seconds_per_bar * chunk_bars

        time_to = int(datetime.now().timestamp())
        time_from = int((datetime.now() - timedelta(days=days)).timestamp())

        url = f"{self.base_url}/defi/ohlcv"
        current_from = time_from
        all_rows = []

        while current_from < time_to:
            current_to = min(time_to, current_from + chunk_seconds)
            params = {
                "address": address,
                "type": Config.TIMEFRAME,
                "time_from": current_from,
                "time_to": current_to
            }

            async with self.semaphore:
                try:
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            items = data.get('data', {}).get('items', [])
                            if items:
                                for item in items:
                                    all_rows.append((
                                        datetime.fromtimestamp(item['unixTime']),
                                        address,
                                        float(item['o']),
                                        float(item['h']),
                                        float(item['l']),
                                        float(item['c']),
                                        float(item['v']),
                                        0.0,
                                        0.0,
                                        'birdeye'
                                    ))
                        elif resp.status == 429:
                            logger.warning(f"Birdeye 429 for {address}, window {current_from}->{current_to}, retrying...")
                            await asyncio.sleep(2)
                            continue  # 重试同一窗口
                        else:
                            logger.error(f"Birdeye OHLCV Error {resp.status} for {address} window {current_from}->{current_to}")
                except Exception as e:
                    logger.error(f"Birdeye Fetch Error {address}: {e}")

            current_from = current_to  # 处理下一段

        return all_rows
