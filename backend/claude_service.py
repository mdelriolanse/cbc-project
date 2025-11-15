import os
import json
from typing import List, Dict
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

client = Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-20250514"

def generate_summary(question: str, pro_arguments: List[Dict], con_arguments: List[Dict]) -> Dict:
    """
    Generate overall summary, consensus view, and timeline view using Claude.
    
    Args:
        question: The debate question
        pro_arguments: List of pro arguments with 'title' and 'content'
        con_arguments: List of con arguments with 'title' and 'content'
    
    Returns:
        Dictionary with 'overall_summary', 'consensus_view', and 'timeline_view'
    """
    # Format pro arguments
    pro_text = "\n\n".join([
        f"Title: {arg['title']}\nContent: {arg['content']}"
        for arg in pro_arguments
    ]) if pro_arguments else "None"
    
    # Format con arguments
    con_text = "\n\n".join([
        f"Title: {arg['title']}\nContent: {arg['content']}"
        for arg in con_arguments
    ]) if con_arguments else "None"
    
    prompt = f"""You are analyzing a debate on: {question}

PRO arguments:
{pro_text}

CON arguments:
{con_text}

Generate three things (do NOT create new arguments, only synthesize existing):
1. OVERALL SUMMARY (2-3 paragraphs): What is this debate about? Main themes?
2. CONSENSUS VIEW (1-2 paragraphs): What do both sides agree on?
3. TIMELINE VIEW: Chronological narrative based on arguments. Array of {{"period": "...", "description": "..."}}

Return JSON only: {{"overall_summary": "...", "consensus_view": "...", "timeline_view": [...]}}"""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract text from response
        response_text = message.content[0].text.strip()
        
        # Try to parse JSON from the response
        # Claude might wrap JSON in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Validate structure
        if not all(key in result for key in ['overall_summary', 'consensus_view', 'timeline_view']):
            raise ValueError("Missing required fields in Claude response")
        
        if not isinstance(result['timeline_view'], list):
            raise ValueError("timeline_view must be a list")
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Claude response: {e}")
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")

