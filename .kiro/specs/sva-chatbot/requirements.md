# Requirements Document

## Introduction

The SVA-Chatbot is an intelligent agentic AI system that automatically generates SystemVerilog Assertions (SVA) from natural language specifications and RTL designs. The system uses a multi-agent pipeline architecture powered by Groq API (llama-3.3-70b-versatile or mixtral-8x7b), with MongoDB for data persistence, and separate backend and frontend components.

## Glossary

- **SVA**: SystemVerilog Assertions - formal properties used to verify hardware designs
- **RTL**: Register Transfer Level - hardware description code in SystemVerilog
- **Specification**: Natural language document describing functional requirements, timing constraints, and protocol behaviors
- **Agent**: An autonomous AI component that performs a specific task in the processing pipeline
- **Orchestrator**: The backend component that manages agent lifecycle and inter-agent communication
- **Groq_API**: The LLM service provider used for AI-powered analysis and generation
- **Frontend**: React-based web application providing the user interface
- **Backend**: FastAPI-based server handling business logic and agent orchestration
- **MongoDB**: Document-oriented database storing projects, specifications, RTL designs, and generated assertions
- **Pattern_Library**: Collection of pre-built assertion templates and common RTL patterns
- **Traceability**: The linkage between requirements, RTL code, and generated assertions
- **Vacuity**: A condition where an assertion is trivially true and provides no verification value
- **Confidence_Score**: A numerical value (0.0 to 1.0) indicating the system's confidence in a generated assertion

## Requirements

### Requirement 1: Document Input Processing

**User Story:** As a verification engineer, I want to upload specification documents in multiple formats, so that I can use existing documentation without format conversion.

#### Acceptance Criteria

1. WHEN a user uploads a Markdown file (.md), THE System SHALL extract and parse the text content
2. WHEN a user uploads a plain text file (.txt), THE System SHALL extract and parse the text content
3. WHEN a user uploads a PDF file (.pdf), THE System SHALL extract and parse the text content
4. WHEN a user uploads a Word document (.doc or .docx), THE System SHALL extract and parse the text content
5. WHEN a file upload fails, THE System SHALL return a descriptive error message
6. WHEN a file exceeds size limits, THE System SHALL reject the upload and notify the user

### Requirement 2: RTL Design Input Processing

**User Story:** As a verification engineer, I want to upload SystemVerilog RTL files, so that the system can analyze my hardware design.

#### Acceptance Criteria

1. WHEN a user uploads a SystemVerilog file (.sv or .v), THE System SHALL parse the file into an abstract syntax tree
2. WHEN parsing succeeds, THE System SHALL extract module definitions, ports, signals, and state machines
3. WHEN parsing fails, THE System SHALL return syntax error details with line numbers
4. WHEN multiple RTL files are uploaded, THE System SHALL process all files and build dependency relationships

### Requirement 3: Specification Analysis

**User Story:** As a verification engineer, I want the system to automatically extract requirements from specifications, so that I don't have to manually structure them.

#### Acceptance Criteria

1. WHEN a specification is processed, THE Specification_Parser SHALL segment the text into individual requirement sentences
2. WHEN requirements are extracted, THE Specification_Parser SHALL identify temporal keywords (after, within, before, eventually)
3. WHEN requirements are extracted, THE Specification_Parser SHALL categorize them as timing, functional, protocol, safety, or liveness requirements
4. WHEN requirements are extracted, THE Specification_Parser SHALL extract entity names (signals, modules, values, states)
5. WHEN ambiguous requirements are detected, THE Specification_Parser SHALL flag them for user clarification

### Requirement 4: RTL Semantic Analysis

**User Story:** As a verification engineer, I want the system to understand my RTL structure, so that assertions can reference the correct signals and modules.

#### Acceptance Criteria

1. WHEN RTL is analyzed, THE RTL_Analyzer SHALL identify all clock signals in the design
2. WHEN RTL is analyzed, THE RTL_Analyzer SHALL identify all reset signals in the design
3. WHEN RTL is analyzed, THE RTL_Analyzer SHALL detect state machines and extract state definitions
4. WHEN RTL is analyzed, THE RTL_Analyzer SHALL build signal dependency graphs
5. WHEN RTL is analyzed, THE RTL_Analyzer SHALL recognize common protocol patterns (handshake, FIFO, AXI)

### Requirement 5: Specification-RTL Alignment

**User Story:** As a verification engineer, I want the system to map requirements to RTL elements, so that assertions target the correct implementation.

#### Acceptance Criteria

1. WHEN alignment is performed, THE Alignment_Agent SHALL map requirement entities to RTL signals with confidence scores
2. WHEN alignment is performed, THE Alignment_Agent SHALL identify which modules implement which specifications
3. WHEN requirements cannot be mapped to RTL, THE Alignment_Agent SHALL flag missing implementations
4. WHEN mappings are ambiguous, THE Alignment_Agent SHALL generate clarification questions for the user
5. FOR ALL aligned requirement-RTL pairs, THE System SHALL store the mapping with confidence scores

### Requirement 6: SVA Code Generation

**User Story:** As a verification engineer, I want the system to generate syntactically correct SVA code, so that I can use it directly in my verification environment.

#### Acceptance Criteria

1. WHEN generating assertions, THE SVA_Generator SHALL produce immediate assertions for combinational checks
2. WHEN generating assertions, THE SVA_Generator SHALL produce concurrent assertions for temporal properties
3. WHEN generating assertions, THE SVA_Generator SHALL include property and sequence definitions where appropriate
4. WHEN generating assertions, THE SVA_Generator SHALL properly reference clock and reset signals
5. WHEN generating assertions, THE SVA_Generator SHALL add meaningful comments explaining each assertion
6. FOR ALL generated assertions, THE System SHALL ensure syntactic correctness according to SystemVerilog standards

### Requirement 7: Assertion Quality Validation

**User Story:** As a verification engineer, I want the system to validate generated assertions, so that I can trust their correctness.

#### Acceptance Criteria

1. WHEN assertions are generated, THE Verification_Agent SHALL perform syntax validation
2. WHEN assertions are generated, THE Verification_Agent SHALL apply vacuity detection heuristics
3. WHEN assertions are generated, THE Verification_Agent SHALL detect potential over-constraints
4. WHEN assertions are generated, THE Verification_Agent SHALL calculate quality scores (0.0 to 1.0)
5. FOR ALL assertions, THE System SHALL provide confidence scores indicating generation certainty

### Requirement 8: Traceability Management

**User Story:** As a verification engineer, I want to trace each assertion back to its source requirement, so that I can verify coverage and understand intent.

#### Acceptance Criteria

1. FOR ALL generated assertions, THE System SHALL link to the originating requirement text
2. FOR ALL generated assertions, THE System SHALL reference the specific RTL signals used
3. FOR ALL generated assertions, THE System SHALL record the RTL line numbers involved
4. WHEN a user views an assertion, THE System SHALL display its traceability information
5. WHEN a user requests a traceability report, THE System SHALL generate a requirement-to-assertion matrix

### Requirement 9: Real-Time User Feedback

**User Story:** As a verification engineer, I want to see processing progress in real-time, so that I understand what the system is doing.

#### Acceptance Criteria

1. WHEN agent processing begins, THE System SHALL send real-time status updates via WebSocket
2. WHEN each agent completes, THE System SHALL notify the frontend with results
3. WHEN agents generate clarification questions, THE System SHALL display them immediately to the user
4. WHEN assertions are generated, THE System SHALL stream them to the frontend as they are created
5. WHEN errors occur, THE System SHALL notify the user immediately with error details

### Requirement 10: Interactive Assertion Refinement

**User Story:** As a verification engineer, I want to edit and refine generated assertions, so that I can correct any issues or adapt them to my needs.

#### Acceptance Criteria

1. WHEN a user edits an assertion, THE System SHALL validate the syntax in real-time
2. WHEN a user saves an edited assertion, THE System SHALL update the database and mark it as modified
3. WHEN a user provides feedback on an assertion, THE System SHALL store the rating and comments
4. WHEN a user requests assertion regeneration, THE System SHALL use previous feedback to improve results
5. WHEN a user asks clarification questions, THE System SHALL engage in conversational refinement

### Requirement 11: Pattern Library Integration

**User Story:** As a verification engineer, I want the system to use proven assertion patterns, so that generated assertions follow best practices.

#### Acceptance Criteria

1. WHEN generating assertions, THE SVA_Generator SHALL query the Pattern_Library for similar patterns
2. WHEN patterns are found, THE SVA_Generator SHALL adapt templates with appropriate signal substitutions
3. WHEN no patterns match, THE SVA_Generator SHALL generate assertions from first principles
4. WHEN users provide positive feedback, THE System SHALL increase pattern usage counts
5. FOR ALL pattern searches, THE System SHALL use semantic similarity (embeddings) for retrieval

### Requirement 12: Project Management

**User Story:** As a verification engineer, I want to organize my work into projects, so that I can manage multiple verification efforts.

#### Acceptance Criteria

1. WHEN a user creates a project, THE System SHALL store project metadata (name, description, timestamps)
2. WHEN a user lists projects, THE System SHALL display all projects with summary statistics
3. WHEN a user deletes a project, THE System SHALL remove all associated specifications, RTL files, and assertions
4. WHEN a user opens a project, THE System SHALL load all project data and display the current state
5. FOR ALL projects, THE System SHALL track total specifications, RTL files, and generated assertions

### Requirement 13: File Upload Interface

**User Story:** As a verification engineer, I want an intuitive file upload interface, so that I can quickly provide inputs to the system.

#### Acceptance Criteria

1. WHEN a user drags files to the upload area, THE Frontend SHALL accept and display them
2. WHEN files are uploading, THE Frontend SHALL show progress indicators
3. WHEN uploads complete, THE Frontend SHALL display file previews and validation status
4. WHEN invalid files are uploaded, THE Frontend SHALL show error messages and reject them
5. WHEN multiple files are uploaded, THE Frontend SHALL handle them concurrently

### Requirement 14: Assertion Visualization

**User Story:** As a verification engineer, I want to view assertions with syntax highlighting and context, so that I can easily understand and review them.

#### Acceptance Criteria

1. WHEN assertions are displayed, THE Frontend SHALL apply SystemVerilog syntax highlighting
2. WHEN a user views an assertion, THE Frontend SHALL show the related specification text side-by-side
3. WHEN a user views an assertion, THE Frontend SHALL show the related RTL code side-by-side
4. WHEN a user clicks on an assertion, THE Frontend SHALL highlight traceability links
5. WHEN assertions are displayed, THE Frontend SHALL show confidence scores and quality indicators

### Requirement 15: Export and Integration

**User Story:** As a verification engineer, I want to export generated assertions, so that I can integrate them into my verification environment.

#### Acceptance Criteria

1. WHEN a user requests export, THE System SHALL generate a downloadable SVA file with all assertions
2. WHEN a user requests export, THE System SHALL include comments and traceability information in the file
3. WHEN a user requests a traceability report, THE System SHALL generate a downloadable document
4. WHEN a user clicks copy, THE System SHALL copy assertion code to the clipboard
5. WHEN exporting, THE System SHALL provide integration instructions for common verification tools

### Requirement 16: Multi-Agent Orchestration

**User Story:** As a system administrator, I want agents to execute in a coordinated pipeline, so that processing is efficient and reliable.

#### Acceptance Criteria

1. WHEN generation starts, THE Orchestrator SHALL initialize all five agents in sequence
2. WHEN an agent completes, THE Orchestrator SHALL pass results to the next agent
3. WHEN an agent fails, THE Orchestrator SHALL implement retry logic with exponential backoff
4. WHEN agents need to communicate, THE Orchestrator SHALL facilitate message passing
5. FOR ALL agent executions, THE Orchestrator SHALL track performance metrics and execution times

### Requirement 17: Groq API Integration

**User Story:** As a system administrator, I want reliable LLM integration, so that the system can leverage AI capabilities effectively.

#### Acceptance Criteria

1. WHEN calling Groq API, THE System SHALL use llama-3.3-70b-versatile as the primary model
2. WHEN the primary model fails, THE System SHALL fall back to mixtral-8x7b-32768
3. WHEN making API calls, THE System SHALL track token usage per project
4. WHEN rate limits are approached, THE System SHALL implement request queuing
5. WHEN API keys are stored, THE System SHALL use secure environment variables and never expose them to the frontend

### Requirement 18: Data Persistence

**User Story:** As a verification engineer, I want my work to be automatically saved, so that I don't lose progress.

#### Acceptance Criteria

1. WHEN specifications are uploaded, THE System SHALL store them in MongoDB with metadata
2. WHEN RTL files are uploaded, THE System SHALL store source code and parsed AST in MongoDB
3. WHEN assertions are generated, THE System SHALL store them with traceability and quality metrics
4. WHEN users provide feedback, THE System SHALL update assertion records immediately
5. FOR ALL database operations, THE System SHALL use appropriate indexes for query performance

### Requirement 19: Error Handling and Recovery

**User Story:** As a verification engineer, I want the system to handle errors gracefully, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN file parsing fails, THE System SHALL provide specific error messages with line numbers
2. WHEN agent processing fails, THE System SHALL log errors and notify the user
3. WHEN API calls fail, THE System SHALL retry with exponential backoff up to 3 attempts
4. WHEN database operations fail, THE System SHALL rollback transactions and preserve data integrity
5. FOR ALL errors, THE System SHALL log detailed information for debugging

### Requirement 20: Security and Authentication

**User Story:** As a system administrator, I want secure access control, so that user data is protected.

#### Acceptance Criteria

1. WHEN users access the system, THE System SHALL require authentication via JWT tokens
2. WHEN users access projects, THE System SHALL verify project ownership
3. WHEN files are uploaded, THE System SHALL validate file types and sizes to prevent malicious uploads
4. WHEN API keys are managed, THE System SHALL store them encrypted and implement rotation strategies
5. FOR ALL communications, THE System SHALL use HTTPS encryption
