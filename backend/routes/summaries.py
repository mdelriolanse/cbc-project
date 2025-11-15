from fastapi import APIRouter, HTTPException
import database
import claude_service
from models import SummaryResponse
from models import ArgumentMatch

router = APIRouter(prefix="/api/topics/{topic_id}", tags=["summaries"])

@router.post("/generate-summary", response_model=SummaryResponse)
async def generate_summary(topic_id: int):
    """Generate summary, consensus view, and timeline view using Claude."""
    # Validate topic exists
    topic_data = database.get_topic_with_arguments(topic_id)
    if not topic_data:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Get arguments
    pro_arguments = topic_data['pro_arguments']
    con_arguments = topic_data['con_arguments']
    
    if not pro_arguments or not con_arguments:
        raise HTTPException(
            status_code=400,
            detail="Topic must have at least one pro argument and one con argument to generate summary"
        )
    
    try:
        # Call Claude service
        result = claude_service.generate_summary(
            question=topic_data['question'],
            pro_arguments=pro_arguments,
            con_arguments=con_arguments
        )
        
        # Update database
        database.update_topic_analysis(
            topic_id=topic_id,
            overall_summary=result['overall_summary'],
            consensus_view=result['consensus_view'],
            timeline_view=result['timeline_view']
        )
        
        return SummaryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.post("/match-arguments", response_model=list[ArgumentMatch])
async def match_arguments(topic_id: int):
    """Use Claude to identify pro/con argument pairs that directly rebut each other."""
    # Validate topic exists
    topic_data = database.get_topic_with_arguments(topic_id)
    if not topic_data:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")

    pro_arguments = topic_data['pro_arguments']
    con_arguments = topic_data['con_arguments']
    # First check for persisted matches in the database
    try:
        persisted = database.get_argument_matches(topic_id)
        if persisted and len(persisted) > 0:
            # Return persisted matches
            return [ArgumentMatch(**m) for m in persisted]

        # No persisted matches -> call Claude to evaluate and persist the results
        matches = claude_service.evaluate_argument_pairs(
            question=topic_data['question'],
            pro_arguments=pro_arguments,
            con_arguments=con_arguments
        )

        # Persist matches for future requests
        if matches:
            database.save_argument_matches(topic_id, matches)

        return [ArgumentMatch(**m) for m in matches]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match arguments: {str(e)}")

