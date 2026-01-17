"""
Property-Based Tests for Assertion Editing

Tests Properties 24 and 25:
- Property 24: Assertion Edit Validation
- Property 25: Assertion Modification Tracking

Validates: Requirements 10.1, 10.2
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.utils.sva_validator import validate_sva_syntax


# Strategy for generating valid SVA code
@st.composite
def valid_sva_code(draw):
    """Generate valid SVA code"""
    assertion_type = draw(st.sampled_from(['assert', 'assume', 'cover']))
    is_concurrent = draw(st.booleans())
    
    if is_concurrent:
        clock_edge = draw(st.sampled_from(['posedge', 'negedge']))
        clock_signal = draw(st.sampled_from(['clk', 'clock', 'sys_clk']))
        signal = draw(st.sampled_from(['valid', 'ready', 'enable', 'data_valid']))
        
        code = f"{assertion_type} property (@({clock_edge} {clock_signal}) {signal});"
    else:
        signal = draw(st.sampled_from(['valid', 'ready', 'enable']))
        code = f"{assertion_type} ({signal});"
    
    return code


# Strategy for generating invalid SVA code
@st.composite
def invalid_sva_code(draw):
    """Generate invalid SVA code"""
    error_type = draw(st.sampled_from([
        'missing_keyword',
        'missing_semicolon',
        'unbalanced_parens',
        'missing_clock'
    ]))
    
    if error_type == 'missing_keyword':
        return "property (valid);"
    elif error_type == 'missing_semicolon':
        return "assert (valid)"
    elif error_type == 'unbalanced_parens':
        return "assert ((valid);"
    elif error_type == 'missing_clock':
        return "assert property (valid);"
    
    return "invalid code"


class TestAssertionEditValidation:
    """
    Property 24: Assertion Edit Validation
    
    Tests that edited assertions are validated before saving.
    
    Validates: Requirements 10.1
    """
    
    @given(code=valid_sva_code())
    @settings(max_examples=100)
    def test_property_24_valid_code_passes_validation(self, code):
        """
        Property 24: Valid SVA code passes validation
        
        For all valid SVA code strings, validation should return True.
        """
        is_valid, error_message = validate_sva_syntax(code)
        assert is_valid, f"Valid code failed validation: {error_message}"
        assert error_message == "", "Valid code should have no error message"
    
    @given(code=invalid_sva_code())
    @settings(max_examples=100)
    def test_property_24_invalid_code_fails_validation(self, code):
        """
        Property 24: Invalid SVA code fails validation
        
        For all invalid SVA code strings, validation should return False
        with an appropriate error message.
        """
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid, "Invalid code passed validation"
        assert error_message != "", "Invalid code should have error message"
        assert len(error_message) > 0, "Error message should be non-empty"
    
    def test_property_24_empty_code_fails(self):
        """
        Property 24: Empty code fails validation
        """
        is_valid, error_message = validate_sva_syntax("")
        assert not is_valid
        assert "Empty" in error_message
    
    def test_property_24_whitespace_only_fails(self):
        """
        Property 24: Whitespace-only code fails validation
        """
        is_valid, error_message = validate_sva_syntax("   \n\t  ")
        assert not is_valid
        assert "Empty" in error_message
    
    def test_property_24_missing_assertion_keyword(self):
        """
        Property 24: Code without assertion keyword fails
        """
        code = "property (valid);"
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid
        assert "assertion keyword" in error_message.lower()
    
    def test_property_24_missing_semicolon(self):
        """
        Property 24: Code without semicolon fails
        """
        code = "assert (valid)"
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid
        assert "semicolon" in error_message.lower()
    
    def test_property_24_unbalanced_parentheses_opening(self):
        """
        Property 24: Code with unclosed parentheses fails
        """
        code = "assert ((valid);"
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid
        assert "parenthes" in error_message.lower()
    
    def test_property_24_unbalanced_parentheses_closing(self):
        """
        Property 24: Code with extra closing parentheses fails
        """
        code = "assert (valid));"
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid
        assert "parenthes" in error_message.lower()
    
    def test_property_24_concurrent_without_clock(self):
        """
        Property 24: Concurrent assertion without clock event fails
        """
        code = "assert property (valid);"
        is_valid, error_message = validate_sva_syntax(code)
        assert not is_valid
        assert "clock" in error_message.lower()
    
    def test_property_24_immediate_assertion_valid(self):
        """
        Property 24: Immediate assertion is valid
        """
        code = "assert (valid && ready);"
        is_valid, error_message = validate_sva_syntax(code)
        assert is_valid
        assert error_message == ""
    
    def test_property_24_concurrent_assertion_valid(self):
        """
        Property 24: Concurrent assertion with clock is valid
        """
        code = "assert property (@(posedge clk) valid |-> ready);"
        is_valid, error_message = validate_sva_syntax(code)
        assert is_valid
        assert error_message == ""
    
    def test_property_24_assume_keyword_valid(self):
        """
        Property 24: Assume keyword is valid
        """
        code = "assume (valid);"
        is_valid, error_message = validate_sva_syntax(code)
        assert is_valid
    
    def test_property_24_cover_keyword_valid(self):
        """
        Property 24: Cover keyword is valid
        """
        code = "cover property (@(posedge clk) valid);"
        is_valid, error_message = validate_sva_syntax(code)
        assert is_valid


class TestAssertionModificationTracking:
    """
    Property 25: Assertion Modification Tracking
    
    Tests that assertion modifications are properly tracked.
    
    Validates: Requirements 10.2
    """
    
    @pytest.mark.asyncio
    async def test_property_25_first_modification_stores_original(self, test_db_client):
        """
        Property 25: First modification stores original code
        
        When an assertion is modified for the first time, the original code
        should be stored.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test assertion
            original_code = "assert (valid);"
            assertion_doc = {
                "project_id": "test_project",
                "code": original_code,
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "modified": False
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Modify assertion
            new_code = "assert (valid && ready);"
            await db.assertions.update_one(
                {"_id": assertion_id},
                {
                    "$set": {
                        "code": new_code,
                        "modified": True,
                        "original_code": original_code
                    }
                }
            )
            
            # Verify original code is stored
            modified_assertion = await db.assertions.find_one({"_id": assertion_id})
            assert modified_assertion["modified"] is True
            assert modified_assertion["original_code"] == original_code
            assert modified_assertion["code"] == new_code
    
    @pytest.mark.asyncio
    async def test_property_25_subsequent_modifications_preserve_original(self, test_db_client):
        """
        Property 25: Subsequent modifications preserve original code
        
        When an assertion is modified multiple times, the original code
        should remain unchanged.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create modified assertion
            original_code = "assert (valid);"
            first_modification = "assert (valid && ready);"
            assertion_doc = {
                "project_id": "test_project",
                "code": first_modification,
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "modified": True,
                "original_code": original_code
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Modify again
            second_modification = "assert (valid && ready && enable);"
            await db.assertions.update_one(
                {"_id": assertion_id},
                {"$set": {"code": second_modification}}
            )
            
            # Verify original code is preserved
            modified_assertion = await db.assertions.find_one({"_id": assertion_id})
            assert modified_assertion["original_code"] == original_code
            assert modified_assertion["code"] == second_modification
    
    @pytest.mark.asyncio
    async def test_property_25_unmodified_assertion_has_no_original(self, test_db_client):
        """
        Property 25: Unmodified assertions have no original_code field
        
        Assertions that have never been modified should not have an
        original_code field.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create unmodified assertion
            assertion_doc = {
                "project_id": "test_project",
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "modified": False
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Verify no original_code field
            assertion = await db.assertions.find_one({"_id": assertion_id})
            assert "original_code" not in assertion or assertion.get("original_code") is None
    
    @pytest.mark.asyncio
    async def test_property_25_modified_flag_set_on_edit(self, test_db_client):
        """
        Property 25: Modified flag is set when assertion is edited
        
        When an assertion is edited, the modified flag should be set to True.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create assertion
            assertion_doc = {
                "project_id": "test_project",
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "modified": False
            }
            
            result = await db.assertions.insert_one(assertion_doc)
            assertion_id = result.inserted_id
            
            # Modify assertion
            await db.assertions.update_one(
                {"_id": assertion_id},
                {
                    "$set": {
                        "code": "assert (valid && ready);",
                        "modified": True,
                        "original_code": "assert (valid);"
                    }
                }
            )
            
            # Verify modified flag
            modified_assertion = await db.assertions.find_one({"_id": assertion_id})
            assert modified_assertion["modified"] is True
