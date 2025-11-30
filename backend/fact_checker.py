import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic
from tavily import TavilyClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file from the backend directory (works in both local and Docker)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

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
    is_relevant: bool = Field(..., description="Whether the argument is relevant to the debate topic")
    validity_score: int = Field(..., ge=1, le=5, description="Validity score from 1-5 stars (only meaningful if is_relevant=True)")
    reasoning: str = Field(..., description="Explanation for the validity score")
    key_urls: List[str] = Field(..., description="Top 3 most relevant source URLs")
    source_count: int = Field(..., description="Number of sources found")


def extract_core_claim(title: str, content: str, debate_question: str) -> str:
    """
    STEP 1: Extract the core verifiable claim from an argument.
    
    Uses Claude to strip away rhetoric and focus on factual claims that can be researched.
    
    Args:
        title: Argument title
        content: Argument content
        debate_question: The debate topic/question this argument is responding to
    
    Returns:
        Extracted claim in 2 sentences or less
    """
    prompt = f"""You are analyzing an argument in a debate about: {debate_question}

Extract the core verifiable claim from this argument. Focus on factual statements that can be researched and verified, not opinions or rhetoric.

Title: {title}
Content: {content}

Return ONLY the core factual claim in 2 sentences or less. Remove all opinion, rhetoric, and emotional language. Focus on what can be factually verified related to the debate topic.

If the argument contains no verifiable factual claims (only opinions, insults, or emotional statements), return "NO VERIFIABLE FACTUAL CLAIMS"."""

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


def analyze_and_score(original_claim: str, tavily_results: List[Dict], debate_question: str) -> ValidityVerdict:
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
    
    prompt = f"""You are fact-checking an argument in a debate about: {debate_question}

FIRST, determine if this argument is RELEVANT to the debate topic.

An argument is IRRELEVANT if it:
- Contains no factual claims (only opinions like "this sucks" or "you guys are wrong")
- Makes claims unrelated to the debate topic
- Is just insults, rhetoric, or emotional statements

If IRRELEVANT:
- Set is_relevant to false
- Set validity_score to 1
- Provide reasoning explaining why it's irrelevant

If RELEVANT:
- Set is_relevant to true
- Verify whether the factual claims supporting their position are true
- Score based on evidence quality (1-5 stars)

ORIGINAL CLAIM:
{original_claim}

SEARCH RESULTS (pre-filtered for high-quality sources with relevance score > 0.5):
{formatted_results}

If RELEVANT, assign a validity score from 1-5 stars based on these criteria:

- 5 stars: Fully supported by multiple high-quality sources (average relevance score > 0.8, at least 2-3 sources)
- 4 stars: Mostly supported with good sources (average relevance score > 0.6, at least 2 sources)
- 3 stars: Partially supported, mixed evidence (1-2 sources with moderate scores)
- 2 stars: Limited support from few sources (only 1 source or low average score)
- 1 star: No credible evidence, contradicted by sources

IMPORTANT: These sources have already been filtered for quality (relevance score > 0.5). 
If very few sources pass this threshold, the validity score should be lower.

Consider BOTH the number of sources AND their quality (relevance scores).

Average relevance score of sources: {avg_score:.3f}
Number of high-quality sources found: {source_count}

Return a JSON object with this exact structure. Make sure all strings are properly escaped:
{{
    "is_relevant": <boolean>,
    "validity_score": <1-5>,
    "reasoning": "<2-3 sentences explaining the score. Escape any quotes with backslash.>",
    "key_urls": ["<url1>", "<url2>", "<url3>"]
}}

IMPORTANT: 
- Return ONLY valid JSON, no markdown formatting or extra text
- Escape all quotes in the reasoning field with backslashes
- Include exactly 3 URLs or fewer from the search results above
- Ensure all URLs are properly quoted and escaped"""

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
        
        # Extract JSON from response - handle multiple formats
        json_text = None
        
        # Try to find JSON in code blocks first
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_block_match:
            json_text = json_block_match.group(1)
        else:
            # Try to find JSON object by matching braces
            # Find the first { and match to the last }
            start_idx = response_text.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
            else:
                # Fallback: use entire response
                json_text = response_text
        
        # Clean up the JSON text
        if json_text:
            json_text = json_text.strip()
        
        # Parse JSON with error handling
        result = None
        try:
            result = json.loads(json_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, extract fields manually using regex
            # This handles cases where Claude returns malformed JSON (e.g., unescaped quotes)
            
            # Extract is_relevant (boolean)
            is_relevant_match = re.search(r'"is_relevant"\s*:\s*(true|false)', json_text, re.IGNORECASE)
            is_relevant = is_relevant_match.group(1).lower() == 'true' if is_relevant_match else True  # Default to True if not found
            
            validity_match = re.search(r'"validity_score"\s*:\s*(\d+)', json_text)
            
            validity_score = int(validity_match.group(1)) if validity_match else 3
            if validity_score < 1 or validity_score > 5:
                validity_score = 3
            
            # Extract reasoning - handle unescaped quotes by finding the field value manually
            reasoning = "Unable to parse reasoning from response"
            reasoning_start = json_text.find('"reasoning"')
            if reasoning_start != -1:
                # Find the colon after "reasoning"
                colon_pos = json_text.find(':', reasoning_start)
                if colon_pos != -1:
                    # Find the opening quote
                    quote_start = json_text.find('"', colon_pos)
                    if quote_start != -1:
                        # Parse character by character to find the closing quote
                        # Skip escaped quotes
                        i = quote_start + 1
                        reasoning_end = -1
                        while i < len(json_text):
                            if json_text[i] == '\\' and i + 1 < len(json_text):
                                i += 2  # Skip escaped character
                                continue
                            elif json_text[i] == '"':
                                # Check if this is followed by comma or closing brace
                                j = i + 1
                                while j < len(json_text) and json_text[j] in ' \t\n\r':
                                    j += 1
                                if j < len(json_text) and json_text[j] in ',}':
                                    reasoning_end = i
                                    break
                            i += 1
                        
                        if reasoning_end > quote_start:
                            reasoning = json_text[quote_start + 1:reasoning_end]
                            # Unescape common escape sequences
                            reasoning = reasoning.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
            
            # Extract URLs from the array
            urls_match = re.search(r'"key_urls"\s*:\s*\[(.*?)\]', json_text, re.DOTALL)
            key_urls = []
            if urls_match:
                urls_text = urls_match.group(1)
                # Extract URLs, handling escaped quotes
                url_matches = re.findall(r'"((?:[^"\\]|\\.)*)"', urls_text)
                key_urls = [url.replace('\\"', '"').replace('\\\\', '\\') for url in url_matches if url][:3]
            
            result = {
                'is_relevant': is_relevant,
                'validity_score': validity_score,
                'reasoning': reasoning,
                'key_urls': key_urls
            }
        
        # Validate and create verdict
        is_relevant = result.get('is_relevant', True)
        if not isinstance(is_relevant, bool):
            is_relevant = str(is_relevant).lower() in ('true', '1', 'yes')
        
        validity_score = int(result.get('validity_score', 3))
        if validity_score < 1 or validity_score > 5:
            validity_score = 3  # Default to middle score if invalid
        
        # Ensure key_urls is a list and limit to 3
        key_urls = result.get('key_urls', [])
        if isinstance(key_urls, str):
            key_urls = [key_urls]
        elif not isinstance(key_urls, list):
            key_urls = []
        # Filter out empty strings and limit to 3
        key_urls = [url for url in key_urls if url and isinstance(url, str)][:3]
        
        # Clean reasoning text
        reasoning = result.get('reasoning', 'No reasoning provided')
        if isinstance(reasoning, str):
            # Remove any extra quotes or formatting
            reasoning = reasoning.strip().strip('"').strip("'")
        
        verdict = ValidityVerdict(
            is_relevant=is_relevant,
            validity_score=validity_score,
            reasoning=reasoning,
            key_urls=key_urls,
            source_count=source_count
        )
        
        return verdict
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Claude response: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to analyze and score: {str(e)}")


def verify_argument(title: str, content: str, debate_question: str) -> ValidityVerdict:
    """
    Main pipeline function that chains all 3 steps together.
    
    Args:
        title: Argument title
        content: Argument content
        debate_question: The debate topic/question this argument is responding to
    
    Returns:
        ValidityVerdict with fact-checking results
    """
    try:
        # Step 1: Extract core claim
        claim = extract_core_claim(title, content, debate_question)
        
        # If no verifiable claims found, return irrelevant verdict
        if claim.upper() == "NO VERIFIABLE FACTUAL CLAIMS" or not claim.strip():
            return ValidityVerdict(
                is_relevant=False,
                validity_score=1,
                reasoning=f"This argument contains no verifiable factual claims related to the debate topic: '{debate_question}'. It consists only of opinions, rhetoric, or emotional statements that cannot be fact-checked.",
                key_urls=[],
                source_count=0
            )
        
        # Step 2: Search for evidence
        all_search_results = search_for_evidence(claim)
        
        # Filter for high-quality sources only (score > 0.5)
        filtered_results = [
            r for r in all_search_results 
            if r.get('score', 0) > 0.5
        ]
        
        # Sort by score (highest first) and take top 3
        filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_sources = filtered_results[:3]
        
        # If no sources pass the threshold, return low validity score (but still relevant if it has claims)
        if not top_sources:
            return ValidityVerdict(
                is_relevant=True,  # Still relevant, just can't verify
                validity_score=1,
                reasoning="No high-quality sources found (all sources had relevance score ≤ 0.5). The claim cannot be verified with credible evidence.",
                key_urls=[],
                source_count=len(all_search_results)
            )
        
        # Step 3: Analyze and score using only filtered high-quality sources
        verdict = analyze_and_score(claim, top_sources, debate_question)
        
        # Extract URLs from top sources for key_urls (only high-quality sources with score > 0.5)
        key_urls = [source.get('url', '') for source in top_sources if source.get('url')]
        verdict.key_urls = key_urls[:3]  # Ensure max 3 URLs
        
        # Update source_count to reflect total sources found (before filtering)
        verdict.source_count = len(all_search_results)
        
        return verdict
        
    except Exception as e:
        # Return a default verdict on error
        return ValidityVerdict(
            is_relevant=True,  # Default to relevant on error
            validity_score=1,
            reasoning=f"Fact-checking failed: {str(e)}",
            key_urls=[],
            source_count=0
        )

