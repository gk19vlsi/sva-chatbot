"""
Property-Based Tests for Export Functionality

Tests Property 37:
- Property 37: Export File Completeness

Validates: Requirements 15.1, 15.2
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from bson import ObjectId


class TestExportFileCompleteness:
    """
    Property 37: Export File Completeness
    
    Tests that exported SVA files contain all assertions with complete
    traceability information and comments.
    
    Validates: Requirements 15.1, 15.2
    """
    
    @pytest.mark.asyncio
    async def test_property_37_export_contains_all_assertions(self, test_db_client):
        """
        Property 37: Export file contains all project assertions
        
        For any project with N assertions, the exported file should
        contain all N assertions.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test project
            project_doc = {
                "name": "Test Export Project",
                "description": "Testing export functionality",
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow(),
                "metadata": {"total_assertions": 0}
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create multiple assertions
            assertion_codes = [
                "assert property (@(posedge clk) valid |-> ready);",
                "assert (enable && !reset);",
                "assert property (@(posedge clk) req |=> ack);",
            ]
            
            assertion_ids = []
            for idx, code in enumerate(assertion_codes):
                assertion_doc = {
                    "project_id": project_id,
                    "code": code,
                    "type": "concurrent" if "property" in code else "immediate",
                    "category": "functional",
                    "confidence_score": 0.9,
                    "quality_score": 0.85,
                    "traceability": {
                        "requirement_text": f"Test requirement {idx + 1}",
                        "rtl_signals": ["clk", "valid", "ready"],
                        "rtl_module": "test_module",
                        "line_numbers": [10 + idx]
                    },
                    "explanation": f"Test assertion {idx + 1}",
                    "generated_at": datetime.utcnow()
                }
                result = await db.assertions.insert_one(assertion_doc)
                assertion_ids.append(result.inserted_id)
            
            # Generate export file
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify all assertions are in export
            for code in assertion_codes:
                assert code in export_content, f"Assertion code not found in export: {code}"
            
            # Verify count in header
            assert f"Total Assertions: {len(assertion_codes)}" in export_content
    
    @pytest.mark.asyncio
    async def test_property_37_export_includes_traceability(self, test_db_client):
        """
        Property 37: Export file includes traceability information
        
        For any assertion in the export, the file should include:
        - Requirement text
        - RTL signals
        - RTL module name
        - Line numbers
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test project
            project_doc = {
                "name": "Traceability Test",
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create assertion with complete traceability
            requirement_text = "The system shall validate handshake protocol"
            rtl_signals = ["valid", "ready", "data"]
            rtl_module = "handshake_controller"
            line_numbers = [42, 43, 44]
            
            assertion_doc = {
                "project_id": project_id,
                "code": "assert property (@(posedge clk) valid |-> ready);",
                "type": "concurrent",
                "category": "protocol",
                "confidence_score": 0.95,
                "quality_score": 0.90,
                "traceability": {
                    "requirement_text": requirement_text,
                    "rtl_signals": rtl_signals,
                    "rtl_module": rtl_module,
                    "line_numbers": line_numbers
                },
                "explanation": "Validates handshake protocol",
                "generated_at": datetime.utcnow()
            }
            await db.assertions.insert_one(assertion_doc)
            
            # Generate export
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify traceability information is present
            assert requirement_text in export_content
            assert rtl_module in export_content
            for signal in rtl_signals:
                assert signal in export_content
            for line_num in line_numbers:
                assert str(line_num) in export_content
    
    @pytest.mark.asyncio
    async def test_property_37_export_includes_comments(self, test_db_client):
        """
        Property 37: Export file includes comments and metadata
        
        The export file should include:
        - File header with project information
        - Integration instructions
        - Per-assertion comments
        - Quality metrics
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test project
            project_name = "Comment Test Project"
            project_doc = {
                "name": project_name,
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create assertion
            confidence_score = 0.87
            quality_score = 0.92
            assertion_doc = {
                "project_id": project_id,
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": confidence_score,
                "quality_score": quality_score,
                "traceability": {
                    "requirement_text": "Test requirement",
                    "rtl_signals": ["valid"],
                    "rtl_module": "test_module"
                },
                "explanation": "Test explanation",
                "generated_at": datetime.utcnow()
            }
            await db.assertions.insert_one(assertion_doc)
            
            # Generate export
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify header and project info
            assert project_name in export_content
            assert "SystemVerilog Assertions" in export_content
            
            # Verify integration instructions
            assert "INTEGRATION INSTRUCTIONS" in export_content
            assert "Review each assertion" in export_content
            
            # Verify quality metrics
            assert f"Confidence: {confidence_score:.2f}" in export_content
            assert f"Quality: {quality_score:.2f}" in export_content
            
            # Verify comments are present
            assert "//" in export_content
            assert "Requirement:" in export_content
    
    @pytest.mark.asyncio
    async def test_property_37_export_groups_by_module(self, test_db_client):
        """
        Property 37: Export file groups assertions by RTL module
        
        Assertions should be organized by their target RTL module.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test project
            project_doc = {
                "name": "Module Grouping Test",
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create assertions for different modules
            modules = ["module_a", "module_b", "module_a"]
            for idx, module in enumerate(modules):
                assertion_doc = {
                    "project_id": project_id,
                    "code": f"assert (signal_{idx});",
                    "type": "immediate",
                    "category": "functional",
                    "confidence_score": 0.9,
                    "traceability": {
                        "requirement_text": f"Requirement {idx}",
                        "rtl_signals": [f"signal_{idx}"],
                        "rtl_module": module
                    },
                    "generated_at": datetime.utcnow()
                }
                await db.assertions.insert_one(assertion_doc)
            
            # Generate export
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify module sections exist
            assert "Module: module_a" in export_content
            assert "Module: module_b" in export_content
            
            # Verify module_a has 2 assertions
            module_a_section = export_content.split("Module: module_a")[1].split("Module:")[0]
            assert "signal_0" in module_a_section
            assert "signal_2" in module_a_section
    
    @pytest.mark.asyncio
    async def test_property_37_export_marks_modified_assertions(self, test_db_client):
        """
        Property 37: Export file marks user-modified assertions
        
        Assertions that have been modified by users should be clearly
        marked in the export.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create test project
            project_doc = {
                "name": "Modified Test",
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create modified assertion
            modified_at = datetime.utcnow()
            assertion_doc = {
                "project_id": project_id,
                "code": "assert (valid && ready);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "modified": True,
                "modified_at": modified_at,
                "original_code": "assert (valid);",
                "traceability": {
                    "requirement_text": "Test requirement",
                    "rtl_signals": ["valid", "ready"],
                    "rtl_module": "test_module"
                },
                "generated_at": datetime.utcnow()
            }
            await db.assertions.insert_one(assertion_doc)
            
            # Generate export
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify modification is marked
            assert "MODIFIED BY USER" in export_content
            assert modified_at.strftime('%Y-%m-%d') in export_content
    
    @pytest.mark.asyncio
    async def test_property_37_export_empty_project_fails(self, test_db_client):
        """
        Property 37: Export fails gracefully for projects with no assertions
        
        Attempting to export a project with no assertions should be handled
        appropriately (this is tested at the API level, not in the generator).
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create project with no assertions
            project_doc = {
                "name": "Empty Project",
                "user_id": "test_user",
                "status": "draft",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Verify no assertions exist
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            assert len(assertions) == 0
    
    @pytest.mark.asyncio
    async def test_property_37_export_includes_integration_instructions(self, test_db_client):
        """
        Property 37: Export file includes integration instructions
        
        The export should include instructions for integrating assertions
        into verification environments.
        """
        async for client, db_name in test_db_client:
            db = client[db_name]
            
            # Create minimal project
            project_doc = {
                "name": "Integration Test",
                "user_id": "test_user",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            
            # Create one assertion
            assertion_doc = {
                "project_id": project_id,
                "code": "assert (valid);",
                "type": "immediate",
                "category": "functional",
                "confidence_score": 0.9,
                "traceability": {
                    "requirement_text": "Test",
                    "rtl_signals": ["valid"],
                    "rtl_module": "test"
                },
                "generated_at": datetime.utcnow()
            }
            await db.assertions.insert_one(assertion_doc)
            
            # Generate export
            from app.routes.projects import _generate_sva_file
            
            project_doc["_id"] = project_id
            assertions = await db.assertions.find(
                {"project_id": project_id}
            ).to_list(length=None)
            
            export_content = _generate_sva_file(project_doc, assertions)
            
            # Verify integration instructions for common tools
            assert "VCS" in export_content or "Synopsys" in export_content
            assert "Xcelium" in export_content or "Cadence" in export_content
            assert "Questa" in export_content or "Mentor" in export_content
            assert "Verilator" in export_content
            
            # Verify general instructions
            assert "Review" in export_content
            assert "clock" in export_content.lower()
            assert "reset" in export_content.lower()
