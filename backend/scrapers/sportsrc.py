import os
import httpx
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

BASE_URL = "https://streamed.pk/"

async def fetch_sportsrc_data(endpoint_type: str, match_id: Optional[str] = None, extra_params: Optional[Dict[str, Any]] = None) -> Any:
    if endpoint_type == "matches":
        # Fetch from streamed.pk/api/matches/live
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.get(f"{BASE_URL}api/matches/live")
                if response.status_code == 200:
                    matches = response.json()
                    # Map to the format the TV app expects: id, title, status, sport, date
                    mapped_matches = []
                    for m in matches:
                        mapped_matches.append({
                            "id": m.get("id", ""),
                            "title": m.get("title", ""),
                            "status": "inprogress",
                            "sport": m.get("category", "football"),
                            "date": str(m.get("date", ""))
                        })
                    return mapped_matches
        except Exception as e:
            logger.error(f"Error fetching live matches from streamed.pk: {e}")
            return []

    elif endpoint_type == "detail" and match_id:
        # 1. Fetch live matches to find this match's sources
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.get(f"{BASE_URL}api/matches/live")
                if response.status_code != 200:
                    return {"id": match_id, "title": "Error", "hls_url": ""}
                
                matches = response.json()
                match_data = next((m for m in matches if m.get("id") == match_id), None)
                if not match_data:
                    return {"id": match_id, "title": "Match not found/ended", "hls_url": ""}
                
                sources = match_data.get("sources", [])
                if not sources:
                    return {"id": match_id, "title": match_data.get("title", ""), "hls_url": "", "streams": []}
                
                # Fetch streams from all sources concurrently
                async def fetch_source_streams(src):
                    s_name = src.get("source")
                    s_id = src.get("id")
                    try:
                        async with httpx.AsyncClient(timeout=10.0, verify=False) as client_s:
                            s_resp = await client_s.get(f"{BASE_URL}api/stream/{s_name}/{s_id}")
                            if s_resp.status_code == 200:
                                return s_name, s_resp.json()
                    except Exception as ex:
                        logger.warning(f"Error fetching streams for source {s_name}: {ex}")
                    return s_name, []

                tasks = [fetch_source_streams(src) for src in sources]
                results = await asyncio.gather(*tasks)

                all_streams = []
                for s_name, streams in results:
                    for stream in streams:
                        all_streams.append({
                            "streamNo": stream.get("streamNo", 1),
                            "language": f"{s_name.upper()} - {stream.get('language', 'English')}",
                            "hd": stream.get("hd", False),
                            "embedUrl": stream.get("embedUrl", ""),
                            "source": s_name
                        })

                if not all_streams:
                    return {"id": match_id, "title": match_data.get("title", ""), "hls_url": "", "streams": []}
                
                # Pick the first stream as default to resolve
                default_embed = all_streams[0]["embedUrl"]
                hls_url = await extract_hls_from_embed(default_embed)
                
                return {
                    "id": match_id,
                    "title": match_data.get("title", ""),
                    "stream_url": default_embed,
                    "hls_url": hls_url,
                    "streams": all_streams
                }
        except Exception as e:
            logger.error(f"Error fetching match details for {match_id}: {e}")
            return {"id": match_id, "title": "Error", "hls_url": "", "streams": []}

    # Fallback to simulated/mock data matching SportSRC v2.5 schema for stats, lineups etc
    return get_mock_data(endpoint_type, match_id, extra_params)

async def extract_hls_from_embed(embed_url: str) -> str:
    logger.info(f"Extracting HLS from embed: {embed_url}")
    captured = []
    
    async def on_request(request):
        url = request.url
        if ".m3u8" in url and url not in captured:
            captured.append(url)
            
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            # Inject navigator.webdriver override to bypass simple bot checks
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            page = await context.new_page()
            page.on("request", on_request)
            
            try:
                await page.goto(embed_url, wait_until="domcontentloaded", timeout=15000)
            except Exception as e:
                logger.warning(f"Playwright navigation warning: {e}")
                
            # Wait for requests to settle or HLS to be found
            for _ in range(8):
                if captured:
                    break
                await asyncio.sleep(1)
                
            await context.close()
            await browser.close()
    except Exception as e:
        logger.error(f"Playwright HLS extraction failed: {e}")
        
    if captured:
        logger.info(f"Successfully extracted HLS URL: {captured[0]}")
        return captured[0]
        
    logger.warning(f"Failed to extract HLS from {embed_url}")
    return ""

def get_mock_data(endpoint_type: str, match_id: Optional[str] = None, extra_params: Optional[Dict[str, Any]] = None) -> Any:
    # Use fallback mock data for testing UI and endpoints
    match_id = match_id or "arsenal-vs-chelsea-101"
    
    if endpoint_type == "matches":
        all_matches = [
            {
                "id": "arsenal-vs-chelsea-101",
                "title": "Arsenal vs Chelsea",
                "status": "inprogress",
                "sport": "football",
                "date": "2026-07-01"
            },
            {
                "id": "real-madrid-vs-barcelona-102",
                "title": "Real Madrid vs Barcelona",
                "status": "upcoming",
                "sport": "football",
                "date": "2026-07-01"
            }
        ]
        status_filter = (extra_params or {}).get("status")
        if status_filter:
            return [m for m in all_matches if m["status"] == status_filter]
        return all_matches
        
    elif endpoint_type == "detail":
        return {
            "id": match_id,
            "title": "Arsenal vs Chelsea",
            "venue": "Emirates Stadium",
            "referee": "Michael Oliver",
            "stream_url": "https://virtualinfrastructure.space/player/html/1",
            "hls_url": "https://kamfir2.space/hls/stream.m3u8"
        }
        
    elif endpoint_type == "scores":
        return [
            {
                "id": "arsenal-vs-chelsea-101",
                "title": "Arsenal vs Chelsea",
                "has_stream": True,
                "has_standing": True
            },
            {
                "id": "real-madrid-vs-barcelona-102",
                "title": "Real Madrid vs Barcelona",
                "has_stream": True,
                "has_standing": True
            }
        ]
        
    elif endpoint_type == "lineups":
        return {
            "home": {
                "formation": "4-3-3",
                "players": [
                    {"name": "David Raya", "photo": "https://placehold.co/100x100?text=Raya"},
                    {"name": "Ben White", "photo": "https://placehold.co/100x100?text=White"},
                    {"name": "William Saliba", "photo": "https://placehold.co/100x100?text=Saliba"},
                    {"name": "Gabriel", "photo": "https://placehold.co/100x100?text=Gabriel"},
                    {"name": "Jurrien Timber", "photo": "https://placehold.co/100x100?text=Timber"},
                    {"name": "Declan Rice", "photo": "https://placehold.co/100x100?text=Rice"},
                    {"name": "Thomas Partey", "photo": "https://placehold.co/100x100?text=Partey"},
                    {"name": "Martin Odegaard", "photo": "https://placehold.co/100x100?text=Odegaard"},
                    {"name": "Bukayo Saka", "photo": "https://placehold.co/100x100?text=Saka"},
                    {"name": "Kai Havertz", "photo": "https://placehold.co/100x100?text=Havertz"},
                    {"name": "Gabriel Martinelli", "photo": "https://placehold.co/100x100?text=Martinelli"}
                ]
            },
            "away": {
                "formation": "4-2-3-1",
                "players": [
                    {"name": "Robert Sanchez", "photo": "https://placehold.co/100x100?text=Sanchez"},
                    {"name": "Malo Gusto", "photo": "https://placehold.co/100x100?text=Gusto"},
                    {"name": "Wesley Fofana", "photo": "https://placehold.co/100x100?text=Fofana"},
                    {"name": "Levi Colwill", "photo": "https://placehold.co/100x100?text=Colwill"},
                    {"name": "Marc Cucurella", "photo": "https://placehold.co/100x100?text=Cucurella"},
                    {"name": "Moises Caicedo", "photo": "https://placehold.co/100x100?text=Caicedo"},
                    {"name": "Enzo Fernandez", "photo": "https://placehold.co/100x100?text=Enzo"},
                    {"name": "Noni Madueke", "photo": "https://placehold.co/100x100?text=Madueke"},
                    {"name": "Cole Palmer", "photo": "https://placehold.co/100x100?text=Palmer"},
                    {"name": "Jadon Sancho", "photo": "https://placehold.co/100x100?text=Sancho"},
                    {"name": "Nicolas Jackson", "photo": "https://placehold.co/100x100?text=Jackson"}
                ]
            }
        }
        
    elif endpoint_type == "stats":
        return {
            "possession": {"home": "55%", "away": "45%"},
            "shots": {"home": 14, "away": 9},
            "xG": {"home": "1.74", "away": "0.98"},
            "shots_on_target": {"home": 6, "away": 3},
            "fouls": {"home": 10, "away": 12},
            "corners": {"home": 8, "away": 4}
        }
        
    elif endpoint_type == "incidents":
        return [
            {"time": "12'", "type": "goal", "player": "Bukayo Saka", "team": "home"},
            {"time": "24'", "type": "card", "player": "Wesley Fofana", "detail": "Yellow Card", "team": "away"},
            {"time": "58'", "type": "goal", "player": "Cole Palmer", "team": "away"},
            {"time": "72'", "type": "substitution", "player": "Martinelli out, Trossard in", "team": "home"}
        ]
        
    elif endpoint_type == "h2h":
        return {
            "matches": [
                {"date": "2025-11-10", "score": "2-1", "winner": "Arsenal"},
                {"date": "2025-04-23", "score": "5-0", "winner": "Arsenal"},
                {"date": "2024-10-21", "score": "2-2", "winner": "Draw"}
            ]
        }
        
    elif endpoint_type == "standing":
        return [
            {"position": 1, "team": "Arsenal", "points": 88},
            {"position": 2, "team": "Man City", "points": 86},
            {"position": 3, "team": "Chelsea", "points": 79},
            {"position": 4, "team": "Liverpool", "points": 78}
        ]
        
    elif endpoint_type == "graph":
        return {
            "home": [15, 25, 10, -5, -20, 5, 30, 45, 10, -15],
            "away": [-15, -25, -10, 5, 20, -5, -30, -45, -10, 15]
        }
        
    elif endpoint_type == "odds":
        return {
            "bookmaker": "Bet365",
            "decimal": {"home": 1.85, "draw": 3.60, "away": 4.10},
            "fractional": {"home": "17/20", "draw": "13/5", "away": "31/10"}
        }
        
    elif endpoint_type == "votes":
        return {
            "winner": {"home": "58%", "draw": "17%", "away": "25%"},
            "btts": {"yes": "65%", "no": "35%"}
        }
        
    elif endpoint_type == "shotmap":
        return [
            {"player": "Bukayo Saka", "x": 88.5, "y": 42.1, "xg": 0.35, "result": "goal"},
            {"player": "Cole Palmer", "x": 12.4, "y": 55.2, "xg": 0.15, "result": "saved"},
            {"player": "Kai Havertz", "x": 75.3, "y": 38.8, "xg": 0.08, "result": "blocked"}
        ]
        
    elif endpoint_type == "highlights":
        return {
            "title": "Arsenal vs Chelsea Highlights",
            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
        
    elif endpoint_type == "last_matches":
        return {
            "home": [
                {"id": "ars-1", "title": "Arsenal vs Man City", "score": "1-0"},
                {"id": "ars-2", "title": "Arsenal vs Bayern", "score": "2-2"}
            ],
            "away": [
                {"id": "che-1", "title": "Chelsea vs Spurs", "score": "2-2"},
                {"id": "che-2", "title": "Chelsea vs Newcastle", "score": "3-2"}
            ]
        }
        
    return {}
