"""
Property-Based Tests for Orchestrator

Tests universal properties that must hold for all pipeline orchestration operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.agents.orchestrator import Orchestrator, PipelineResult
from app.agents.base import PipelineContext, AgentResult
from app.clients.groq_client import GroqClient
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
import asyncio


@pytest.mark.asyncio
@given(project_id=st.text(min_size=24, max_size=24, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))))
@settings(max_examples=20, deadline=None)
async def test_agent_pipeline_sequencing(project_id):
    """
    Property 38: Agent Pipeline Sequencing
    
    Universal Property:
    For any generation request, the orchestrator should execute agents
    in the correct sequence: Spec Parser → RTL Analyzer → Alignment → 
    SVA Generator → Validator.
    
    Validates: Requirements 16.1, 16.2
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    mock_db.pipeline_executions.insert_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Track agent execution order
    execution_order = []
    
    # Mock each agent's execute method to track order
    async def mock_execute(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            execution_order.append(agent_name)
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data={f"{agent_name}_result": "success"},
                execution_time=0.1
            )
        return execute
    
    # Patch all agent execute methods
    orchestrator.agents["spec_parser"].execute = await mock_execute("spec_parser")
    orchestrator.agents["rtl_analyzer"].execute = await mock_execute("rtl_analyzer")
    orchestrator.agents["alignment"].execute = await mock_execute("alignment")
    orchestrator.agents["sva_generator"].execute = await mock_execute("sva_generator")
    orchestrator.agents["validation"].execute = await mock_execute("validation")
    
    # Execute pipeline
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must execute successfully
    assert result.success, f"Pipeline failed: {result.error}"
    
    # Property: All five agents must execute
    assert len(execution_order) == 5, \
        f"Expected 5 agents to execute, got {len(execution_order)}"
    
    # Property: Agents must execute in correct sequence
    expected_sequence = ["spec_parser", "rtl_analyzer", "alignment", "sva_generator", "validation"]
    assert execution_order == expected_sequence, \
        f"Agent execution order incorrect. Expected {expected_sequence}, got {execution_order}"
    
    # Property: All agent results must be recorded
    assert len(result.agent_results) == 5, \
        f"Expected 5 agent results, got {len(result.agent_results)}"
    
    # Property: Agent results must be in correct order
    result_names = [r.agent_name for r in result.agent_results]
    assert result_names == expected_sequence, \
        f"Agent result order incorrect. Expected {expected_sequence}, got {result_names}"
    
    # Property: Each agent must report success
    for agent_result in result.agent_results:
        assert agent_result.success, \
            f"Agent {agent_result.agent_name} failed: {agent_result.error}"


@pytest.mark.asyncio
async def test_pipeline_context_passing():
    """
    Test that context is correctly passed between agents.
    
    Part of Property 38: Agent Pipeline Sequencing
    Validates: Requirement 16.2
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    mock_db.pipeline_executions.insert_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Track context data passed to each agent
    context_snapshots = []
    
    # Mock agent execute methods to capture context
    async def mock_execute_with_context(agent_name, data_to_add):
        async def execute(context: PipelineContext) -> AgentResult:
            # Capture current context data
            context_snapshots.append({
                "agent": agent_name,
                "context_data": dict(context.data)
            })
            
            # Return result with new data
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data=data_to_add,
                execution_time=0.1
            )
        return execute
    
    # Setup agents with different data contributions
    orchestrator.agents["spec_parser"].execute = await mock_execute_with_context(
        "spec_parser", {"requirements": ["req1", "req2"]}
    )
    orchestrator.agents["rtl_analyzer"].execute = await mock_execute_with_context(
        "rtl_analyzer", {"modules": ["mod1"]}
    )
    orchestrator.agents["alignment"].execute = await mock_execute_with_context(
        "alignment", {"alignments": ["align1"]}
    )
    orchestrator.agents["sva_generator"].execute = await mock_execute_with_context(
        "sva_generator", {"assertions": ["assert1"]}
    )
    orchestrator.agents["validation"].execute = await mock_execute_with_context(
        "validation", {"validated": True}
    )
    
    # Execute pipeline
    project_id = str(ObjectId())
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must succeed
    assert result.success
    
    # Property: First agent should receive empty context
    assert context_snapshots[0]["agent"] == "spec_parser"
    assert context_snapshots[0]["context_data"] == {}
    
    # Property: Second agent should receive first agent's data
    assert context_snapshots[1]["agent"] == "rtl_analyzer"
    assert "requirements" in context_snapshots[1]["context_data"]
    
    # Property: Third agent should receive accumulated data
    assert context_snapshots[2]["agent"] == "alignment"
    assert "requirements" in context_snapshots[2]["context_data"]
    assert "modules" in context_snapshots[2]["context_data"]
    
    # Property: Final data should contain all agent contributions
    assert "requirements" in result.final_data
    assert "modules" in result.final_data
    assert "alignments" in result.final_data
    assert "assertions" in result.final_data
    assert "validated" in result.final_data


@pytest.mark.asyncio
async def test_pipeline_stops_on_agent_failure():
    """
    Test that pipeline stops when an agent fails.
    
    Part of Property 38: Agent Pipeline Sequencing
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    mock_db.pipeline_executions.insert_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Track execution
    execution_order = []
    
    # Mock agents - second agent fails
    async def mock_success(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            execution_order.append(agent_name)
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data={},
                execution_time=0.1
            )
        return execute
    
    async def mock_failure(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            execution_order.append(agent_name)
            return AgentResult(
                agent_name=agent_name,
                success=False,
                error="Simulated failure",
                execution_time=0.1
            )
        return execute
    
    # First agent succeeds, second fails
    orchestrator.agents["spec_parser"].execute = await mock_success("spec_parser")
    orchestrator.agents["rtl_analyzer"].execute = await mock_failure("rtl_analyzer")
    orchestrator.agents["alignment"].execute = await mock_success("alignment")
    orchestrator.agents["sva_generator"].execute = await mock_success("sva_generator")
    orchestrator.agents["validation"].execute = await mock_success("validation")
    
    # Execute pipeline
    project_id = str(ObjectId())
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must fail
    assert not result.success
    
    # Property: First agent executes once, second agent retries 3 times (total 4 executions)
    # Remaining agents should not execute
    assert len(execution_order) == 4  # 1 spec_parser + 3 rtl_analyzer retries
    assert execution_order[0] == "spec_parser"
    assert all(name == "rtl_analyzer" for name in execution_order[1:])
    
    # Property: Only first two agent types should be in results
    agent_types = set(execution_order)
    assert agent_types == {"spec_parser", "rtl_analyzer"}
    
    # Property: Error message should indicate which agent failed
    assert "rtl_analyzer" in result.error


if __name__ == "__main__":
    print("Run with: pytest tests/test_orchestrator_properties.py -v")



@pytest.mark.asyncio
@given(
    project_id=st.text(min_size=24, max_size=24, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))),
    failure_count=st.integers(min_value=1, max_value=2)
)
@settings(max_examples=20, deadline=None)
async def test_agent_retry_with_exponential_backoff(project_id, failure_count):
    """
    Property 39: Agent Retry with Exponential Backoff
    
    Universal Property:
    For any agent execution that fails, the orchestrator should retry
    up to 3 times with exponentially increasing delays between attempts.
    
    Validates: Requirements 16.3, 19.3
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    mock_db.pipeline_executions.insert_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Track retry attempts and delays
    attempt_times = []
    
    # Mock agent that fails N times then succeeds
    attempts = [0]  # Use list to allow modification in closure
    
    async def mock_execute_with_retries(context: PipelineContext) -> AgentResult:
        attempt_times.append(asyncio.get_event_loop().time())
        attempts[0] += 1
        
        if attempts[0] <= failure_count:
            # Fail on first N attempts
            return AgentResult(
                agent_name="spec_parser",
                success=False,
                error=f"Simulated failure {attempts[0]}",
                execution_time=0.01
            )
        else:
            # Succeed on final attempt
            return AgentResult(
                agent_name="spec_parser",
                success=True,
                data={"requirements": []},
                execution_time=0.01
            )
    
    # Mock other agents to succeed immediately
    async def mock_success(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data={},
                execution_time=0.01
            )
        return execute
    
    orchestrator.agents["spec_parser"].execute = mock_execute_with_retries
    orchestrator.agents["rtl_analyzer"].execute = await mock_success("rtl_analyzer")
    orchestrator.agents["alignment"].execute = await mock_success("alignment")
    orchestrator.agents["sva_generator"].execute = await mock_success("sva_generator")
    orchestrator.agents["validation"].execute = await mock_success("validation")
    
    # Execute pipeline
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline should eventually succeed (after retries)
    assert result.success, f"Pipeline failed after retries: {result.error}"
    
    # Property: Number of attempts should be failure_count + 1 (final success)
    assert attempts[0] == failure_count + 1, \
        f"Expected {failure_count + 1} attempts, got {attempts[0]}"
    
    # Property: There should be delays between attempts (exponential backoff)
    if len(attempt_times) > 1:
        for i in range(1, len(attempt_times)):
            delay = attempt_times[i] - attempt_times[i-1]
            # Expected delay is 2^(i-1) seconds (1s, 2s, 4s, ...)
            expected_min_delay = 2 ** (i - 1) * 0.9  # Allow 10% tolerance
            assert delay >= expected_min_delay, \
                f"Delay between attempts {i-1} and {i} too short: {delay}s < {expected_min_delay}s"


@pytest.mark.asyncio
async def test_agent_retry_exhaustion():
    """
    Test that agent fails after exhausting all retry attempts.
    
    Part of Property 39: Agent Retry with Exponential Backoff
    Validates: Requirement 16.3
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    mock_db.pipeline_executions.insert_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Track attempts
    attempts = [0]
    
    # Mock agent that always fails
    async def mock_always_fail(context: PipelineContext) -> AgentResult:
        attempts[0] += 1
        return AgentResult(
            agent_name="spec_parser",
            success=False,
            error="Persistent failure",
            execution_time=0.01
        )
    
    orchestrator.agents["spec_parser"].execute = mock_always_fail
    
    # Execute pipeline
    project_id = str(ObjectId())
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must fail
    assert not result.success
    
    # Property: Agent should be retried exactly 3 times
    assert attempts[0] == 3, f"Expected 3 retry attempts, got {attempts[0]}"
    
    # Property: Error should be reported
    assert result.error is not None
    assert "spec_parser" in result.error


@pytest.mark.asyncio
@given(project_id=st.text(min_size=24, max_size=24, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))))
@settings(max_examples=20, deadline=None)
async def test_agent_performance_metrics_tracking(project_id):
    """
    Property 40: Agent Performance Metrics Tracking
    
    Universal Property:
    For any agent execution, the orchestrator should record the execution
    time and store it in the metrics collection.
    
    Validates: Requirement 16.5
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    
    # Track what gets inserted into database
    inserted_metrics = []
    
    async def capture_insert(doc):
        inserted_metrics.append(doc)
        return MagicMock(_id=ObjectId())
    
    mock_db.pipeline_executions.insert_one = capture_insert
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Mock all agents to succeed with known execution times
    async def mock_execute(agent_name, exec_time):
        async def execute(context: PipelineContext) -> AgentResult:
            await asyncio.sleep(exec_time)  # Simulate work
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data={},
                execution_time=exec_time
            )
        return execute
    
    orchestrator.agents["spec_parser"].execute = await mock_execute("spec_parser", 0.1)
    orchestrator.agents["rtl_analyzer"].execute = await mock_execute("rtl_analyzer", 0.15)
    orchestrator.agents["alignment"].execute = await mock_execute("alignment", 0.12)
    orchestrator.agents["sva_generator"].execute = await mock_execute("sva_generator", 0.18)
    orchestrator.agents["validation"].execute = await mock_execute("validation", 0.11)
    
    # Execute pipeline
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must succeed
    assert result.success
    
    # Property: Metrics must be recorded in database
    assert len(inserted_metrics) == 1, \
        f"Expected 1 metrics record, got {len(inserted_metrics)}"
    
    metrics = inserted_metrics[0]
    
    # Property: Metrics must include project_id
    assert metrics["project_id"] == project_id
    
    # Property: Metrics must include success status
    assert "success" in metrics
    assert metrics["success"] == True
    
    # Property: Metrics must include total execution time
    assert "total_execution_time" in metrics
    assert metrics["total_execution_time"] > 0
    
    # Property: Metrics must include agent count
    assert "agent_count" in metrics
    assert metrics["agent_count"] == 5
    
    # Property: Metrics must include per-agent metrics
    assert "agent_metrics" in metrics
    assert len(metrics["agent_metrics"]) == 5
    
    # Property: Each agent metric must have required fields
    for agent_metric in metrics["agent_metrics"]:
        assert "agent_name" in agent_metric
        assert "success" in agent_metric
        assert "execution_time" in agent_metric
        assert agent_metric["execution_time"] > 0
    
    # Property: Agent names in metrics must match pipeline sequence
    agent_names = [m["agent_name"] for m in metrics["agent_metrics"]]
    expected_names = ["spec_parser", "rtl_analyzer", "alignment", "sva_generator", "validation"]
    assert agent_names == expected_names


@pytest.mark.asyncio
async def test_metrics_tracking_on_failure():
    """
    Test that metrics are tracked even when pipeline fails.
    
    Part of Property 40: Agent Performance Metrics Tracking
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.pipeline_executions = AsyncMock()
    
    inserted_metrics = []
    
    async def capture_insert(doc):
        inserted_metrics.append(doc)
        return MagicMock(_id=ObjectId())
    
    mock_db.pipeline_executions.insert_one = capture_insert
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create orchestrator
    orchestrator = Orchestrator(groq_client=mock_groq_client, db=mock_db)
    
    # Mock agents - second one fails
    async def mock_success(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            return AgentResult(
                agent_name=agent_name,
                success=True,
                data={},
                execution_time=0.1
            )
        return execute
    
    async def mock_failure(agent_name):
        async def execute(context: PipelineContext) -> AgentResult:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                error="Test failure",
                execution_time=0.1
            )
        return execute
    
    orchestrator.agents["spec_parser"].execute = await mock_success("spec_parser")
    orchestrator.agents["rtl_analyzer"].execute = await mock_failure("rtl_analyzer")
    orchestrator.agents["alignment"].execute = await mock_success("alignment")
    orchestrator.agents["sva_generator"].execute = await mock_success("sva_generator")
    orchestrator.agents["validation"].execute = await mock_success("validation")
    
    # Execute pipeline
    project_id = str(ObjectId())
    result = await orchestrator.execute_pipeline(project_id=project_id)
    
    # Property: Pipeline must fail
    assert not result.success
    
    # Property: Metrics must still be recorded
    assert len(inserted_metrics) == 1
    
    metrics = inserted_metrics[0]
    
    # Property: Metrics must show failure
    assert metrics["success"] == False
    
    # Property: Error must be recorded
    assert "error" in metrics
    assert metrics["error"] is not None
    
    # Property: Partial agent metrics must be recorded
    assert len(metrics["agent_metrics"]) == 2  # Only first two agents executed
