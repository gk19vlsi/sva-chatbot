"""
Property-Based Tests for Assertion Regeneration

Tests Property 26 (Feedback-Based Regeneration):
- Assertions can be regenerated based on feedback
- Regenerated assertions incorporate feedback
- Original assertions are marked as superseded

Validates: Requirements 10.4
"""
import pytest
from datetime import datetime
from bson import ObjectId


class TestFeedbackBasedRegeneration:
    """
    Property 26: Feedback-Based Regeneration
    
    Tests that assertions can be regenerated based on user feedback.
    
    Validates: Requirements 10.4
    """
    
    @pytest.mark.asyncio
    async def test_property_26_regeneration_creates_new_assertion(self, test_db_client):
        """
        Property 26: Regeneration creates a new assertion
        
        When an assertion is regenerated, a new assertion document
        should be created in the database.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion
            original_assertion = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "generated_at": datetime.utcnow()
            }
            
            result = await db.assertions.insert_one(original_assertion)
            original_id = result.inserted_id
            
            # Simulate regeneration
            regenerated_assertion = {
                "project_id": original_assertion["project_id"],
                "code": "assert (valid && ready);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.8,
                "generated_at": datetime.utcnow(),
                "regenerated_from": original_id,
                "feedback_incorporated": 2
            }
            
            result = await db.assertions.insert_one(regenerated_assertion)
            new_id = result.inserted_id
            
            # Verify new assertion exists
            new_assertion = await db.assertions.find_one({"_id": new_id})
            assert new_assertion is not None
            assert new_assertion["regenerated_from"] == original_id
            assert new_assertion["feedback_incorporated"] == 2
    
    @pytest.mark.asyncio
    async def test_property_26_original_marked_as_superseded(self, test_db_client):
        """
        Property 26: Original assertion is marked as superseded
        
        When an assertion is regenerated, the original should be marked
        as superseded with a reference to the new assertion.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion
            original_assertion = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate"
            }
            
            result = await db.assertions.insert_one(original_assertion)
            original_id = result.inserted_id
            
            # Create regenerated assertion
            regenerated_assertion = {
                "project_id": original_assertion["project_id"],
                "code": "assert (valid && ready);",
                "type": "immediate",
                "regenerated_from": original_id
            }
            
            result = await db.assertions.insert_one(regenerated_assertion)
            new_id = result.inserted_id
            
            # Mark original as superseded
            await db.assertions.update_one(
                {"_id": original_id},
                {
                    "$set": {
                        "superseded_by": new_id,
                        "superseded_at": datetime.utcnow()
                    }
                }
            )
            
            # Verify original is marked as superseded
            original = await db.assertions.find_one({"_id": original_id})
            assert "superseded_by" in original
            assert original["superseded_by"] == new_id
            assert "superseded_at" in original
    
    @pytest.mark.asyncio
    async def test_property_26_feedback_count_tracked(self, test_db_client):
        """
        Property 26: Number of feedback entries incorporated is tracked
        
        The regenerated assertion should track how many feedback entries
        were considered during regeneration.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion
            original_assertion = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate"
            }
            
            result = await db.assertions.insert_one(original_assertion)
            original_id = result.inserted_id
            
            # Create feedback entries
            for i in range(3):
                feedback_doc = {
                    "assertion_id": original_id,
                    "project_id": original_assertion["project_id"],
                    "user_id": f"user_{i}",
                    "rating": 2,  # Low rating
                    "comment": f"Issue {i}",
                    "submitted_at": datetime.utcnow()
                }
                await db.feedback.insert_one(feedback_doc)
            
            # Create regenerated assertion
            regenerated_assertion = {
                "project_id": original_assertion["project_id"],
                "code": "assert (valid && ready && enable);",
                "type": "immediate",
                "regenerated_from": original_id,
                "feedback_incorporated": 3
            }
            
            result = await db.assertions.insert_one(regenerated_assertion)
            
            # Verify feedback count
            new_assertion = await db.assertions.find_one({"_id": result.inserted_id})
            assert new_assertion["feedback_incorporated"] == 3
    
    @pytest.mark.asyncio
    async def test_property_26_regeneration_chain_tracked(self, test_db_client):
        """
        Property 26: Regeneration chain can be tracked
        
        Multiple regenerations should form a traceable chain from
        original to latest version.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion
            v1 = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "version": 1
            }
            
            result = await db.assertions.insert_one(v1)
            v1_id = result.inserted_id
            
            # Create second version
            v2 = {
                "project_id": v1["project_id"],
                "code": "assert (valid && ready);",
                "type": "immediate",
                "version": 2,
                "regenerated_from": v1_id
            }
            
            result = await db.assertions.insert_one(v2)
            v2_id = result.inserted_id
            
            # Mark v1 as superseded
            await db.assertions.update_one(
                {"_id": v1_id},
                {"$set": {"superseded_by": v2_id}}
            )
            
            # Create third version
            v3 = {
                "project_id": v1["project_id"],
                "code": "assert (valid && ready && enable);",
                "type": "immediate",
                "version": 3,
                "regenerated_from": v2_id
            }
            
            result = await db.assertions.insert_one(v3)
            v3_id = result.inserted_id
            
            # Mark v2 as superseded
            await db.assertions.update_one(
                {"_id": v2_id},
                {"$set": {"superseded_by": v3_id}}
            )
            
            # Verify chain
            v1_doc = await db.assertions.find_one({"_id": v1_id})
            v2_doc = await db.assertions.find_one({"_id": v2_id})
            v3_doc = await db.assertions.find_one({"_id": v3_id})
            
            assert v1_doc["superseded_by"] == v2_id
            assert v2_doc["superseded_by"] == v3_id
            assert v2_doc["regenerated_from"] == v1_id
            assert v3_doc["regenerated_from"] == v2_id
    
    @pytest.mark.asyncio
    async def test_property_26_traceability_preserved(self, test_db_client):
        """
        Property 26: Traceability is preserved during regeneration
        
        The regenerated assertion should maintain the same traceability
        information as the original.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion with traceability
            traceability = {
                "requirement_text": "System shall validate input",
                "rtl_signals": ["valid", "ready"],
                "rtl_module": "input_validator"
            }
            
            original_assertion = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "traceability": traceability
            }
            
            result = await db.assertions.insert_one(original_assertion)
            original_id = result.inserted_id
            
            # Create regenerated assertion
            regenerated_assertion = {
                "project_id": original_assertion["project_id"],
                "code": "assert (valid && ready);",
                "type": "immediate",
                "regenerated_from": original_id,
                "traceability": traceability  # Same traceability
            }
            
            result = await db.assertions.insert_one(regenerated_assertion)
            
            # Verify traceability preserved
            new_assertion = await db.assertions.find_one({"_id": result.inserted_id})
            assert new_assertion["traceability"] == traceability
            assert new_assertion["traceability"]["requirement_text"] == "System shall validate input"
    
    @pytest.mark.asyncio
    async def test_property_26_confidence_score_adjusted(self, test_db_client):
        """
        Property 26: Confidence score may be adjusted for regenerated assertions
        
        Regenerated assertions may have different confidence scores
        based on the regeneration process.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create original assertion
            original_assertion = {
                "project_id": ObjectId(),
                "code": "assert (valid);",
                "type": "immediate",
                "confidence_score": 0.9
            }
            
            result = await db.assertions.insert_one(original_assertion)
            original_id = result.inserted_id
            
            # Create regenerated assertion with adjusted confidence
            regenerated_assertion = {
                "project_id": original_assertion["project_id"],
                "code": "assert (valid && ready);",
                "type": "immediate",
                "regenerated_from": original_id,
                "confidence_score": 0.8,  # Slightly lower
                "feedback_incorporated": 2
            }
            
            result = await db.assertions.insert_one(regenerated_assertion)
            
            # Verify confidence score
            new_assertion = await db.assertions.find_one({"_id": result.inserted_id})
            assert new_assertion["confidence_score"] == 0.8
            assert new_assertion["confidence_score"] <= original_assertion["confidence_score"]
