from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import database
import fact_checker
from models import ArgumentCreate, ArgumentCreateResponse, ArgumentResponse

router = APIRouter(prefix="/api/topics/{topic_id}/arguments", tags=["arguments"])

@router.post("", response_model=ArgumentCreateResponse, status_code=201)
async def create_argument(topic_id: int, argument: ArgumentCreate):
    """Create a new argument for a topic."""
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Validate side
    if argument.side not in ['pro', 'con']:
        raise HTTPException(status_code=400, detail="side must be either 'pro' or 'con'")
    
    # Validation: Topic must have at least 1 pro AND 1 con total
    # Previous behavior required adding the missing opposite-side argument before allowing
    # additional arguments on the same side. We now allow creating multiple arguments
    # on the same side even when the other side is empty. This lets topics start with
    # a single pro OR con and grow naturally.
    
    try:
        # Run fact-checker to verify relevance before saving
        verdict = fact_checker.verify_argument(
            title=argument.title,
            content=argument.content,
            debate_question=topic['question']
        )
        
        # Reject irrelevant arguments
        if not verdict.is_relevant:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Argument not relevant",
                    "reasoning": verdict.reasoning,
                    "message": f"This argument was rejected as not relevant to the debate topic: '{topic['question']}'. Please submit an argument with factual claims related to the debate."
                }
            )
        
        # Create the argument
        argument_id = database.create_argument(
            topic_id=topic_id,
            side=argument.side,
            title=argument.title,
            content=argument.content,
            author=argument.author,
            sources=argument.sources
        )
        
        # Save validity score immediately
        database.update_argument_validity(
            argument_id=argument_id,
            validity_score=verdict.validity_score,
            validity_reasoning=verdict.reasoning,
            key_urls=verdict.key_urls
        )
        
        return ArgumentCreateResponse(argument_id=argument_id)
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for irrelevant arguments)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create argument: {str(e)}")


@router.put("/{argument_id}")
async def update_argument(topic_id: int, argument_id: int, argument: ArgumentCreate):
    """Update an existing argument. Clearing persisted matches for the topic so they will be re-evaluated."""
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")

    # Validate argument exists
    args = database.get_arguments(topic_id)
    arg_exists = any(a['id'] == argument_id for a in args)
    if not arg_exists:
        raise HTTPException(status_code=404, detail=f"Argument with id {argument_id} not found in topic {topic_id}")

    try:
        database.update_argument(argument_id, argument.title, argument.content, argument.sources)
        # Clear persisted matches for this topic so they will be recomputed on next request
        database.delete_argument_matches_for_topic(topic_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update argument: {str(e)}")

@router.get("", response_model=list[ArgumentResponse])
async def get_arguments(
    topic_id: int,
    side: Optional[str] = Query(None, description="Filter by side: 'pro', 'con', or 'both' (default)")
):
    """Get arguments for a topic, optionally filtered by side."""
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Validate side parameter
    if side and side not in ['pro', 'con', 'both']:
        raise HTTPException(status_code=400, detail="side query parameter must be 'pro', 'con', or 'both'")
    
    try:
        filter_side = None if (side is None or side == 'both') else side
        arguments = database.get_arguments(topic_id, filter_side)
        return [ArgumentResponse(**arg) for arg in arguments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch arguments: {str(e)}")

