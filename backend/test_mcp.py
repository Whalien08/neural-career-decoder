import asyncio
import json
import os
import sys
from mcp_server import mcp

def extract_result(tool_output):
    """MCP tools might return a list of TextContent objects. Extract the data."""
    if isinstance(tool_output, list) and len(tool_output) > 0:
        # Check if it has a 'text' attribute (TextContent)
        if hasattr(tool_output[0], 'text'):
            content = tool_output[0].text
            try:
                return json.loads(content)
            except:
                return content
    return tool_output

async def test():
    username = 'torvalds'
    print(f'--- Testing for {username} ---')
    
    try:
        # 1. Scrape
        raw_github_data = await mcp.call_tool('scrape_github', {'username': username})
        github_data = extract_result(raw_github_data)
        
        if isinstance(github_data, dict) and 'error' in github_data:
            print(f"Error in scrape_github: {github_data['error']}")
            return
        print('Step 1: Scrape successful.')

        # 2. Analyze
        raw_analysis = await mcp.call_tool('analyze_profile', {'github_data': github_data})
        analysis = extract_result(raw_analysis)
        print('Step 2: Analysis successful.')

        # 3. Generate HTML
        raw_html = await mcp.call_tool('generate_card_html', {
            'username': username,
            'github_data': github_data,
            'analysis': analysis
        })
        html = extract_result(raw_html)
        print('Step 3: HTML Generation successful.')

        # 4. Results
        print('\n--- Analysis Results ---')
        if isinstance(analysis, dict):
            print(f"Theme: {analysis.get('card_theme')}")
            print(f"Vibe:  {analysis.get('developer_vibe')}")
        else:
            print(f"Analysis returned non-dict: {analysis}")

    except Exception as e:
        print(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    asyncio.run(test())
