from fastapi import APIRouter, HTTPException
import database
import claude_service
from models import SummaryResponse

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

