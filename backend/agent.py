import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp_server import mcp

load_dotenv()

SYSTEM_INSTRUCTION = """
You are the Neural Career Decoder, an advanced AI specialized in high-level technical profiling. 
When a user gives you a GitHub username, you ALWAYS follow this exact sequence: 
1. Call scrape_github
2. Call analyze_profile with the result
3. Call generate_card_html with the username, github_data, and analysis
4. Call save_card with the result

Strictly follow these technical constraints for analysis:
- Look for patterns in Computer Vision (OpenCV, PyTorch, etc.).
- Search for GAN (Generative Adversarial Networks) related repositories.
- Analyze System Architecture (Scalability, low-level optimization, design patterns).
- Provide a complexity_score (1-100), next_level_recommendation, skill_heatmap (CV, Backend, Frontend), career_time_travel (2-year prediction), and collaborator_synergy analysis.

Never skip steps. Be highly analytical, technical, and forward-looking. 
If the profile is private or doesn't exist, say so clearly.
"""

# Map function names to their implementations in mcp_server
TOOL_MAPPING = {
    "scrape_github": lambda **kwargs: mcp.call_tool("scrape_github", kwargs),
    "analyze_profile": lambda **kwargs: mcp.call_tool("analyze_profile", kwargs),
    "generate_card_html": lambda **kwargs: mcp.call_tool("generate_card_html", kwargs),
    "save_card": lambda **kwargs: mcp.call_tool("save_card", kwargs),
}

tools_spec = [
    {
        "function_declarations": [
            {
                "name": "scrape_github",
                "description": "Fetch GitHub statistics for a given username.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"}
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "analyze_profile",
                "description": "Analyze GitHub data for Neural Career metrics (CV, GANs, Sys Arch, Heatmap, Time-Travel).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "github_data": {"type": "object"}
                    },
                    "required": ["github_data"]
                }
            },
            {
                "name": "generate_card_html",
                "description": "Generate a self-contained Neural Cyberpunk HTML dev card.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "github_data": {"type": "object"},
                        "analysis": {"type": "object"}
                    },
                    "required": ["username", "github_data", "analysis"]
                }
            },
            {
                "name": "save_card",
                "description": "Save the HTML card to a static file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "html": {"type": "string"}
                    },
                    "required": ["username", "html"]
                }
            }
        ]
    }
]

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class GitHubCardAgent:
    def __init__(self):
        self.model_id = "gemini-2.0-flash"

    def _extract_content(self, tool_output):
        if isinstance(tool_output, list) and len(tool_output) > 0:
            if hasattr(tool_output[0], 'text'):
                content = tool_output[0].text
                try:
                    return json.loads(content)
                except:
                    return content
        return tool_output

    async def process_request(self, username: str):
        print(f"DEBUG: Starting Neural Decoding for {username}")
        chat = client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools_spec
            )
        )
        
        message = f"Execute Neural Career Decoding for user: {username}"
        response = chat.send_message(message)
        
        # Track the data the frontend needs!
        captured_analysis = {
            "tech_persona": "Latent patterns identified. Decoding persona...",
            "complexity_score": 50,
            "next_level_recommendation": "Continuity analysis required.",
            "skill_heatmap": {"computer_vision": 50, "backend": 50, "frontend": 50},
            "career_time_travel": "Timeline synchronizing...",
            "avatar_url": "https://github.com/identicons/github.png"
        }
        captured_url = f"/static/cards/{username}.html"
        
        max_iterations = 10
        for i in range(max_iterations):
            if not response.candidates or not response.candidates[0].content.parts:
                break
                
            parts = response.candidates[0].content.parts
            tool_calls = [p.function_call for p in parts if p.function_call]
            
            if not tool_calls:
                break
                
            tool_responses = []
            for call in tool_calls:
                func_name = call.name
                args = call.args
                
                try:
                    raw_result = await TOOL_MAPPING[func_name](**args)
                    result = self._extract_content(raw_result)
                    
                    # === THE UPGRADE: Eavesdrop on the tools ===
                    if func_name == "analyze_profile" and isinstance(result, dict):
                        captured_analysis.update(result)
                    elif func_name == "save_card" and isinstance(result, str):
                        captured_url = result
                    # ============================================

                    tool_responses.append(types.Part.from_function_response(
                        name=func_name,
                        response={"result": result}
                    ))
                except Exception as e:
                    print(f"Error calling tool {func_name}: {e}")
                    tool_responses.append(types.Part.from_function_response(
                        name=func_name,
                        response={"error": str(e)}
                    ))
            
            response = chat.send_message(tool_responses)
            
        # Return EXACTLY what your React frontend demands
        return {
            "status": "success",
            "card_url": captured_url,
            "analysis": captured_analysis
        }

github_card_agent = GitHubCardAgent()

def get_agent():
    return github_card_agent
