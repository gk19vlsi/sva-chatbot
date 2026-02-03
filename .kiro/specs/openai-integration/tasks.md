# Implementation Plan: OpenAI Integration

## Overview

This implementation plan adds OpenAI API support to the SVA-Chatbot project as an alternative LLM provider. The approach follows a layered strategy: first establishing the foundation (configuration, base interfaces), then implementing the OpenAI client, creating the factory pattern, and finally integrating with existing agents. Each step builds incrementally and includes validation through tests.

## Tasks

- [ ] 1. Update configuration and dependencies
  - [x] 1.1 Add OpenAI configuration settings to Settings class
    - Add `llm_provider`, `openai_api_key`, `openai_primary_model`, `openai_fallback_model` fields to `backend/app/config.py`
    - Set default values: `llm_provider="groq"`, `openai_primary_model="gpt-4o"`, `openai_fallback_model="gpt-4o-mini"`
    - Ensure backward compatibility by making OpenAI settings optional with empty string defaults
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 1.2 Update .env.example with OpenAI configuration
    - Add `LLM_PROVIDER` setting with example values and comments
    - Add `OPENAI_API_KEY` with placeholder text
    - Add `OPENAI_PRIMARY_MODEL` and `OPENAI_FALLBACK_MODEL` with recommended defaults
    - Add explanatory comments for each OpenAI configuration option
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 1.3 Add openai package to requirements.txt
    - Add `openai>=1.0.0` to requirements.txt (supports async operations and Python 3.8+)
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 2. Create base LLM client interface
  - [x] 2.1 Define LLMClient Protocol
    - Create `backend/app/clients/base.py` with LLMClient Protocol class
    - Define method signatures: `chat_completion`, `chat_completion_with_fallback`, `get_token_usage`, `close`
    - Use `typing.Protocol` and `@runtime_checkable` decorator for type safety
    - Add comprehensive docstrings for each method
    - _Requirements: 1.1, 4.4_
  - [x] 2.2 Create LLMAPIError exception class
    - Add `LLMAPIError` exception class to `backend/app/clients/base.py`
    - Include fields: `message`, `provider`, `status_code`, `original_error`
    - Format error messages as `[provider] message`
    - _Requirements: 1.4, 9.1, 9.2_

- [ ] 3. Implement OpenAI client
  - [x] 3.1 Create OpenAIClient class structure
    - Create `backend/app/clients/openai_client.py`
    - Implement `__init__` method with AsyncOpenAI client initialization
    - Set up instance variables: `client`, `primary_model`, `fallback_model`, `_token_usage`
    - Add session management methods: `close`, `__aenter__`, `__aexit__`
    - _Requirements: 1.1, 1.8_
  - [x] 3.2 Implement chat_completion method
    - Implement cache checking using existing `llm_cache` utility
    - Make API call to OpenAI using `client.chat.completions.create()`
    - Track token usage per project_id
    - Log request and response with structured logging
    - Track metrics using existing `track_llm_request` utility
    - Cache successful responses
    - Handle errors and raise `LLMAPIError` with provider name
    - Return response in standardized format matching GroqClient
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 10.1, 10.4, 11.1, 11.3, 11.4_
  - [x] 3.3 Implement chat_completion_with_fallback method
    - Try primary model first
    - Catch errors and check for rate limit conditions
    - Implement aggressive fallback logic for rate limits
    - Fall back to secondary model on failure
    - Log fallback attempts with reason
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 3.4 Implement token usage tracking methods
    - Implement `_track_token_usage` private method
    - Implement `get_token_usage` public method
    - Follow same pattern as GroqClient for consistency
    - _Requirements: 10.2, 10.3_
  - [x] 3.5 Write property tests for OpenAI client
    - **Property 1: Response Format Consistency**
    - **Property 2: API Call Correctness**
    - **Property 3: Error Handling**
    - **Property 4: Token Usage Tracking**
    - **Property 5: Response Caching**
    - **Property 6: Request and Response Logging**
    - **Property 7: Model Fallback Behavior**
    - Use Hypothesis to generate random messages, parameters, and scenarios
    - Mock OpenAI API responses for testing
    - Configure tests to run minimum 100 iterations
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 10.1, 10.2, 10.3, 10.4_
  - [x] 3.6 Write unit tests for OpenAI client
    - Test initialization with valid and invalid API keys
    - Test async context manager behavior
    - Test specific error scenarios (auth failure, network error, invalid model)
    - Test cache hit and miss scenarios
    - _Requirements: 1.4, 1.6, 1.8_

- [x] 4. Checkpoint - Ensure OpenAI client tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Create LLM client factory
  - [x] 5.1 Implement LLMClientFactory class
    - Create `backend/app/clients/factory.py`
    - Implement `create_client()` static method
    - Add provider validation logic (accept "groq" or "openai")
    - Add API key validation for selected provider
    - Return appropriate client instance based on `settings.llm_provider`
    - Raise `ValueError` for invalid configurations with clear messages
    - Implement `get_provider_name()` static method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 3.5_
  - [x] 5.2 Write property tests for factory
    - **Property 8: Configuration Validation**
    - Test with various invalid provider names and missing API keys
    - Use Hypothesis to generate random invalid configurations
    - _Requirements: 3.1, 3.5, 4.3_
  - [x] 5.3 Write unit tests for factory
    - Test factory creates GroqClient when provider is "groq"
    - Test factory creates OpenAIClient when provider is "openai"
    - Test factory raises error for invalid provider
    - Test factory raises error when API key is missing
    - Test default provider behavior (should be "groq")
    - _Requirements: 4.1, 4.2, 4.3, 3.2, 8.1_

- [ ] 6. Update agents to use factory
  - [x] 6.1 Update Orchestrator to use LLMClientFactory
    - Modify `backend/app/agents/orchestrator.py`
    - Replace direct GroqClient instantiation with `LLMClientFactory.create_client()`
    - Update initialization to pass factory-created client to all agents
    - Add startup logging to show which provider is being used
    - _Requirements: 5.1, 5.4, 9.4_
  - [x] 6.2 Verify agent compatibility with both providers
    - Ensure all agents (SpecificationParserAgent, RTLAnalyzerAgent, AlignmentAgent, SVAGeneratorAgent, ValidationAgent) accept client through constructor
    - Verify agents use client interface methods without provider-specific code
    - _Requirements: 5.2, 5.3_
  - [x] 6.3 Write property tests for provider switching
    - **Property 9: Provider Switching**
    - Test agent operations with both Groq and OpenAI configurations
    - Use Hypothesis to generate random agent inputs
    - Mock both provider APIs to verify agents work with either
    - _Requirements: 5.3_
  - [x] 6.4 Write integration tests for agent initialization
    - Test Orchestrator initializes with Groq provider
    - Test Orchestrator initializes with OpenAI provider
    - Test agents receive correct client type
    - _Requirements: 5.1, 5.4_

- [x] 7. Checkpoint - Ensure agent integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Add backward compatibility validation
  - [x] 8.1 Write property tests for backward compatibility
    - **Property 10: Backward Compatibility**
    - Test system operations with Groq-only configuration
    - Test system operations with LLM_PROVIDER omitted (should default to Groq)
    - Test system operations with only GROQ_API_KEY provided
    - Verify GroqClient interface hasn't changed
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 8.2 Write unit tests for configuration defaults
    - Test default provider is "groq" when LLM_PROVIDER not specified
    - Test system starts without OpenAI configuration when using Groq
    - Test GroqClient still works as before
    - _Requirements: 3.2, 8.1, 8.4_

- [ ] 9. Add performance metrics tracking
  - [x] 9.1 Ensure OpenAI client integrates with metrics system
    - Verify `track_llm_request` is called for all OpenAI API calls
    - Verify `log_llm_request` includes provider name in logs
    - Verify request duration is tracked
    - Verify success/failure rates are tracked
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [x] 9.2 Write property tests for performance metrics
    - **Property 11: Performance Metrics Tracking**
    - Test metrics are tracked for random API calls
    - Test metrics include provider name
    - Test duration tracking accuracy
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 10. Update documentation files
  - [x] 10.1 Verify .env.example is complete
    - Ensure all OpenAI configuration options are documented
    - Ensure comments are clear and helpful
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 10.2 Verify requirements.txt is updated
    - Ensure openai package is included with correct version
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 10.3 Write unit tests for documentation files
    - Test .env.example contains LLM_PROVIDER
    - Test .env.example contains OPENAI_API_KEY
    - Test .env.example contains OPENAI_PRIMARY_MODEL
    - Test .env.example contains OPENAI_FALLBACK_MODEL
    - Test requirements.txt contains openai package
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1_

- [x] 11. Final checkpoint - Run full test suite
  - Ensure all unit tests pass
  - Ensure all property tests pass
  - Ensure all integration tests pass
  - Verify test coverage meets goals (90% line coverage, 85% branch coverage)
  - Ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples and edge cases
- The implementation maintains full backward compatibility with existing Groq-only setups
- All agents will work with both providers without code changes
