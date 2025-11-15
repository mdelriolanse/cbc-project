from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import database
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
    # Allow first argument of either side, but after that require both sides
    counts = database.get_argument_counts(topic_id)
    
    # If topic has one side but not the other, only allow arguments from the missing side
    if counts['pro_count'] == 0 and counts['con_count'] > 0:
        if argument.side != 'pro':
            raise HTTPException(
                status_code=400,
                detail="Topic must have at least 1 pro argument AND 1 con argument. Please add a pro argument first."
            )
    elif counts['con_count'] == 0 and counts['pro_count'] > 0:
        if argument.side != 'con':
            raise HTTPException(
                status_code=400,
                detail="Topic must have at least 1 pro argument AND 1 con argument. Please add a con argument first."
            )
    
    try:
        argument_id = database.create_argument(
            topic_id=topic_id,
            side=argument.side,
            title=argument.title,
            content=argument.content,
            author=argument.author,
            sources=argument.sources
        )
        return ArgumentCreateResponse(argument_id=argument_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create argument: {str(e)}")

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

