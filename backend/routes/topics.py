from fastapi import APIRouter, HTTPException
import database
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
    """Get a topic with its arguments and analysis."""
    topic_data = database.get_topic_with_arguments(topic_id)
    if not topic_data:
        raise HTTPException(status_code=404, detail=f"Topic with id {topic_id} not found")
    
    return TopicDetailResponse(**topic_data)

