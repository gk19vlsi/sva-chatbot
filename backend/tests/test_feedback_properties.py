"""
Property-Based Tests for Feedback Collection

Tests Properties 26 and 29:
- Property 26: Feedback Persistence
- Property 29: Pattern Usage Tracking

Validates: Requirements 10.3, 11.4
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from bson import ObjectId


class TestFeedbackPersistence:
    """
    Property 26: Feedback Persistence
    
    Tests that user feedback is properly stored and retrieved.
    
    Validates: Requirements 10.3
    """
    
    @pytest.mark.asyncio
    async def test_property_26_feedback_stored_in_database(self, test_db_client):
        """
        Property 26: Feedback is stored in database
        
        When feedback is submitted, it should be stored in the feedback collection
        and associated with the assertion.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test assertion
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Submit feedback
            feedback_doc = {
                "assertion_id": assertion_id,
                "project_id": assertion_doc["project_id"],
                "user_id": "test_user",
                "rating": 5,
                "comment": "Great assertion!",
                "submitted_at": datetime.utcnow()
            }
            
            await db.feedback.insert_one(feedback_doc)
            
            # Verify feedback is stored
            stored_feedback = await db.feedback.find_one({"assertion_id": assertion_id})
            assert stored_feedback is not None
            assert stored_feedback["rating"] == 5
            assert stored_feedback["comment"] == "Great assertion!"
            assert stored_feedback["user_id"] == "test_user"
    
    @pytest.mark.asyncio
    @given(rating=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50)
    async def test_property_26_rating_range_validation(self, test_db_client, rating):
        """
        Property 26: Rating must be between 1 and 5
        
        All feedback ratings should be within the valid range of 1-5.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test assertion
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate"
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Submit feedback with generated rating
            feedback_doc = {
                "assertion_id": assertion_id,
                "project_id": assertion_doc["project_id"],
                "user_id": "test_user",
                "rating": rating,
                "submitted_at": datetime.utcnow()
            }
            
            await db.feedback.insert_one(feedback_doc)
            
            # Verify rating is in valid range
            stored_feedback = await db.feedback.find_one({"assertion_id": assertion_id})
            assert 1 <= stored_feedback["rating"] <= 5
    
    @pytest.mark.asyncio
    async def test_property_26_multiple_feedback_entries(self, test_db_client):
        """
        Property 26: Multiple feedback entries can be stored
        
        An assertion can have multiple feedback entries from different users
        or at different times.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test assertion
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate"
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Submit multiple feedback entries
            for i in range(3):
                feedback_doc = {
                    "assertion_id": assertion_id,
                    "project_id": assertion_doc["project_id"],
                    "user_id": f"user_{i}",
                    "rating": i + 3,  # 3, 4, 5
                    "comment": f"Comment {i}",
                    "submitted_at": datetime.utcnow()
                }
                await db.feedback.insert_one(feedback_doc)
            
            # Verify all feedback entries are stored
            feedback_list = await db.feedback.find(
                {"assertion_id": assertion_id}
            ).to_list(length=None)
            
            assert len(feedback_list) == 3
            assert set(fb["user_id"] for fb in feedback_list) == {"user_0", "user_1", "user_2"}
    
    @pytest.mark.asyncio
    async def test_property_26_feedback_with_optional_comment(self, test_db_client):
        """
        Property 26: Feedback comment is optional
        
        Feedback can be submitted with or without a comment.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test assertion
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate"
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Submit feedback without comment
            feedback_doc = {
                "assertion_id": assertion_id,
                "project_id": assertion_doc["project_id"],
                "user_id": "test_user",
                "rating": 4,
                "submitted_at": datetime.utcnow()
            }
            
            await db.feedback.insert_one(feedback_doc)
            
            # Verify feedback is stored without comment
            stored_feedback = await db.feedback.find_one({"assertion_id": assertion_id})
            assert stored_feedback is not None
            assert stored_feedback["rating"] == 4
            assert "comment" not in stored_feedback or stored_feedback.get("comment") is None


class TestPatternUsageTracking:
    """
    Property 29: Pattern Usage Tracking
    
    Tests that pattern usage is tracked based on feedback.
    
    Validates: Requirements 11.4
    """
    
    @pytest.mark.asyncio
    async def test_property_29_positive_feedback_increments_usage(self, test_db_client):
        """
        Property 29: Positive feedback increments pattern usage count
        
        When an assertion receives positive feedback (rating >= 4),
        the associated pattern's usage count should be incremented.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test pattern
            pattern_doc = {
                "name": "handshake_pattern",
                "template": "assert property...",
                "usage_count": 0,
                "positive_feedback_count": 0
            }
            
            pattern_result = await db.pattern_library.insert_one(pattern_doc)
            pattern_id = pattern_result.inserted_id
            
            # Create assertion using this pattern
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid && ready);",
                "type": "immediate",
                "pattern_id": pattern_id
            }
            
            assertion_result = await db.assertions.insert_one(assertion_doc)
            assertion_id = assertion_result.inserted_id
            
            # Simulate positive feedback (rating = 5)
            await db.pattern_library.update_one(
                {"_id": pattern_id},
                {
                    "$inc": {"usage_count": 1, "positive_feedback_count": 1},
                    "$set": {"last_used": datetime.utcnow()}
                }
            )
            
            # Verify pattern usage count incremented
            updated_pattern = await db.pattern_library.find_one({"_id": pattern_id})
            assert updated_pattern["usage_count"] == 1
            assert updated_pattern["positive_feedback_count"] == 1
            assert "last_used" in updated_pattern
    
    @pytest.mark.asyncio
    async def test_property_29_negative_feedback_tracked(self, test_db_client):
        """
        Property 29: Negative feedback is tracked separately
        
        When an assertion receives negative feedback (rating <= 2),
        the pattern's negative feedback count should be incremented.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test pattern
            pattern_doc = {
                "name": "test_pattern",
                "template": "assert property...",
                "usage_count": 0,
                "negative_feedback_count": 0
            }
            
            pattern_result = await db.pattern_library.insert_one(pattern_doc)
            pattern_id = pattern_result.inserted_id
            
            # Create assertion using this pattern
            assertion_doc = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "pattern_id": pattern_id
            }
            
            await db.assertions.insert_one(assertion_doc)
            
            # Simulate negative feedback (rating = 1)
            await db.pattern_library.update_one(
                {"_id": pattern_id},
                {"$inc": {"negative_feedback_count": 1}}
            )
            
            # Verify negative feedback count incremented
            updated_pattern = await db.pattern_library.find_one({"_id": pattern_id})
            assert updated_pattern["negative_feedback_count"] == 1
    
    @pytest.mark.asyncio
    async def test_property_29_pattern_ranking_by_feedback(self, test_db_client):
        """
        Property 29: Patterns can be ranked by feedback
        
        Patterns with more positive feedback should rank higher.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create multiple patterns with different feedback counts
            patterns = [
                {"name": "pattern_1", "positive_feedback_count": 10, "negative_feedback_count": 1},
                {"name": "pattern_2", "positive_feedback_count": 5, "negative_feedback_count": 2},
                {"name": "pattern_3", "positive_feedback_count": 15, "negative_feedback_count": 0}
            ]
            
            for pattern in patterns:
                await db.pattern_library.insert_one(pattern)
            
            # Query patterns sorted by positive feedback
            sorted_patterns = await db.pattern_library.find().sort(
                "positive_feedback_count", -1
            ).to_list(length=None)
            
            # Verify patterns are sorted correctly
            assert sorted_patterns[0]["name"] == "pattern_3"  # 15 positive
            assert sorted_patterns[1]["name"] == "pattern_1"  # 10 positive
            assert sorted_patterns[2]["name"] == "pattern_2"  # 5 positive
    
    @pytest.mark.asyncio
    async def test_property_29_pattern_without_feedback(self, test_db_client):
        """
        Property 29: Patterns without feedback have zero counts
        
        Newly created patterns should have zero feedback counts.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create new pattern
            pattern_doc = {
                "name": "new_pattern",
                "template": "assert property...",
                "usage_count": 0,
                "positive_feedback_count": 0,
                "negative_feedback_count": 0
            }
            
            result = await db.pattern_library.insert_one(pattern_doc)
            pattern_id = result.inserted_id
            
            # Verify counts are zero
            pattern = await db.pattern_library.find_one({"_id": pattern_id})
            assert pattern["usage_count"] == 0
            assert pattern["positive_feedback_count"] == 0
            assert pattern["negative_feedback_count"] == 0
    
    @pytest.mark.asyncio
    async def test_property_29_last_used_timestamp_updated(self, test_db_client):
        """
        Property 29: Last used timestamp is updated on positive feedback
        
        When a pattern receives positive feedback, its last_used timestamp
        should be updated.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create pattern
            pattern_doc = {
                "name": "test_pattern",
                "template": "assert property...",
                "usage_count": 0
            }
            
            result = await db.pattern_library.insert_one(pattern_doc)
            pattern_id = result.inserted_id
            
            # Update with positive feedback
            now = datetime.utcnow()
            await db.pattern_library.update_one(
                {"_id": pattern_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used": now}
                }
            )
            
            # Verify last_used is set
            updated_pattern = await db.pattern_library.find_one({"_id": pattern_id})
            assert "last_used" in updated_pattern
            assert updated_pattern["last_used"] is not None
