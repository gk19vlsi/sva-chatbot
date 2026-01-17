# Design Document: SVA-Chatbot

## Overview

The SVA-Chatbot is a full-stack web application that uses a multi-agent AI pipeline to automatically generate SystemVerilog Assertions from natural language specifications and RTL designs. The system consists of three main layers:

1. **Frontend Layer**: React-based web application providing file upload, real-time monitoring, and assertion visualization
2. **Backend Layer**: FastAPI-based server orchestrating a five-agent pipeline powered by Groq API
3. **Data Layer**: MongoDB database storing projects, documents, and generated artifacts

The system follows an event-driven architecture with WebSocket communication for real-time updates and RESTful APIs for CRUD operations.

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ File Upload  │  │ Chat UI      │  │ Assertion    │      │
│  │ Interface    │  │ & Monitoring │  │ Viewer       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Gateway & Orchestrator              │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │           Multi-Agent Pipeline System                │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ Agent 1: Specification Parser                  │ │   │
│  │  │ Agent 2: RTL Analyzer                          │ │   │
│  │  │ Agent 3: Spec-RTL Alignment                    │ │   │
│  │  │ Agent 4: SVA Generator                         │ │   │
│  │  │ Agent 5: Verification & Refinement             │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │         Groq API Integration Layer                   │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    MongoDB Database                          │
│  Collections: projects, specifications, rtl_designs,        │
│  assertions, agent_conversations, pattern_library           │
└─────────────────────────────────────────────────────────────┘
```

### Agent Pipeline Flow

```
User Upload → API Gateway → Orchestrator
                              ↓
                    ┌─────────┴─────────┐
                    │ Agent 1: Spec     │
                    │ Parser            │
                    │ - Extract text    │
                    │ - Segment reqs    │
                    │ - Categorize      │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │ Agent 2: RTL      │
                    │ Analyzer          │
                    │ - Parse AST       │
                    │ - Extract modules │
                    │ - Find clocks     │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │ Agent 3: Alignment│
                    │ - Map entities    │
                    │ - Score confidence│
                    │ - Flag gaps       │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │ Agent 4: SVA Gen  │
                    │ - Query patterns  │
                    │ - Generate code   │
                    │ - Add comments    │
                    └─────────┬─────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │ Agent 5: Validator│
                    │ - Check syntax    │
                    │ - Detect vacuity  │
                    │ - Score quality   │
                    └─────────┬─────────┘
                              ↓
                    Results → Frontend
```

## Components and Interfaces

### Frontend Components

#### 1. File Upload Component

**Responsibility**: Handle specification and RTL file uploads

**Interface**:

```typescript
interface FileUploadProps {
  projectId: string;
  fileType: "specification" | "rtl";
  onUploadComplete: (fileId: string) => void;
  onUploadError: (error: Error) => void;
}

interface UploadedFile {
  id: string;
  filename: string;
  size: number;
  type: string;
  status: "uploading" | "processing" | "complete" | "error";
  progress: number;
}
```

**Key Features**:

- Drag-and-drop support using react-dropzone
- File validation (type, size)
- Progress tracking
- Preview capability

#### 2. Chat Interface Component

**Responsibility**: Display agent activity and handle user interactions

**Interface**:

```typescript
interface ChatMessage {
  id: string;
  timestamp: Date;
  agentName: string;
  role: "user" | "agent" | "system";
  content: string;
  metadata?: {
    requirementCount?: number;
    assertionCount?: number;
    clarificationNeeded?: boolean;
  };
}

interface ChatInterfaceProps {
  projectId: string;
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
}
```

#### 3. Assertion Viewer Component

**Responsibility**: Display and edit generated assertions

**Interface**:

```typescript
interface Assertion {
  id: string;
  code: string;
  type: "immediate" | "concurrent" | "property" | "sequence";
  confidenceScore: number;
  qualityScore: number;
  traceability: {
    requirementId: string;
    requirementText: string;
    rtlSignals: string[];
    rtlModule: string;
  };
  explanation: string;
}

interface AssertionViewerProps {
  assertions: Assertion[];
  onEdit: (id: string, newCode: string) => void;
  onFeedback: (id: string, rating: number, comment: string) => void;
}
```

#### 4. Visualization Dashboard Component

**Responsibility**: Display traceability and coverage metrics

**Interface**:

```typescript
interface TraceabilityMatrix {
  requirements: Requirement[];
  assertions: Assertion[];
  mappings: Array<{
    requirementId: string;
    assertionIds: string[];
    coverage: number;
  }>;
}

interface DashboardProps {
  projectId: string;
  traceability: TraceabilityMatrix;
  metrics: {
    totalRequirements: number;
    totalAssertions: number;
    coveragePercentage: number;
    avgConfidenceScore: number;
  };
}
```

### Backend Components

#### 1. API Gateway

**Responsibility**: Handle HTTP requests, authentication, and routing

**Endpoints**:

```python
# Project Management
POST   /api/projects
GET    /api/projects
GET    /api/projects/{id}
DELETE /api/projects/{id}

# File Upload
POST   /api/projects/{id}/upload-spec
POST   /api/projects/{id}/upload-rtl

# Generation
POST   /api/projects/{id}/generate
GET    /api/projects/{id}/status
GET    /api/projects/{id}/results

# Chat & Interaction
POST   /api/chat
GET    /api/chat/{sessionId}/history

# Assertions
GET    /api/assertions/{id}
PUT    /api/assertions/{id}
POST   /api/assertions/{id}/feedback

# Patterns
GET    /api/patterns
POST   /api/patterns/search

# WebSocket
WS     /ws/generation
```

**Authentication**:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPBearer = Depends(security)):
    # JWT token verification
    token = credentials.credentials
    # Validate and decode token
    return user_id
```

#### 2. Orchestrator

**Responsibility**: Manage agent lifecycle and pipeline execution

**Interface**:

```python
class Orchestrator:
    def __init__(self, db: Database, groq_client: GroqClient):
        self.db = db
        self.groq_client = groq_client
        self.agents = self._initialize_agents()

    async def execute_pipeline(
        self,
        project_id: str,
        websocket: WebSocket
    ) -> PipelineResult:
        """Execute the five-agent pipeline"""
        context = PipelineContext(project_id=project_id)

        # Agent 1: Parse specifications
        spec_result = await self.agents['spec_parser'].execute(context)
        await self._send_update(websocket, 'spec_parsed', spec_result)

        # Agent 2: Analyze RTL
        rtl_result = await self.agents['rtl_analyzer'].execute(context)
        await self._send_update(websocket, 'rtl_analyzed', rtl_result)

        # Agent 3: Align spec and RTL
        alignment_result = await self.agents['alignment'].execute(context)
        await self._send_update(websocket, 'aligned', alignment_result)

        # Agent 4: Generate SVA
        sva_result = await self.agents['sva_generator'].execute(context)
        await self._send_update(websocket, 'sva_generated', sva_result)

        # Agent 5: Validate and refine
        final_result = await self.agents['validator'].execute(context)
        await self._send_update(websocket, 'completed', final_result)

        return final_result
```

#### 3. Agent Base Class

**Responsibility**: Define common agent interface

**Interface**:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    def __init__(self, name: str, groq_client: GroqClient, db: Database):
        self.name = name
        self.groq_client = groq_client
        self.db = db

    @abstractmethod
    async def execute(self, context: PipelineContext) -> AgentResult:
        """Execute agent-specific logic"""
        pass

    async def call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """Make LLM API call with error handling"""
        try:
            response = await self.groq_client.chat_completion(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback to mixtral
            response = await self.groq_client.chat_completion(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
```

#### 4. Specification Parser Agent

**Responsibility**: Extract and structure requirements from documents

**Implementation**:

```python
class SpecificationParserAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Load specification documents
        specs = await self.db.get_specifications(context.project_id)

        all_requirements = []
        for spec in specs:
            # Extract text based on file type
            text = await self._extract_text(spec)

            # Use LLM to parse requirements
            system_prompt = """You are a requirements extraction expert.
            Extract individual requirements from the specification text.
            For each requirement, identify:
            - The requirement text
            - Category (timing/functional/protocol/safety/liveness)
            - Temporal keywords (after, within, before, eventually, etc.)
            - Entity names (signals, modules, states, values)

            Return as JSON array."""

            user_prompt = f"Extract requirements from:\n\n{text}"

            response = await self.call_groq(system_prompt, user_prompt)
            requirements = json.loads(response)

            # Store parsed requirements
            for req in requirements:
                req_id = await self.db.store_requirement(
                    project_id=context.project_id,
                    spec_id=spec['_id'],
                    requirement=req
                )
                all_requirements.append({**req, 'id': req_id})

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={'requirements': all_requirements}
        )

    async def _extract_text(self, spec: Dict) -> str:
        """Extract text from various file formats"""
        if spec['file_type'] == 'pdf':
            return await self._extract_pdf(spec['file_path'])
        elif spec['file_type'] == 'docx':
            return await self._extract_docx(spec['file_path'])
        else:
            return spec['raw_text']
```

#### 5. RTL Analyzer Agent

**Responsibility**: Parse and analyze SystemVerilog RTL

**Implementation**:

```python
class RTLAnalyzerAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Load RTL files
        rtl_files = await self.db.get_rtl_designs(context.project_id)

        all_modules = []
        for rtl in rtl_files:
            # Parse SystemVerilog using tree-sitter
            ast = await self._parse_systemverilog(rtl['source_code'])

            # Extract structural information
            modules = self._extract_modules(ast)

            # Use LLM for semantic analysis
            system_prompt = """You are a hardware design analysis expert.
            Analyze the SystemVerilog code and identify:
            - Clock signals
            - Reset signals
            - State machines (states and transitions)
            - Signal dependencies
            - Protocol patterns (handshake, FIFO, AXI, etc.)

            Return as JSON."""

            user_prompt = f"Analyze this SystemVerilog code:\n\n{rtl['source_code']}"

            response = await self.call_groq(system_prompt, user_prompt)
            analysis = json.loads(response)

            # Store analysis
            await self.db.update_rtl_analysis(
                rtl_id=rtl['_id'],
                analysis=analysis
            )

            all_modules.extend(analysis['modules'])

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={'modules': all_modules}
        )
```

#### 6. Alignment Agent

**Responsibility**: Map requirements to RTL elements

**Implementation**:

```python
class AlignmentAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Load requirements and RTL analysis
        requirements = await self.db.get_requirements(context.project_id)
        rtl_analysis = await self.db.get_rtl_analysis(context.project_id)

        alignments = []
        for req in requirements:
            system_prompt = """You are a specification-to-implementation mapping expert.
            Given a requirement and RTL analysis, identify:
            - Which RTL signals correspond to requirement entities
            - Which modules implement the requirement
            - Confidence score (0.0 to 1.0)
            - Any ambiguities or missing implementations

            Return as JSON."""

            user_prompt = f"""Requirement: {req['text']}
            Entities: {req['entities']}

            RTL Modules: {json.dumps(rtl_analysis['modules'])}

            Map requirement to RTL."""

            response = await self.call_groq(system_prompt, user_prompt)
            alignment = json.loads(response)

            # Store alignment
            alignment_id = await self.db.store_alignment(
                project_id=context.project_id,
                requirement_id=req['id'],
                alignment=alignment
            )

            alignments.append({**alignment, 'id': alignment_id})

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={'alignments': alignments}
        )
```

#### 7. SVA Generator Agent

**Responsibility**: Generate SystemVerilog assertions

**Implementation**:

```python
class SVAGeneratorAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Load alignments
        alignments = await self.db.get_alignments(context.project_id)

        assertions = []
        for alignment in alignments:
            # Query pattern library for similar patterns
            patterns = await self._search_patterns(alignment)

            system_prompt = """You are a SystemVerilog assertion generation expert.
            Generate syntactically correct SVA code that verifies the requirement.

            Use:
            - Immediate assertions for combinational checks
            - Concurrent assertions for temporal properties
            - Proper clock and reset references
            - Meaningful comments

            Return only the SVA code."""

            user_prompt = f"""Requirement: {alignment['requirement_text']}
            RTL Signals: {alignment['rtl_signals']}
            Clock: {alignment['clock']}
            Reset: {alignment['reset']}

            Similar patterns:
            {self._format_patterns(patterns)}

            Generate SVA assertion."""

            response = await self.call_groq(system_prompt, user_prompt, temperature=0.2)

            # Store assertion
            assertion_id = await self.db.store_assertion(
                project_id=context.project_id,
                requirement_id=alignment['requirement_id'],
                code=response,
                rtl_module=alignment['rtl_module'],
                confidence_score=alignment['confidence_score']
            )

            assertions.append({
                'id': assertion_id,
                'code': response,
                'requirement_id': alignment['requirement_id']
            })

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={'assertions': assertions}
        )

    async def _search_patterns(self, alignment: Dict) -> List[Dict]:
        """Search pattern library using semantic similarity"""
        # Generate embedding for alignment
        embedding = await self._generate_embedding(alignment['requirement_text'])

        # Vector search in MongoDB
        patterns = await self.db.pattern_library.aggregate([
            {
                "$vectorSearch": {
                    "index": "pattern_embeddings",
                    "path": "embedding_vector",
                    "queryVector": embedding,
                    "numCandidates": 100,
                    "limit": 5
                }
            }
        ]).to_list(length=5)

        return patterns
```

#### 8. Validation Agent

**Responsibility**: Validate and score generated assertions

**Implementation**:

```python
class ValidationAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Load generated assertions
        assertions = await self.db.get_assertions(context.project_id)

        validated_assertions = []
        for assertion in assertions:
            # Syntax validation
            syntax_valid = await self._validate_syntax(assertion['code'])

            # Use LLM for quality analysis
            system_prompt = """You are a SystemVerilog assertion quality expert.
            Analyze the assertion for:
            - Vacuity (is it trivially true?)
            - Over-constraints (is it too restrictive?)
            - Quality score (0.0 to 1.0)
            - Suggestions for improvement

            Return as JSON."""

            user_prompt = f"""Assertion code:
            {assertion['code']}

            Requirement: {assertion['requirement_text']}
            RTL context: {assertion['rtl_module']}

            Analyze quality."""

            response = await self.call_groq(system_prompt, user_prompt)
            quality_analysis = json.loads(response)

            # Update assertion with validation results
            await self.db.update_assertion_validation(
                assertion_id=assertion['id'],
                validation={
                    'syntax_valid': syntax_valid,
                    'vacuity_check': quality_analysis['vacuity'],
                    'quality_score': quality_analysis['quality_score']
                }
            )

            validated_assertions.append({
                **assertion,
                'validation': quality_analysis
            })

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={'assertions': validated_assertions}
        )

    async def _validate_syntax(self, sva_code: str) -> bool:
        """Basic syntax validation using regex patterns"""
        # Check for basic SVA syntax patterns
        patterns = [
            r'assert\s+property',
            r'@\(posedge\s+\w+\)',
            r'##\d+',
            r'\|->',
            r'\|=>'
        ]
        # Simple heuristic validation
        return any(re.search(pattern, sva_code) for pattern in patterns)
```

#### 9. Groq API Client

**Responsibility**: Handle LLM API communication

**Interface**:

```python
class GroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.session = aiohttp.ClientSession()

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9
    ) -> Dict:
        """Make chat completion request"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }

        async with self.session.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise GroqAPIError(f"API call failed: {await response.text()}")
            return await response.json()

    async def close(self):
        await self.session.close()
```

## Data Models

### MongoDB Collections

#### 1. Projects Collection

```python
{
    "_id": ObjectId,
    "name": str,
    "description": str,
    "created_at": datetime,
    "updated_at": datetime,
    "user_id": str,
    "status": "draft" | "processing" | "completed" | "failed",
    "metadata": {
        "total_specs": int,
        "total_rtl_files": int,
        "total_assertions": int
    }
}
```

#### 2. Specifications Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "filename": str,
    "file_type": "pdf" | "docx" | "md" | "txt",
    "file_path": str,  # GridFS reference
    "raw_text": str,
    "parsed_requirements": [
        {
            "requirement_id": str,
            "text": str,
            "category": "timing" | "functional" | "protocol" | "safety" | "liveness",
            "temporal_keywords": [str],
            "entities": [str],
            "priority": int
        }
    ],
    "uploaded_at": datetime,
    "processed": bool
}
```

#### 3. RTL Designs Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "filename": str,
    "file_path": str,
    "source_code": str,
    "parsed_ast": dict,  # Abstract Syntax Tree
    "analysis": {
        "modules": [
            {
                "name": str,
                "ports": [dict],
                "signals": [dict],
                "state_machines": [dict],
                "clocks": [str],
                "resets": [str]
            }
        ],
        "dependencies": dict,
        "complexity_score": float
    },
    "uploaded_at": datetime,
    "processed": bool
}
```

#### 4. Assertions Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "requirement_id": str,
    "rtl_module": str,
    "assertion_code": str,
    "assertion_type": "immediate" | "concurrent" | "property" | "sequence",
    "category": str,
    "confidence_score": float,  # 0.0 to 1.0
    "explanation": str,
    "traceability": {
        "spec_reference": str,
        "rtl_signals": [str],
        "line_numbers": [int]
    },
    "validation": {
        "syntax_valid": bool,
        "vacuity_check": str,
        "quality_score": float
    },
    "user_feedback": {
        "rating": int,
        "modified": bool,
        "comments": str
    },
    "generated_at": datetime,
    "agent_version": str
}
```

#### 5. Pattern Library Collection

```python
{
    "_id": ObjectId,
    "name": str,
    "description": str,
    "category": str,
    "protocol_type": str,  # e.g., 'AXI', 'APB', 'handshake'
    "template": str,  # SVA template with placeholders
    "parameters": [str],
    "example_usage": str,
    "tags": [str],
    "embedding_vector": [float],  # For semantic search
    "usage_count": int,
    "rating": float
}
```

### Database Indexes

```python
# Performance optimization
projects_indexes = [
    ("user_id", 1, "created_at", -1),
]

specifications_indexes = [
    ("project_id", 1),
]

rtl_designs_indexes = [
    ("project_id", 1),
]

assertions_indexes = [
    ("project_id", 1, "confidence_score", -1),
    ("requirement_id", 1),
]

pattern_library_indexes = [
    ("category", 1),
    ("tags", 1),
]

# Vector search index for pattern library
pattern_library_vector_index = {
    "name": "pattern_embeddings",
    "type": "vectorSearch",
    "fields": [{
        "type": "vector",
        "path": "embedding_vector",
        "numDimensions": 1536,  # OpenAI embedding size
        "similarity": "cosine"
    }]
}
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Document Text Extraction Consistency

_For any_ supported document format (PDF, DOCX, MD, TXT) containing text content, extracting text from the document should produce output that preserves the original text content.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: SystemVerilog Parsing Completeness

_For any_ valid SystemVerilog file, parsing the file should produce an AST that contains all module definitions, ports, signals, and state machines present in the source code.

**Validates: Requirements 2.1, 2.2**

### Property 3: Error Message Descriptiveness

_For any_ file processing failure (upload, parsing, or validation), the system should return an error message that includes the failure type and specific details (e.g., line numbers for syntax errors).

**Validates: Requirements 1.5, 2.3, 19.1**

### Property 4: Requirement Segmentation Completeness

_For any_ specification document, the parsed requirements should cover all requirement sentences in the original document without omission or duplication.

**Validates: Requirements 3.1**

### Property 5: Temporal Keyword Detection

_For any_ requirement containing temporal keywords (after, within, before, eventually, always, until), the parser should identify and extract all such keywords.

**Validates: Requirements 3.2**

### Property 6: Requirement Categorization Accuracy

_For any_ requirement with clear category indicators, the parser should assign it to exactly one category (timing, functional, protocol, safety, or liveness).

**Validates: Requirements 3.3**

### Property 7: Entity Extraction Completeness

_For any_ requirement mentioning signals, modules, states, or values, the parser should extract all such entity names.

**Validates: Requirements 3.4**

### Property 8: Clock and Reset Signal Detection

_For any_ RTL design containing clock or reset signals (identified by naming conventions or usage patterns), the analyzer should detect and classify all such signals.

**Validates: Requirements 4.1, 4.2**

### Property 9: State Machine Extraction

_For any_ RTL design containing a state machine (case statement with state variable), the analyzer should detect the FSM and extract all state definitions.

**Validates: Requirements 4.3**

### Property 10: Signal Dependency Graph Completeness

_For any_ RTL design, the dependency graph should include all signals and their direct dependencies (assignments and references).

**Validates: Requirements 4.4**

### Property 11: Protocol Pattern Recognition

_For any_ RTL design implementing a known protocol pattern (handshake, FIFO, AXI), the analyzer should recognize and classify the pattern.

**Validates: Requirements 4.5**

### Property 12: Requirement-RTL Alignment Confidence

_For any_ requirement-RTL alignment, the system should assign a confidence score between 0.0 and 1.0, where higher scores indicate stronger evidence of correct mapping.

**Validates: Requirements 5.1, 5.2**

### Property 13: Missing Implementation Detection

_For any_ requirement that cannot be mapped to RTL elements with confidence above a threshold, the system should flag it as a missing implementation.

**Validates: Requirements 5.3**

### Property 14: Alignment Persistence

_For any_ aligned requirement-RTL pair, storing the alignment and then retrieving it should produce an equivalent alignment with the same confidence score.

**Validates: Requirements 5.5**

### Property 15: Assertion Type Appropriateness

_For any_ combinational requirement (no temporal keywords), the generated assertion should be an immediate assertion; for any temporal requirement, it should be a concurrent assertion.

**Validates: Requirements 6.1, 6.2**

### Property 16: Clock and Reset Reference Correctness

_For any_ generated concurrent assertion, it should reference a clock signal from the target RTL module, and if the module has a reset, the assertion should handle reset appropriately.

**Validates: Requirements 6.4**

### Property 17: Assertion Comment Presence

_For any_ generated assertion, the code should include at least one comment explaining the assertion's purpose or linking to the requirement.

**Validates: Requirements 6.5**

### Property 18: SVA Syntax Validity

_For any_ generated assertion code, parsing it with a SystemVerilog parser should succeed without syntax errors.

**Validates: Requirements 6.6, 7.1**

### Property 19: Quality Score Range

_For any_ validated assertion, the quality score should be a number between 0.0 and 1.0 inclusive.

**Validates: Requirements 7.4, 7.5**

### Property 20: Traceability Completeness

_For any_ generated assertion, its traceability record should include the originating requirement text, all RTL signals referenced in the assertion, and the RTL module name.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 21: Traceability Matrix Completeness

_For any_ project with N requirements and M assertions, the traceability matrix should contain entries for all N requirements, showing which assertions (if any) validate each requirement.

**Validates: Requirements 8.5**

### Property 22: WebSocket Status Update Delivery

_For any_ agent execution in the pipeline, the system should send at least one WebSocket message indicating the agent's status (started, in-progress, or completed).

**Validates: Requirements 9.1, 9.2, 9.4**

### Property 23: Error Notification Immediacy

_For any_ error occurring during processing, the system should send a WebSocket notification within 1 second of error detection.

**Validates: Requirements 9.5, 19.2**

### Property 24: Assertion Edit Validation

_For any_ user edit to an assertion, validating the syntax should return a result indicating whether the edited code is syntactically valid SystemVerilog.

**Validates: Requirements 10.1**

### Property 25: Assertion Modification Tracking

_For any_ assertion that is edited and saved, retrieving the assertion from the database should show the modified flag set to true.

**Validates: Requirements 10.2**

### Property 26: Feedback Persistence

_For any_ user feedback (rating and comments) submitted for an assertion, retrieving the assertion should include the stored feedback.

**Validates: Requirements 10.3**

### Property 27: Pattern Library Query Execution

_For any_ assertion generation request, the system should query the pattern library for similar patterns before generating code.

**Validates: Requirements 11.1**

### Property 28: Pattern Template Adaptation

_For any_ pattern template with placeholders, adapting it with signal substitutions should replace all placeholders with actual signal names from the RTL.

**Validates: Requirements 11.2**

### Property 29: Pattern Usage Tracking

_For any_ pattern that receives positive user feedback, the pattern's usage count should increase by 1.

**Validates: Requirements 11.4**

### Property 30: Project Metadata Persistence

_For any_ created project, storing it and then retrieving it should produce a project record with the same name, description, and user_id.

**Validates: Requirements 12.1**

### Property 31: Project Listing Completeness

_For any_ user with N projects, listing projects should return exactly N project records with summary statistics.

**Validates: Requirements 12.2**

### Property 32: Cascading Project Deletion

_For any_ project with associated specifications, RTL files, and assertions, deleting the project should remove all associated records from the database.

**Validates: Requirements 12.3**

### Property 33: Project Statistics Accuracy

_For any_ project, the tracked statistics (total specs, total RTL files, total assertions) should match the actual count of documents in the respective collections.

**Validates: Requirements 12.5**

### Property 34: File Upload Progress Tracking

_For any_ file being uploaded, the frontend should receive progress updates with increasing percentage values from 0 to 100.

**Validates: Requirements 13.2**

### Property 35: Invalid File Rejection

_For any_ file that fails validation (wrong type or exceeds size limit), the upload should be rejected and an error message displayed.

**Validates: Requirements 13.4, 20.3**

### Property 36: Assertion Display Completeness

_For any_ assertion displayed in the viewer, the UI should show the assertion code, confidence score, quality score, and traceability information.

**Validates: Requirements 14.1, 14.5**

### Property 37: Export File Completeness

_For any_ project export, the generated SVA file should contain all assertions from the project with comments and traceability information.

**Validates: Requirements 15.1, 15.2**

### Property 38: Agent Pipeline Sequencing

_For any_ generation request, the orchestrator should execute agents in the correct sequence: Spec Parser → RTL Analyzer → Alignment → SVA Generator → Validator.

**Validates: Requirements 16.1, 16.2**

### Property 39: Agent Retry with Exponential Backoff

_For any_ agent execution that fails, the orchestrator should retry up to 3 times with exponentially increasing delays between attempts.

**Validates: Requirements 16.3, 19.3**

### Property 40: Agent Performance Metrics Tracking

_For any_ agent execution, the orchestrator should record the execution time and store it in the metrics collection.

**Validates: Requirements 16.5**

### Property 41: LLM Model Fallback

_For any_ Groq API call that fails with the primary model (llama-3.3-70b-versatile), the system should retry with the fallback model (mixtral-8x7b-32768).

**Validates: Requirements 17.1, 17.2**

### Property 42: Token Usage Tracking

_For any_ Groq API call, the system should record the token count and associate it with the project.

**Validates: Requirements 17.3**

### Property 43: API Key Security

_For any_ API response sent to the frontend, the response should not contain the Groq API key or any other sensitive credentials.

**Validates: Requirements 17.5**

### Property 44: Database Storage Consistency

_For any_ document (specification, RTL, or assertion) stored in MongoDB, retrieving it by ID should return a document with all the same field values.

**Validates: Requirements 18.1, 18.2, 18.3**

### Property 45: Immediate Feedback Updates

_For any_ user feedback submission, the assertion record should be updated in the database before the API returns a success response.

**Validates: Requirements 18.4**

### Property 46: Transaction Rollback on Failure

_For any_ database operation that fails during a multi-step transaction, all changes in that transaction should be rolled back, leaving the database in its previous consistent state.

**Validates: Requirements 19.4**

### Property 47: Error Logging Completeness

_For any_ error that occurs in the system, an error log entry should be created containing the error type, message, stack trace, and timestamp.

**Validates: Requirements 19.5**

### Property 48: Authentication Requirement

_For any_ API endpoint (except public health checks), requests without a valid JWT token should be rejected with a 401 Unauthorized response.

**Validates: Requirements 20.1**

### Property 49: Project Ownership Authorization

_For any_ project access request, the system should verify that the requesting user's ID matches the project's user_id before allowing access.

**Validates: Requirements 20.2**

### Property 50: API Key Encryption at Rest

_For any_ API key stored in the database, the stored value should be encrypted, not plaintext.

**Validates: Requirements 20.4**

## Error Handling

### File Processing Errors

**Strategy**: Graceful degradation with detailed error reporting

**Error Types**:

1. **File Upload Errors**
   - Invalid file type: Return 400 with supported formats
   - File too large: Return 413 with size limit
   - Corrupted file: Return 422 with corruption details

2. **Parsing Errors**
   - PDF extraction failure: Log error, notify user, allow retry
   - SystemVerilog syntax error: Return line numbers and error description
   - Malformed document: Return specific parsing error with context

**Implementation**:

```python
class FileProcessingError(Exception):
    def __init__(self, file_type: str, error_details: str, line_number: int = None):
        self.file_type = file_type
        self.error_details = error_details
        self.line_number = line_number

    def to_response(self):
        return {
            "error": "file_processing_failed",
            "file_type": self.file_type,
            "details": self.error_details,
            "line_number": self.line_number
        }
```

### Agent Execution Errors

**Strategy**: Retry with exponential backoff, fallback to alternative approaches

**Error Types**:

1. **LLM API Errors**
   - Rate limit exceeded: Queue request, retry after delay
   - Model unavailable: Switch to fallback model
   - Timeout: Retry with increased timeout
   - Invalid response: Log error, request regeneration

2. **Agent Logic Errors**
   - Parsing failure: Return partial results, flag for manual review
   - Alignment failure: Lower confidence threshold, flag ambiguities
   - Generation failure: Use pattern library fallback

**Implementation**:

```python
async def execute_with_retry(
    agent: Agent,
    context: PipelineContext,
    max_retries: int = 3
) -> AgentResult:
    for attempt in range(max_retries):
        try:
            result = await agent.execute(context)
            return result
        except GroqAPIError as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(delay)
                continue
            else:
                # Final attempt failed, return error result
                return AgentResult(
                    agent_name=agent.name,
                    success=False,
                    error=str(e)
                )
```

### Database Errors

**Strategy**: Transaction rollback, data integrity preservation

**Error Types**:

1. **Connection Errors**
   - Connection lost: Retry with connection pool
   - Timeout: Increase timeout, retry
   - Authentication failure: Log critical error, alert admin

2. **Data Errors**
   - Duplicate key: Return 409 Conflict
   - Validation error: Return 422 with validation details
   - Transaction failure: Rollback, return 500 with safe error message

**Implementation**:

```python
async def safe_database_operation(operation: Callable, session: ClientSession):
    async with session.start_transaction():
        try:
            result = await operation()
            await session.commit_transaction()
            return result
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Database operation failed: {e}")
            raise DatabaseError("Operation failed, changes rolled back")
```

### WebSocket Errors

**Strategy**: Automatic reconnection, message queuing

**Error Types**:

1. **Connection Errors**
   - Connection dropped: Attempt reconnection with exponential backoff
   - Send failure: Queue message, retry on reconnection
   - Receive timeout: Send ping, check connection health

**Implementation**:

```python
class WebSocketManager:
    async def send_with_retry(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            # Queue message for when client reconnects
            await self.message_queue.put(message)
            logger.warning("WebSocket disconnected, message queued")
```

### Security Errors

**Strategy**: Fail securely, log security events

**Error Types**:

1. **Authentication Errors**
   - Invalid token: Return 401, log attempt
   - Expired token: Return 401 with refresh instruction
   - Missing token: Return 401

2. **Authorization Errors**
   - Insufficient permissions: Return 403, log attempt
   - Resource not owned: Return 404 (don't reveal existence)

3. **Input Validation Errors**
   - Malicious file: Reject, log security event, alert admin
   - SQL injection attempt: Sanitize, log, block IP if repeated
   - XSS attempt: Sanitize, log security event

**Implementation**:

```python
def verify_project_ownership(user_id: str, project_id: str, db: Database):
    project = db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project["user_id"] != user_id:
        logger.warning(f"Unauthorized access attempt: user {user_id} to project {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

## Testing Strategy

### Overview

The SVA-Chatbot testing strategy employs a dual approach combining unit tests for specific scenarios and property-based tests for comprehensive coverage. This ensures both concrete correctness and general behavioral guarantees.

### Unit Testing

**Framework**: pytest (Python backend), Jest (React frontend)

**Scope**: Specific examples, edge cases, integration points

**Unit Test Categories**:

1. **API Endpoint Tests**
   - Test each endpoint with valid inputs
   - Test authentication and authorization
   - Test error responses
   - Example: Test POST /api/projects creates project with correct metadata

2. **File Processing Tests**
   - Test each file format with sample documents
   - Test extraction accuracy with known content
   - Test error handling with corrupted files
   - Example: Test PDF extraction with a sample PDF containing known text

3. **Agent Integration Tests**
   - Test agent initialization
   - Test agent communication
   - Test pipeline execution with sample data
   - Example: Test Spec Parser with a sample specification document

4. **Database Tests**
   - Test CRUD operations
   - Test transaction rollback
   - Test index usage
   - Example: Test project creation and retrieval

5. **Frontend Component Tests**
   - Test component rendering
   - Test user interactions
   - Test state management
   - Example: Test FileUpload component accepts valid files

**Example Unit Test**:

```python
def test_project_creation():
    """Test that creating a project stores correct metadata"""
    client = TestClient(app)
    response = client.post(
        "/api/projects",
        json={"name": "Test Project", "description": "Test Description"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    project = response.json()
    assert project["name"] == "Test Project"
    assert project["description"] == "Test Description"
    assert "created_at" in project
    assert project["status"] == "draft"
```

### Property-Based Testing

**Framework**: Hypothesis (Python backend), fast-check (TypeScript frontend)

**Configuration**: Minimum 100 iterations per property test

**Scope**: Universal properties across all inputs

**Property Test Categories**:

1. **Round-Trip Properties**
   - Database storage and retrieval
   - File upload and download
   - Serialization and deserialization
   - Example: Store project → Retrieve project → Should be equivalent

2. **Invariant Properties**
   - Confidence scores always between 0.0 and 1.0
   - Quality scores always between 0.0 and 1.0
   - Project statistics match actual counts
   - Example: For any assertion, confidence_score ∈ [0.0, 1.0]

3. **Metamorphic Properties**
   - Adding then removing an assertion returns to original state
   - Parsing then unparsing preserves structure
   - Example: For any project, delete_assertion(add_assertion(project, a), a) ≈ project

4. **Error Handling Properties**
   - Invalid inputs always return errors
   - Errors always include descriptive messages
   - Example: For any invalid file type, upload returns 400 error

**Example Property Test**:

```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1, max_size=100),
    description=st.text(max_size=500)
)
def test_project_round_trip(name, description):
    """
    Feature: sva-chatbot, Property 30: Project Metadata Persistence

    For any created project, storing it and then retrieving it
    should produce a project record with the same name, description, and user_id.
    """
    # Create project
    project_id = create_project(name, description, test_user_id)

    # Retrieve project
    retrieved = get_project(project_id)

    # Verify equivalence
    assert retrieved["name"] == name
    assert retrieved["description"] == description
    assert retrieved["user_id"] == test_user_id
```

**Property Test Tagging Convention**:
Each property test must include a comment referencing its design document property:

```python
"""
Feature: sva-chatbot, Property {number}: {property_text}
"""
```

### Integration Testing

**Scope**: End-to-end workflows

**Test Scenarios**:

1. **Complete Generation Pipeline**
   - Upload specification and RTL
   - Trigger generation
   - Verify assertions are created
   - Check traceability links

2. **Real-Time Updates**
   - Connect WebSocket
   - Start generation
   - Verify status updates received
   - Verify completion notification

3. **User Interaction Flow**
   - Create project
   - Upload files
   - Generate assertions
   - Edit assertion
   - Provide feedback
   - Export results

**Example Integration Test**:

```python
async def test_complete_generation_pipeline():
    """Test the entire pipeline from upload to assertion generation"""
    # Create project
    project_id = await create_project("Integration Test")

    # Upload specification
    spec_id = await upload_specification(project_id, "sample_spec.md")

    # Upload RTL
    rtl_id = await upload_rtl(project_id, "sample_design.sv")

    # Start generation
    async with websocket_connect(f"/ws/generation?project={project_id}") as ws:
        await trigger_generation(project_id)

        # Collect status updates
        updates = []
        async for message in ws:
            updates.append(message)
            if message["status"] == "completed":
                break

        # Verify pipeline executed
        assert any(u["agent"] == "spec_parser" for u in updates)
        assert any(u["agent"] == "rtl_analyzer" for u in updates)
        assert any(u["agent"] == "sva_generator" for u in updates)

    # Verify assertions were created
    assertions = await get_assertions(project_id)
    assert len(assertions) > 0

    # Verify traceability
    for assertion in assertions:
        assert "requirement_id" in assertion
        assert "rtl_module" in assertion
        assert len(assertion["traceability"]["rtl_signals"]) > 0
```

### Performance Testing

**Scope**: Response times, throughput, resource usage

**Test Scenarios**:

1. **File Processing Performance**
   - Large PDF processing time < 30 seconds
   - Large RTL file parsing time < 10 seconds

2. **Agent Execution Performance**
   - Complete pipeline for typical project < 2 minutes
   - Individual agent execution < 30 seconds

3. **Database Performance**
   - Query response time < 100ms for indexed queries
   - Bulk insertion performance

4. **Concurrent User Load**
   - Support 10 concurrent users
   - WebSocket message delivery latency < 500ms

### Test Data Management

**Strategy**: Use realistic sample data for testing

**Test Data Sets**:

1. **Sample Specifications**
   - Simple handshake protocol spec
   - FIFO specification
   - AXI protocol subset
   - Complex multi-requirement spec

2. **Sample RTL Designs**
   - Simple handshake module
   - FIFO implementation
   - AXI slave interface
   - State machine examples

3. **Expected Assertions**
   - Hand-written correct assertions for sample designs
   - Used for validation and comparison

**Test Data Location**: `tests/fixtures/`

### Continuous Integration

**CI Pipeline**:

1. **On Pull Request**:
   - Run all unit tests
   - Run property tests (100 iterations)
   - Run linting and type checking
   - Check code coverage (target: 80%)

2. **On Merge to Main**:
   - Run full test suite
   - Run integration tests
   - Run performance tests
   - Deploy to staging environment

3. **Nightly**:
   - Run property tests with 1000 iterations
   - Run extended performance tests
   - Generate test coverage reports

**Tools**:

- GitHub Actions for CI/CD
- pytest-cov for coverage reporting
- pytest-benchmark for performance tracking

### Test Coverage Goals

**Targets**:

- Unit test coverage: 80% of code
- Property test coverage: All 50 correctness properties
- Integration test coverage: All major user workflows
- API endpoint coverage: 100% of endpoints

**Coverage Monitoring**:

- Track coverage trends over time
- Require coverage maintenance in PRs
- Generate coverage reports in CI
