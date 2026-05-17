from mcp.server.fastmcp import FastMCP
import httpx
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

# --- STRUCTURED OUTPUT SCHEMAS ---
class AnalysisSchema(BaseModel):
    tech_persona: str = Field(description="1-2 sentence high-level technical analysis")
    complexity_score: int = Field(description="Overall technical complexity score (1-100)")
    next_level_recommendation: str = Field(description="A specific framework or skill to learn next")
    repo_count: int = Field(description="The number of public repositories")
    top_languages: List[str] = Field(description="List of top 3 programming languages used")
    career_time_travel: str = Field(description="A 1-sentence prediction of their profile in 2 years")
    avatar_url: str = Field(description="The GitHub avatar URL provided in the data")

# Initialize FastMCP server
mcp = FastMCP("GitHubDevCard")

# Configure Gemini
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub statistics for a given username."""
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    async with httpx.AsyncClient() as client_httpx:
        # User info
        user_resp = await client_httpx.get(f"https://api.github.com/users/{username}", headers=headers)
        if user_resp.status_code != 200:
            return {"error": f"User {username} not found"}
        user_data = user_resp.json()

        # Repos
        repos_resp = await client_httpx.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100")
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []

    # Parse languages
    languages = {}
    for r in repos_data:
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    top_3_langs = [l[0] for l in sorted_langs[:3]]

    return {
        "name": user_data.get("name"),
        "bio": user_data.get("bio"),
        "location": user_data.get("location"),
        "public_repos": user_data.get("public_repos", 0),
        "followers": user_data.get("followers", 0),
        "avatar_url": user_data.get("avatar_url"),
        "top_languages": top_3_langs
    }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data for Neural Career metrics and return specialized tech analysis."""
    
    prompt = f"""
    Analyze this GitHub profile data for a "Neural Career Decoder" report.
    Base your analysis STRICTLY on the provided repositories, languages, and activity.
    
    Data: {json.dumps(github_data)}
    """
    
    # FORCED STRUCTURED OUTPUT: Gemini will only return JSON matching AnalysisSchema
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnalysisSchema
        )
    )
    
    # Return as a dict for the MCP tool interface
    return json.loads(response.text)

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained Cyberpunk HTML dev card with Neural features."""
    complexity = analysis.get("complexity_score", 50)
    repos = analysis.get("repo_count", 0)
    langs = ", ".join(analysis.get("top_languages", ["N/A"]))
    
    html = f"""
    <div class="card-to-capture w-[340px] p-8 rounded-2xl border-2 border-magenta-500 bg-slate-950 text-cyan-400 font-mono shadow-[0_0_30px_rgba(34,211,238,0.2)] hover:scale-[1.02] transition-transform duration-500">
        <div class="flex items-center mb-8 border-b border-magenta-500/30 pb-6">
            <img src="{analysis.get('avatar_url')}" crossOrigin="anonymous" class="w-20 h-20 rounded-xl border-2 border-cyan-400 mr-4 shadow-[0_0_15px_rgba(34,211,238,0.4)] bg-slate-900" onerror="this.src='https://api.dicebear.com/7.x/identicon/svg?seed={username}'">
            <div>
                <h1 class="text-xl font-black tracking-tighter uppercase leading-none">{github_data.get('name') or username}</h1>
                <p class="text-[10px] text-magenta-400 mt-2 italic font-bold">UPLINK_STABLE // @{username}</p>
            </div>
        </div>
        
        <div class="mb-8">
            <h2 class="text-[10px] uppercase text-magenta-500 mb-2 tracking-widest font-black flex items-center gap-2">
                <span class="w-1.5 h-1.5 bg-magenta-500 rounded-full animate-pulse"></span>
                Tech Persona
            </h2>
            <p class="text-xs leading-relaxed text-slate-200">{analysis.get('tech_persona')}</p>
        </div>

        <div class="mb-8">
            <div class="flex justify-between text-[10px] uppercase mb-2 font-bold">
                <span>Neural Complexity</span>
                <span class="text-magenta-400">{complexity}%</span>
            </div>
            <div class="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-magenta-500/20 p-[2px]">
                <div class="bg-gradient-to-r from-cyan-500 via-blue-500 to-magenta-500 h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(217,70,239,0.5)]" style="width: {complexity}%"></div>
            </div>
        </div>

        <div class="mb-8 grid grid-cols-2 gap-4 text-center">
            <div class="p-3 border border-cyan-500/20 bg-cyan-500/5 rounded-lg">
                <div class="text-[8px] opacity-60 uppercase tracking-widest">Repos</div>
                <div class="text-sm font-black text-white">{repos}</div>
            </div>
            <div class="p-3 border border-blue-500/20 bg-blue-500/5 rounded-lg">
                <div class="text-[8px] opacity-60 uppercase tracking-widest">Stack</div>
                <div class="text-[10px] font-black text-white truncate">{langs}</div>
            </div>
        </div>

        <div class="p-4 border border-cyan-400/50 bg-cyan-400/5 rounded-xl shadow-[inset_0_0_10px_rgba(34,211,238,0.1)]">
            <h2 class="text-[10px] uppercase text-cyan-300 mb-1 font-black tracking-widest">Next Evolution</h2>
            <p class="text-[11px] text-white uppercase font-bold tracking-tight">{analysis.get('next_level_recommendation')}</p>
        </div>

        <div class="mt-8 pt-4 border-t border-magenta-500/30">
             <div class="text-[9px] text-slate-400 leading-snug italic">
                <span class="text-magenta-500 font-bold uppercase mr-1">TimeTravel_2028:</span>
                "{analysis.get('career_time_travel')}"
            </div>
        </div>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the HTML card to a static file."""
    base_dir = Path(__file__).parent
    path = base_dir / "static" / "cards" / f"{username}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;800&display=swap');
            body {{ 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                background: transparent; 
                margin: 0;
                font-family: 'JetBrains Mono', monospace;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
