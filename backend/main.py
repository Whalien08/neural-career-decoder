from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uvicorn
from pathlib import Path
import asyncio
import time
import random
import httpx
import re
import textwrap
from datetime import datetime

# Mock ADK stubs
try:
    from google_adk import Runner, InMemorySessionService, InMemoryMemoryService
except ImportError:
    class InMemorySessionService: pass
    class InMemoryMemoryService: pass
    class Runner:
        def __init__(self, agent, session_service, memory_service):
            self.agent = agent
        async def run(self, session_id, message):
            return await self.agent.process_request(session_id)

from agent import github_card_agent

app = FastAPI(title="GitHub Dev Card Generator API")

MOCK_MODE = True
user_cache = {}
CACHE_TTL = 600

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(agent=github_card_agent, session_service=session_service, memory_service=memory_service)

STATIC_DIR = Path(__file__).parent / "static" / "cards"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

class GenerateRequest(BaseModel):
    username: str

async def get_clean_bio(client_httpx, username, api_bio):
    # Tier 1: Real GitHub Bio (Prioritized)
    if api_bio and str(api_bio).strip():
        return api_bio.strip()
        
    # Tier 2: Smart README Scrape
    for branch in ['main', 'master']:
        try:
            url = f'https://raw.githubusercontent.com/{username}/{username}/{branch}/README.md'
            res = await client_httpx.get(url, timeout=3.0)
            if res.status_code == 200:
                # Split by lines to find the first actual paragraph
                lines = res.text.split('\n')
                for line in lines:
                    # Clean markdown links, HTML, and headers
                    clean_line = re.sub(r'!\[.*?\]\(.*?\)|<[^>]+>|#+\s', '', line).strip()
                    # If it's an actual sentence (more than 30 chars), use it
                    if len(clean_line) > 30:
                        return clean_line[:147] + '...' if len(clean_line) > 150 else clean_line
        except Exception:
            continue
            
    # Tier 3: Fallback
    return 'Data Unavailable: No public bio provided by user.'

def get_alignment(languages):
    """Aggregate languages into 10 industry-standard domains."""
    domains = {
        "AI & Data Science": 0,
        "Full-Stack & Web": 0,
        "Backend & Core Systems": 0,
        "Mobile Development": 0,
        "DevOps & Infrastructure": 0,
        "Security & Info Assurance": 0,
        "Embedded & Aerospace": 0,
        "Cloud & Data Engineering": 0,
        "Game Development": 0,
        "Blockchain & Web3": 0
    }
    
    mapping = {
        "Python": "AI & Data Science", "R": "AI & Data Science", "Julia": "AI & Data Science", "Jupyter Notebook": "AI & Data Science",
        "JavaScript": "Full-Stack & Web", "TypeScript": "Full-Stack & Web", "HTML": "Full-Stack & Web", "CSS": "Full-Stack & Web", "React": "Full-Stack & Web",
        "C": "Backend & Core Systems", "C++": "Backend & Core Systems", "Rust": "Backend & Core Systems", "Go": "Backend & Core Systems", "Java": "Backend & Core Systems", "C#": "Backend & Core Systems",
        "Kotlin": "Mobile Development", "Swift": "Mobile Development", "Dart": "Mobile Development", "Objective-C": "Mobile Development",
        "Shell": "DevOps & Infrastructure", "PowerShell": "DevOps & Infrastructure", "HCL": "DevOps & Infrastructure", "Dockerfile": "DevOps & Infrastructure", "Ruby": "DevOps & Infrastructure",
        "Assembly": "Security & Info Assurance", "Bash": "Security & Info Assurance", "YARA": "Security & Info Assurance",
        "MATLAB": "Embedded & Aerospace", "VHDL": "Embedded & Aerospace", "Verilog": "Embedded & Aerospace",
        "SQL": "Cloud & Data Engineering", "Scala": "Cloud & Data Engineering", "Hadoop": "Cloud & Data Engineering", "Spark": "Cloud & Data Engineering",
        "Unity": "Game Development", "Unreal": "Game Development", "GDScript": "Game Development", "Lua": "Game Development",
        "Solidity": "Blockchain & Web3"
    }
    
    total = sum(languages.values()) if languages else 0
    if total == 0: return domains
    
    for lang, count in languages.items():
        domain = mapping.get(lang)
        if domain:
            domains[domain] += (count / total) * 100
            
    return {k: round(v, 1) for k, v in domains.items()}

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    current_time = time.time()
    
    if request.username in user_cache:
        data, timestamp = user_cache[request.username]
        if current_time - timestamp < CACHE_TTL:
            return data

    github_data = {"name": request.username, "avatar_url": f"https://github.com/{request.username}.png", "public_repos": 0, "followers": 0, "created_at": "2024-01-01T00:00:00Z", "bio": None}
    top_languages = ["N/A"]
    raw_languages = {}
    stars_count = 0
    event_hours = []
    
    try:
        async with httpx.AsyncClient() as client_httpx:
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"token {token}"} if token else {}
            
            # 1. Profile Fetch
            resp = await client_httpx.get(f"https://api.github.com/users/{request.username}", headers=headers)
            if resp.status_code == 200:
                github_data = resp.json()
            
            # 2. Smart Bio Extraction
            github_data["bio"] = await get_clean_bio(client_httpx, request.username, github_data.get("bio"))

            # 3. Repos & Languages
            repos_resp = await client_httpx.get(f"https://api.github.com/users/{request.username}/repos?sort=updated&per_page=100", headers=headers)
            if repos_resp.status_code == 200:
                repos_list = repos_resp.json()
                for r in repos_list:
                    l = r.get("language")
                    if l: raw_languages[l] = raw_languages.get(l, 0) + 1
                    stars_count += r.get("stargazers_count", 0)
                sorted_langs = sorted(raw_languages.items(), key=lambda x: x[1], reverse=True)
                top_languages = [l[0] for l in sorted_langs[:3]]

            # 4. Events
            events_resp = await client_httpx.get(f"https://api.github.com/users/{request.username}/events/public", headers=headers)
            if events_resp.status_code == 200:
                for event in events_resp.json():
                    try:
                        hour = int(event["created_at"][11:13])
                        event_hours.append(hour)
                    except: pass
    except Exception: pass

    repos = github_data.get("public_repos", 0)
    followers = github_data.get("followers", 0)
    created_at_str = github_data.get("created_at") or "2024-01-01T00:00:00Z"
    created_at = datetime.strptime(created_at_str[:10], "%Y-%m-%d")
    account_years = (datetime.now() - created_at).days / 365
    
    if event_hours:
        morning = sum(1 for h in event_hours if 6 <= h < 12)
        afternoon = sum(1 for h in event_hours if 12 <= h < 18)
        evening = sum(1 for h in event_hours if 18 <= h < 23)
        night = sum(1 for h in event_hours if h >= 23 or h < 5)
        counts = {"Morning Developer": morning, "Mid-Day Specialist": afternoon, "Evening Architect": evening, "Night Owl": night}
        chronos = max(counts, key=counts.get)
    else:
        chronos = "Standard Cycle"

    bounty = 500 + (repos * 25) + (followers * 100) + (stars_count * 250)

    is_elite = followers > 5000 or request.username.lower() == 'torvalds'
    if is_elite:
        persona = "Kernel Overlord"
        translation = "Level 3: Cybernetic Deity // Core Architect"
        complexity = 99
        evolution = "System complete."
        quote = "I am the architect of the foundations."
    else:
        complexity = min(99, 45 + (repos * 2) + (followers // 3))
        main_lang = top_languages[0] if top_languages and top_languages[0] != "N/A" else "General"
        mapping = {
            "Python": ("AI Latent Architect", "Level 2: Neural Specialist"),
            "JavaScript": ("Web Matrix Vanguard", "Level 2: Frontend Synthesis"),
            "General": ("Cybernetic Polymath", "Level 2: Full-Stack Node")
        }
        persona, translation = mapping.get(main_lang, mapping["General"])
        evolution = f"Scale existing {repos} data nodes."
        quote = "Neural pathways forming."

    response_payload = {
        "status": "success",
        "username": request.username,
        "public_name": github_data.get("name") or request.username,
        "repos": repos,
        "followers": followers,
        "stars": stars_count,
        "languages": top_languages,
        "persona": persona,
        "translation": translation,
        "complexity": complexity,
        "evolution": evolution,
        "avatar": github_data.get("avatar_url"),
        "bio": github_data.get("bio"),
        "quote": quote,
        "chronos": chronos,
        "bounty": f"{bounty:,}",
        "alignments": get_alignment(raw_languages),
        "card_url": f"/card/{request.username}"
    }
    
    user_cache[request.username] = (response_payload, current_time)
    return response_payload

@app.get("/card/{username}")
async def get_card(username: str):
    card_path = STATIC_DIR / f"{username}.html"
    if not card_path.exists(): raise HTTPException(status_code=404)
    with open(card_path, "r", encoding="utf-8") as f: return f.read()

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
