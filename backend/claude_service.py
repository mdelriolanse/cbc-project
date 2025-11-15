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


def evaluate_argument_pairs(question: str, pro_arguments: List[Dict], con_arguments: List[Dict]) -> List[Dict]:
    """
    Evaluate pro and con arguments and return pairs that directly rebut each other.

    Returns a list of objects: {"pro_id": int, "con_id": int, "reason": str}
    """
    # Prepare formatted text with ids so Claude can reference them
    def fmt_args(args, side_label):
        if not args:
            return "None"
        lines = []
        for a in args:
            # Expect each arg to include 'id', 'title', 'content'
            lines.append(f"ID: {a.get('id')} | Title: {a.get('title')} | Content: {a.get('content')}")
        return "\n\n".join(lines)

    pro_text = fmt_args(pro_arguments, 'PRO')
    con_text = fmt_args(con_arguments, 'CON')

    prompt = f"""You are given a debate question and two lists of arguments, PRO and CON. Each argument is labeled with an ID.

Question: {question}

PRO arguments:
{pro_text}

CON arguments:
{con_text}

Task: For each PRO argument, identify any CON arguments that directly rebut or address the same claim (and vice versa). Return a JSON array of objects with the fields:

  - pro_id: the ID of the pro argument (or null if the match is from a con perspective)
  - con_id: the ID of the con argument (or null if the match is from a pro perspective)
  - reason: one-sentence explanation of why these two arguments are linked (the claim they conflict about)

Only include pairs where the arguments clearly address the same point or directly contradict one another. Do not invent arguments. Return JSON only, e.g.:

[{{"pro_id": 12, "con_id": 34, "reason": "Both discuss data collection practices; con argues it's not harmful, pro argues privacy risk."}}]
"""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Strip code fences if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # Validate structure
        if not isinstance(result, list):
            raise ValueError("Expected a JSON array of matches")

        # Normalize entries to have pro_id and con_id
        normalized = []
        for item in result:
            if not isinstance(item, dict):
                continue
            pro_id = item.get('pro_id')
            con_id = item.get('con_id')
            reason = item.get('reason') or item.get('explanation') or None
            if pro_id is None or con_id is None:
                # skip incomplete matches
                continue
            normalized.append({'pro_id': int(pro_id), 'con_id': int(con_id), 'reason': reason})

        return normalized

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Claude response: {e}")
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")

