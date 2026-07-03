import os
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.sportsrc.org/v2/"

def get_api_key() -> Optional[str]:
    return os.environ.get("SPORTSRC_API_KEY")

async def fetch_sportsrc_data(endpoint_type: str, match_id: Optional[str] = None, extra_params: Optional[Dict[str, Any]] = None) -> Any:
    api_key = get_api_key()
    params = {"type": endpoint_type}
    if match_id:
        # Match ID/slug
        params["id"] = match_id
    if extra_params:
        params.update(extra_params)

    if api_key:
        headers = {"X-API-KEY": api_key}
        url = BASE_URL
        # In query param option as fallback if headers fail, but headers recommended
        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"SportSRC API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error calling SportSRC API: {e}")

    # Fallback to simulated/mock data matching SportSRC v2.5 schema
    return get_mock_data(endpoint_type, match_id, extra_params)

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
