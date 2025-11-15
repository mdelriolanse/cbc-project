from fastapi import APIRouter, HTTPException
import database
import fact_checker
import claude_service
from models import TopicCreate, TopicResponse, TopicListItem, TopicDetailResponse

router = APIRouter(prefix="/api/topics", tags=["topics"])

@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(topic: TopicCreate):
    """Create a new debate topic."""
    try:
        topic_id = database.create_topic(
            question=topic.question,
            created_by=topic.created_by
        )
        topic_data = database.get_topic(topic_id)
        return TopicResponse(
            topic_id=topic_data['id'],
            question=topic_data['question'],
            created_by=topic_data['created_by'],
            created_at=topic_data.get('created_at')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")

@router.get("", response_model=list[TopicListItem])
async def get_topics():
    """Get all topics with pro/con argument counts."""
    try:
        topics = database.get_all_topics()
        return [TopicListItem(**topic) for topic in topics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch topics: {str(e)}")

@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(topic_id: int):
    """
    Get a topic with its arguments and analysis.
    Automatically verifies arguments and generates Claude analysis if missing.
    Arguments are always sorted by validity score (highest first).
    """
    topic_data = database.get_topic_with_arguments(topic_id)
    if not topic_data:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    # Check if any arguments need verification
    all_arguments = topic_data['pro_arguments'] + topic_data['con_arguments']
    needs_verification = any(
        arg.get('validity_score') is None for arg in all_arguments
    )
    
    # Auto-verify all arguments if needed
    if needs_verification and all_arguments:
        for arg in all_arguments:
            if arg.get('validity_score') is None:
                try:
                    verdict = fact_checker.verify_argument(
                        title=arg['title'],
                        content=arg['content']
                    )
                    database.update_argument_validity(
                        argument_id=arg['id'],
                        validity_score=verdict.validity_score,
                        validity_reasoning=verdict.reasoning,
                        key_urls=verdict.key_urls
                    )
                except Exception:
                    # Continue even if verification fails for one argument
                    pass
        
        # Refetch topic data with updated validity scores
        topic_data = database.get_topic_with_arguments(topic_id)
    
    # Check if Claude analysis is missing
    needs_analysis = (
        not topic_data.get('overall_summary') or
        not topic_data.get('consensus_view') or
        not topic_data.get('timeline_view')
    )
    
    # Auto-generate Claude analysis if needed
    if needs_analysis:
        pro_args = topic_data['pro_arguments']
        con_args = topic_data['con_arguments']
        
        if pro_args and con_args:
            try:
                result = claude_service.generate_summary(
                    question=topic_data['question'],
                    pro_arguments=pro_args,
                    con_arguments=con_args
                )
                database.update_topic_analysis(
                    topic_id=topic_id,
                    overall_summary=result['overall_summary'],
                    consensus_view=result['consensus_view'],
                    timeline_view=result['timeline_view']
                )
                # Update topic_data with new analysis
                topic_data['overall_summary'] = result['overall_summary']
                topic_data['consensus_view'] = result['consensus_view']
                topic_data['timeline_view'] = result['timeline_view']
            except Exception:
                # Continue even if analysis generation fails
                pass
    
    return TopicDetailResponse(**topic_data)

