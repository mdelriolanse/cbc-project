import os
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
from tavily import TavilyClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Initialize API clients
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is required")

claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Use Claude Haiku for fast, cost-effective fact-checking
CLAUDE_MODEL = "claude-3-haiku-20240307"


class ValidityVerdict(BaseModel):
    """Pydantic model for fact-checking verdict."""
    validity_score: int = Field(..., ge=1, le=5, description="Validity score from 1-5 stars")
    reasoning: str = Field(..., description="Explanation for the validity score")
    key_urls: List[str] = Field(..., description="Top 3 most relevant source URLs")
    source_count: int = Field(..., description="Number of sources found")


def extract_core_claim(title: str, content: str) -> str:
    """
    STEP 1: Extract the core verifiable claim from an argument.
    
    Uses Claude to strip away rhetoric and focus on factual claims that can be researched.
    
    Args:
        title: Argument title
        content: Argument content
    
    Returns:
        Extracted claim in 2 sentences or less
    """
    prompt = f"""Extract the core verifiable claim from this argument. Focus on factual statements that can be researched and verified, not opinions or rhetoric.

Title: {title}
Content: {content}

Return ONLY the core factual claim in 2 sentences or less. Remove all opinion, rhetoric, and emotional language. Focus on what can be factually verified."""

    try:
        message = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        claim = message.content[0].text.strip()
        return claim
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract core claim: {str(e)}")


def search_for_evidence(claim: str) -> List[Dict]:
    """
    STEP 2: Search for evidence using Tavily API.
    
    Args:
        claim: The extracted core claim to search for
    
    Returns:
        List of search results from Tavily
    """
    try:
        response = tavily_client.search(
            query=claim,
            max_results=10,
            search_depth="advanced"
        )
        
        # Tavily returns results directly or in a 'results' key
        if isinstance(response, dict):
            results = response.get('results', [])
        elif isinstance(response, list):
            results = response
        else:
            results = []
        
        return results
        
    except Exception as e:
        raise RuntimeError(f"Failed to search for evidence: {str(e)}")


def format_tavily_results(results: List[Dict]) -> str:
    """
    Format Tavily search results for Claude analysis.
    
    Args:
        results: List of Tavily search result dictionaries
    
    Returns:
        Formatted string with results
    """
    if not results:
        return "No sources found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        url = result.get('url', 'No URL')
        score = result.get('score', 0)
        content = result.get('content', 'No content')[:500]  # Limit content length
        
        formatted.append(f"""
Source {i}:
Title: {title}
URL: {url}
Relevance Score: {score:.3f}
Content: {content}...
""")
    
    return "\n".join(formatted)


def analyze_and_score(original_claim: str, tavily_results: List[Dict]) -> ValidityVerdict:
    """
    STEP 3: Analyze evidence and assign validity score.
    
    Uses Claude to analyze the quality and quantity of evidence and assign a 1-5 star score.
    
    Args:
        original_claim: The extracted core claim
        tavily_results: List of Tavily search results
    
    Returns:
        ValidityVerdict with score, reasoning, and key URLs
    """
    formatted_results = format_tavily_results(tavily_results)
    source_count = len(tavily_results)
    
    # Calculate average relevance score
    avg_score = 0.0
    if tavily_results:
        scores = [r.get('score', 0) for r in tavily_results]
        avg_score = sum(scores) / len(scores) if scores else 0.0
    
    prompt = f"""You are a fact-checker analyzing the validity of a claim based on search results.

ORIGINAL CLAIM:
{original_claim}

SEARCH RESULTS:
{formatted_results}

Analyze the evidence and assign a validity score from 1-5 stars based on these criteria:

- 5 stars: Fully supported by multiple high-quality sources (average relevance score > 0.8)
- 4 stars: Mostly supported with good sources (average relevance score > 0.6)
- 3 stars: Partially supported, mixed evidence
- 2 stars: Mostly unsupported or low-quality sources
- 1 star: No credible evidence or contradicted by sources

Consider BOTH the number of sources AND their quality (relevance scores).

Average relevance score of sources: {avg_score:.3f}
Number of sources found: {source_count}

Return a JSON object with this exact structure:
{{
    "validity_score": <1-5>,
    "reasoning": "<2-3 sentences explaining the score>",
    "key_urls": ["<top 3 most relevant URLs>"]
}}

Only include URLs from the search results above."""

    try:
        message = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = message.content[0].text.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Validate and create verdict
        validity_score = int(result.get('validity_score', 3))
        if validity_score < 1 or validity_score > 5:
            validity_score = 3  # Default to middle score if invalid
        
        # Ensure key_urls is a list and limit to 3
        key_urls = result.get('key_urls', [])
        if isinstance(key_urls, str):
            key_urls = [key_urls]
        key_urls = key_urls[:3]  # Limit to top 3
        
        verdict = ValidityVerdict(
            validity_score=validity_score,
            reasoning=result.get('reasoning', 'No reasoning provided'),
            key_urls=key_urls,
            source_count=source_count
        )
        
        return verdict
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Claude response: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to analyze and score: {str(e)}")


def verify_argument(title: str, content: str) -> ValidityVerdict:
    """
    Main pipeline function that chains all 3 steps together.
    
    Args:
        title: Argument title
        content: Argument content
    
    Returns:
        ValidityVerdict with fact-checking results
    """
    try:
        # Step 1: Extract core claim
        claim = extract_core_claim(title, content)
        
        # Step 2: Search for evidence
        search_results = search_for_evidence(claim)
        
        # Step 3: Analyze and score
        verdict = analyze_and_score(claim, search_results)
        
        return verdict
        
    except Exception as e:
        # Return a default verdict on error
        return ValidityVerdict(
            validity_score=1,
            reasoning=f"Fact-checking failed: {str(e)}",
            key_urls=[],
            source_count=0
        )

