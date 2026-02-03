# Requirements Document: OpenAI Integration

## Introduction

This document specifies the requirements for adding OpenAI API support to the SVA-Chatbot project as an alternative LLM provider alongside the existing Groq API integration. The system currently uses a GroqClient class for all LLM interactions across multiple agents (orchestrator, sva_generator, rtl_analyzer, etc.). This feature will enable users to configure and use OpenAI's API as an alternative provider while maintaining full backward compatibility with existing Groq-only configurations.

## Glossary

- **LLM_Provider**: A service that provides Large Language Model API access (Groq or OpenAI)
- **Client**: A class that handles API communication with an LLM_Provider
- **Client_Factory**: A component that creates and returns the appropriate Client based on configuration
- **Agent**: A component in the pipeline that uses an LLM_Provider for processing (e.g., orchestrator, sva_generator)
- **Configuration**: Environment variables and settings that control system behavior
- **API_Key**: Authentication credential for accessing an LLM_Provider's API
- **Model**: A specific LLM model offered by an LLM_Provider (e.g., gpt-4, llama-3.3-70b-versatile)
- **Chat_Completion**: An API request to generate text responses from an LLM
- **Token_Usage**: Metrics tracking the number of tokens consumed by API requests
- **Fallback_Model**: A secondary model used when the primary model fails or is unavailable

## Requirements

### Requirement 1: OpenAI Client Implementation

**User Story:** As a developer, I want an OpenAI client class that mirrors the GroqClient functionality, so that OpenAI can be used as a drop-in replacement for Groq.

#### Acceptance Criteria

1. THE OpenAI_Client SHALL implement the same interface as the GroqClient
2. WHEN a chat completion is requested, THE OpenAI_Client SHALL make API calls to OpenAI's chat completion endpoint
3. WHEN an API call succeeds, THE OpenAI_Client SHALL return response data in the same format as GroqClient
4. WHEN an API call fails, THE OpenAI_Client SHALL raise an appropriate error with descriptive messages
5. THE OpenAI_Client SHALL track token usage per project_id
6. THE OpenAI_Client SHALL support caching of responses with configurable TTL
7. THE OpenAI_Client SHALL log all requests and responses with structured logging
8. THE OpenAI_Client SHALL support async/await patterns using aiohttp

### Requirement 2: Model Fallback Support

**User Story:** As a user, I want automatic fallback to a secondary model when the primary model fails, so that my requests can still be processed.

#### Acceptance Criteria

1. WHEN the primary model fails, THE OpenAI_Client SHALL automatically retry with the fallback model
2. WHEN a rate limit error occurs, THE OpenAI_Client SHALL use the fallback model if aggressive fallback is enabled
3. THE OpenAI_Client SHALL log all fallback attempts with the reason for fallback
4. THE OpenAI_Client SHALL support configurable primary and fallback models

### Requirement 3: Provider Selection Configuration

**User Story:** As a system administrator, I want to configure which LLM provider to use via environment variables, so that I can switch between Groq and OpenAI without code changes.

#### Acceptance Criteria

1. THE Configuration SHALL include an LLM_PROVIDER setting that accepts "groq" or "openai" as values
2. WHEN LLM_PROVIDER is not specified, THE Configuration SHALL default to "groq" for backward compatibility
3. THE Configuration SHALL include OPENAI_API_KEY for OpenAI authentication
4. THE Configuration SHALL include OPENAI_PRIMARY_MODEL and OPENAI_FALLBACK_MODEL settings
5. WHEN OpenAI is selected but OPENAI_API_KEY is missing, THE System SHALL raise a configuration error at startup

### Requirement 4: Client Factory Pattern

**User Story:** As a developer, I want a factory that creates the appropriate client based on configuration, so that agents don't need to know which provider is being used.

#### Acceptance Criteria

1. THE Client_Factory SHALL create a GroqClient when LLM_PROVIDER is "groq"
2. THE Client_Factory SHALL create an OpenAI_Client when LLM_PROVIDER is "openai"
3. WHEN an invalid LLM_PROVIDER value is specified, THE Client_Factory SHALL raise a configuration error
4. THE Client_Factory SHALL return clients that implement a common interface
5. THE Client_Factory SHALL be usable as a dependency injection mechanism

### Requirement 5: Agent Integration

**User Story:** As a developer, I want all existing agents to work with both providers without modification, so that the system remains maintainable.

#### Acceptance Criteria

1. WHEN an Agent is initialized, THE Agent SHALL receive a client from the Client_Factory
2. THE Agent SHALL use the client interface without knowing the underlying provider
3. WHEN the provider is changed in configuration, THE Agent SHALL continue functioning without code changes
4. THE Orchestrator SHALL initialize agents with the configured provider's client

### Requirement 6: Environment Configuration

**User Story:** As a user, I want clear documentation of OpenAI configuration options in .env.example, so that I can easily set up OpenAI integration.

#### Acceptance Criteria

1. THE .env.example file SHALL include LLM_PROVIDER with example values
2. THE .env.example file SHALL include OPENAI_API_KEY with placeholder text
3. THE .env.example file SHALL include OPENAI_PRIMARY_MODEL with a recommended default
4. THE .env.example file SHALL include OPENAI_FALLBACK_MODEL with a recommended default
5. THE .env.example file SHALL include comments explaining each OpenAI configuration option

### Requirement 7: Dependency Management

**User Story:** As a developer, I want the openai package added to requirements.txt, so that the OpenAI client can be installed with other dependencies.

#### Acceptance Criteria

1. THE requirements.txt file SHALL include the openai package with a specific version
2. THE openai package version SHALL be compatible with Python 3.8+
3. THE openai package SHALL support async operations

### Requirement 8: Backward Compatibility

**User Story:** As an existing user, I want my current Groq-only setup to continue working without any changes, so that the update doesn't break my workflow.

#### Acceptance Criteria

1. WHEN LLM_PROVIDER is not specified in configuration, THE System SHALL use Groq as the default provider
2. WHEN only GROQ_API_KEY is provided, THE System SHALL function exactly as before the update
3. THE GroqClient SHALL remain unchanged in its public interface
4. THE System SHALL not require OpenAI configuration when using Groq

### Requirement 9: Error Handling and Logging

**User Story:** As a system administrator, I want clear error messages and logging for provider-related issues, so that I can troubleshoot configuration problems.

#### Acceptance Criteria

1. WHEN a provider-specific error occurs, THE System SHALL log the error with the provider name
2. WHEN API authentication fails, THE System SHALL provide a clear error message indicating which API key is invalid
3. WHEN a model is not available, THE System SHALL log which provider and model were requested
4. THE System SHALL log which provider is being used at startup

### Requirement 10: Token Usage Tracking

**User Story:** As a project manager, I want token usage tracked separately for each provider, so that I can monitor costs per provider.

#### Acceptance Criteria

1. THE OpenAI_Client SHALL track prompt_tokens, completion_tokens, and total_tokens per project
2. THE OpenAI_Client SHALL provide a method to retrieve token usage statistics for a project
3. THE Token usage tracking SHALL follow the same pattern as GroqClient
4. THE System SHALL log token usage after each API call with the provider name

### Requirement 11: Performance Metrics

**User Story:** As a developer, I want performance metrics tracked for both providers, so that I can compare response times and reliability.

#### Acceptance Criteria

1. THE OpenAI_Client SHALL track request duration for each API call
2. THE OpenAI_Client SHALL track success and failure rates
3. THE OpenAI_Client SHALL integrate with the existing metrics tracking system
4. THE System SHALL log performance metrics with the provider name for filtering
