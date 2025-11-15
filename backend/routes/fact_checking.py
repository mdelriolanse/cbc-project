from fastapi import APIRouter, HTTPException
from typing import Optional
import database
import fact_checker
from models import ValidityVerdictResponse, ArgumentWithValidityResponse

router = APIRouter(prefix="/api", tags=["fact-checking"])

@router.post("/arguments/{argument_id}/verify", response_model=ValidityVerdictResponse)
async def verify_argument(argument_id: int):
    """
    Verify a single argument's validity.
    Runs the fact-checking pipeline and saves results to database.
    """
    # Get argument from database
    argument = database.get_argument(argument_id)
    if not argument:
        raise HTTPException(status_code=404, detail=f"Argument with id {argument_id} not found")
    
    try:
        # Run fact-checking pipeline
        verdict = fact_checker.verify_argument(
            title=argument['title'],
            content=argument['content']
        )
        
        # Save results to database
        database.update_argument_validity(
            argument_id=argument_id,
            validity_score=verdict.validity_score,
            validity_reasoning=verdict.reasoning
        )
        
        return ValidityVerdictResponse(
            validity_score=verdict.validity_score,
            reasoning=verdict.reasoning,
            key_urls=verdict.key_urls,
            source_count=verdict.source_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify argument: {str(e)}")


@router.post("/topics/{topic_id}/verify-all", response_model=dict)
async def verify_all_arguments(topic_id: int):
    """
    Verify all arguments for a topic in batch.
    Returns a summary of verification results.
    """
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Get all arguments for the topic
    arguments = database.get_arguments(topic_id)
    if not arguments:
        raise HTTPException(status_code=400, detail="Topic has no arguments to verify")
    
    results = {
        "total_arguments": len(arguments),
        "verified": 0,
        "failed": 0,
        "results": []
    }
    
    for arg in arguments:
        try:
            verdict = fact_checker.verify_argument(
                title=arg['title'],
                content=arg['content']
            )
            
            # Save results to database
            database.update_argument_validity(
                argument_id=arg['id'],
                validity_score=verdict.validity_score,
                validity_reasoning=verdict.reasoning
            )
            
            results["verified"] += 1
            results["results"].append({
                "argument_id": arg['id'],
                "title": arg['title'],
                "validity_score": verdict.validity_score,
                "status": "success"
            })
            
        except Exception as e:
            results["failed"] += 1
            results["results"].append({
                "argument_id": arg['id'],
                "title": arg['title'],
                "status": "failed",
                "error": str(e)
            })
    
    return results


@router.get("/topics/{topic_id}/arguments/verified", response_model=list[ArgumentWithValidityResponse])
async def get_arguments_sorted_by_validity(
    topic_id: int,
    side: Optional[str] = None
):
    """
    Get arguments sorted by validity score (highest first, unverified at end).
    Optionally filter by side (pro/con).
    """
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Validate side parameter
    if side and side not in ['pro', 'con']:
        raise HTTPException(status_code=400, detail="side query parameter must be 'pro' or 'con'")
    
    try:
        arguments = database.get_arguments_sorted_by_validity(topic_id, side)
        return [ArgumentWithValidityResponse(**arg) for arg in arguments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch arguments: {str(e)}")

