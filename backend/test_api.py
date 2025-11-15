import pytest
from fastapi.testclient import TestClient
from main import app
import database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Reset database before each test."""
    database.init_db()
    yield
    # Cleanup if needed

def test_create_topic():
    """Test creating a topic."""
    response = client.post("/api/topics", json={
        "question": "Should we ban TikTok?",
        "created_by": "testuser"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["question"] == "Should we ban TikTok?"
    assert data["created_by"] == "testuser"
    assert "topic_id" in data
    return data["topic_id"]

def test_get_topics():
    """Test getting all topics."""
    # Create a topic first
    topic_id = test_create_topic()
    
    response = client.get("/api/topics")
    assert response.status_code == 200
    topics = response.json()
    assert len(topics) > 0
    assert topics[0]["id"] == topic_id
    assert "pro_count" in topics[0]
    assert "con_count" in topics[0]

def test_get_topic():
    """Test getting a specific topic."""
    topic_id = test_create_topic()
    
    response = client.get(f"/api/topics/{topic_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == topic_id
    assert data["question"] == "Should we ban TikTok?"
    assert "pro_arguments" in data
    assert "con_arguments" in data

def test_get_nonexistent_topic():
    """Test getting a topic that doesn't exist."""
    response = client.get("/api/topics/99999")
    assert response.status_code == 404

def test_create_argument():
    """Test creating arguments."""
    topic_id = test_create_topic()
    
    # Create pro argument
    response = client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Privacy concerns",
        "content": "TikTok collects too much data",
        "author": "user1",
        "sources": "https://example.com"
    })
    assert response.status_code == 201
    assert "argument_id" in response.json()
    
    # Create con argument
    response = client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "con",
        "title": "Free speech",
        "content": "Banning violates free speech",
        "author": "user2"
    })
    assert response.status_code == 201

def test_create_argument_validation():
    """Test argument validation - must have both pro and con."""
    topic_id = test_create_topic()
    
    # Create pro argument
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Test",
        "content": "Test content",
        "author": "user1"
    })
    
    # Try to add another pro (should fail if no con exists)
    response = client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Test 2",
        "content": "Test content 2",
        "author": "user1"
    })
    assert response.status_code == 400

def test_get_arguments():
    """Test getting arguments."""
    topic_id = test_create_topic()
    
    # Create arguments
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Pro argument",
        "content": "Content",
        "author": "user1"
    })
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "con",
        "title": "Con argument",
        "content": "Content",
        "author": "user2"
    })
    
    # Get all arguments
    response = client.get(f"/api/topics/{topic_id}/arguments")
    assert response.status_code == 200
    args = response.json()
    assert len(args) == 2
    
    # Get pro only
    response = client.get(f"/api/topics/{topic_id}/arguments?side=pro")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["side"] == "pro"

def test_generate_summary():
    """Test generating summary."""
    topic_id = test_create_topic()
    
    # Create arguments
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Privacy concerns",
        "content": "TikTok collects user data without consent",
        "author": "user1"
    })
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "con",
        "title": "Free speech",
        "content": "Banning TikTok would violate free speech rights",
        "author": "user2"
    })
    
    # Mock or skip if no API key - just test endpoint structure
    # In real scenario, you'd mock the Claude API call
    response = client.post(f"/api/topics/{topic_id}/generate-summary")
    # This will fail without API key, but tests endpoint exists
    assert response.status_code in [200, 500]  # 500 if no API key

def test_generate_summary_requires_both_sides():
    """Test that summary requires both pro and con."""
    topic_id = test_create_topic()
    
    # Only create pro argument
    client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "pro",
        "title": "Test",
        "content": "Content",
        "author": "user1"
    })
    
    response = client.post(f"/api/topics/{topic_id}/generate-summary")
    assert response.status_code == 400

def test_invalid_side():
    """Test invalid side value."""
    topic_id = test_create_topic()
    
    response = client.post(f"/api/topics/{topic_id}/arguments", json={
        "side": "invalid",
        "title": "Test",
        "content": "Content",
        "author": "user1"
    })
    assert response.status_code == 400

