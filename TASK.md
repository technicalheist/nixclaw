# NixClaw - Multi-Agent AI System

## Project Vision
Build a powerful, Python-based multi-agent AI system **using Microsoft's AutoGen framework** similar to GitHub Copilot, Claude, or OpenCode that can autonomously break down complex tasks, dynamically create specialized agents, and execute them efficiently in isolated environments. This system will be designed for long-running background operations with human-in-the-loop capabilities via Telegram.

**Project Name**: **NixClaw**
**PyPI Package**: `nixclaw` (to be published when complete)
**Framework**: Built on top of **AutoGen 0.7.5** (autogen-agentchat, autogen-core, autogen-ext)
**Language**: Python 3.10+
**Core Dependencies**: autogen-agentchat, autogen-core, autogen-ext, pydantic, python-dotenv, aiofiles

### Dual Usage Design
NixClaw is designed to work in two ways:

**1. As a CLI tool (terminal usage):**
```bash
# Install from PyPI (once published)
pip install nixclaw

# One-shot task
nixclaw "Analyze the project and fix bugs"

# Interactive mode
nixclaw --interactive

# Team mode with specific agent profiles
nixclaw --team CodeGenerator,Analyzer "Build a REST API"

# Or via python module
python -m nixclaw "Your task here"
```

**2. As a Python library (importable package):**
```python
import asyncio
from nixclaw import Orchestrator, AgentFactory, ManagedAgent, get_settings

# Simple: run a task through the orchestrator
async def main():
    orchestrator = Orchestrator()
    result = await orchestrator.run("Analyze the codebase")
    print(result)
    await orchestrator.close()

asyncio.run(main())

# Advanced: create and manage agents directly
async def advanced():
    factory = AgentFactory.get_instance()
    agent = await factory.create_agent("CodeGenerator")
    result = await agent.run("Write a hello world script")
    print(agent.get_result_text(result))
    await factory.cleanup_all()

asyncio.run(advanced())
```

---

## Core Architecture

### AutoGen Integration
This project leverages **AutoGen 0.7.5** (pyautogen) as the foundation:

**AutoGen Components Used**:
- **AssistantAgent**: LLM-powered agent for reasoning and decision making
- **UserProxyAgent**: Human interaction point (will adapt for Telegram integration)
- **GroupChat**: Multi-agent conversation orchestration
- **ConversableAgent**: Base class for all agent types
- **Agent.register_for_llm_execution()**: For tool/function execution registration
- **ConversationManager**: Manages conversation history between agents
- **OpenAI ChatCompletion**: Model client for LLM interactions

**Why AutoGen 0.7.5**:
- Mature, stable version with proven production use
- Conversation-based agent interaction (message passing)
- Flexible tool/function calling system
- Support for both sync and async execution
- Multi-agent orchestration via GroupChat
- Built-in conversation history management
- Code execution capabilities
- Community adoption and extensive examples

### 1. Agent Hierarchy & Design

#### 1.1 Orchestrator Agent (Primary Manager)
- **Base Class**: Extends `ConversableAgent` (or custom subclass of `AssistantAgent`)
- **Role**: Task coordinator and dynamic agent factory
- **Communication**: Uses AutoGen's conversation message protocol
- **Responsibilities**:
  - Analyze incoming tasks via LLM (OpenAI ChatCompletion)
  - Break down tasks into subtasks (LLM-driven analysis)
  - Create child agents dynamically based on task requirements
  - Orchestrate via conversation and `GroupChat` with child agents
  - Monitor agent execution and lifecycle
  - Aggregate results and manage context flow from multiple agents
  - Handle task state management and persistence
  - Make decisions on agent reassignment or retry logic
  - Register and execute tools/functions via AutoGen's tool registration system

#### 1.2 Child/Specialist Agents
- **Base Class**: Extends `ConversableAgent` (or `AssistantAgent`)
- **Role**: Execute assigned tasks
- **Characteristics**:
  - Dynamically spawned by Orchestrator as AssistantAgent instances
  - Task-specific or domain-specific configurations (different system prompts)
  - Can spawn their own sub-agents (hierarchical GroupChats)
  - Have access to shared context/memory via message history
  - Report back to parent agent with results/logs via message protocol
  - Can use other agents as tools (via Agent-as-Tool pattern)
  - Participate in parent's GroupChat for coordination and monitoring
  - Execute via AutoGen's conversation loop with tool registration

#### 1.3 Agent Pool Management
- Track active agents
- Manage agent lifecycle (creation, execution, termination)
- Resource allocation (CPU, memory limits per agent)
- Agent reusability for similar tasks

---

## Feature Requirements (Detailed Breakdown)

### 2. Task Breakdown System
**Requirement**: Agent breaks down complex tasks into manageable subtasks

- **Functionality**:
  - LLM-driven task decomposition analysis
  - Generate hierarchical task tree (DAG - Directed Acyclic Graph)
  - Identify task dependencies and parallelizable tasks
  - Create priority-ordered todo list with estimated complexity
  - Store task metadata (type, required tools, agent specialty needed, time estimate)
  - Track task status: `pending`, `in_progress`, `completed`, `failed`, `blocked`

- **Data Structure**:
  ```
  Task {
    id: unique_id
    parent_task_id: reference to parent
    title: string
    description: string
    type: enum (code, analysis, research, system, etc)
    subtasks: [Task]
    status: string
    priority: int
    estimated_time: float
    required_tools: [string]
    assigned_agent_id: string
    result: any
    error: string
    created_at: timestamp
    completed_at: timestamp
    dependencies: [task_id]
    estimated_tokens: int
  }
  ```

---

### 3. Dynamic Agent Assignment
**Requirement**: Orchestrator dynamically creates and assigns agents as needed

- **Agent Factory Pattern**:
  - Define agent templates/profiles based on specialty
  - Profiles: `CodeGenerator`, `Analyzer`, `Researcher`, `SystemAdmin`, `Debugger`, etc.
  - On-demand agent instantiation based on task requirements
  - Agent configuration injection (tools, system prompt, context)

- **Assignment Strategy**:
  - Match task type to appropriate agent profile
  - Consider agent workload (queue size, current tasks)
  - Implement load balancing across agents
  - Agent pool reuse (don't recreate if suitable agent exists and available)
  - Timeout and failure handling with agent reallocation

- **Agent Metadata & Tracking**:
  ```
  Agent {
    id: unique_id
    profile: string (specialty)
    status: enum (idle, busy, failed, terminated)
    assigned_tasks: [task_id]
    current_task_id: task_id
    tools_available: [tool_names]
    context_window: int
    created_at: timestamp
    last_activity: timestamp
    error_count: int
    token_usage: {total, used, remaining}
  }
  ```

---

### 4. Agent-as-Tool Pattern
**Requirement**: Agents can be dynamically invoked as tools by other agents

- **Implementation**:
  - Expose agent as callable tool via function signature
  - Standardized interface: `agent_execute(agent_id, task_description, context) -> result`
  - Support agent chaining (A → B → C)
  - Context passing between agents
  - Result wrapping and error handling
  - Avoid circular dependencies (cycle detection)

- **Tool Function**:
  ```python
  {
    "name": "delegate_to_agent",
    "description": "Delegate a subtask to a specialized agent",
    "parameters": {
      "agent_profile": "string - e.g., 'CodeGenerator'",
      "task": "string - task description",
      "context": "dict - relevant context",
      "priority": "high|normal|low"
    }
  }
  ```

---

### 5. Lightweight Architecture
**Requirement**: Designed for isolated, resource-efficient Docker environments

- **Design Principles**:
  - Stateless agent instances (state stored externally)
  - Minimal dependencies (use only autogen and essential libraries)
  - Docker-ready (Dockerfile included)
  - Resource limits: CPU, memory, timeout per task
  - Container health checks
  - Graceful shutdown and cleanup

- **Container Configuration**:
  - Max memory per agent: configurable (default 512MB)
  - CPU share limits: configurable
  - Task execution timeout: configurable per task type
  - Network isolation capability
  - Volume mounts for input/output

---

### 6. Core Tool Set (Always Available)

#### 6.1 File Operations
1. **read_file** - Read file contents (with line range support)
   - Handle large files (streaming/chunking)
   - Support multiple encodings
   
2. **write_file** - Write/create files
   - Append mode support
   - Handle existing files (overwrite/merge options)
   - Directory creation if needed
   
3. **delete_file** - Delete files safely
   - Confirmation for critical files
   - Recursive directory deletion option

#### 6.2 Directory Operations
1. **list_dir** - List directory contents
   - Recursive listing support
   - Filter by file type
   - Sort options
   
2. **create_dir** - Create directories
   - Recursive creation (mkdir -p equivalent)

#### 6.3 Search Operations
1. **search_files** - Find files by pattern/glob
   - Recursive search
   - Size filters
   - Modified date filters
   
2. **search_content** - Search file contents
   - Regex support
   - Case sensitivity option
   - Line context output
   - Max matches limit

#### 6.4 Shell Command Execution (CRITICAL - Section 7)
*See detailed section below*

---

### 7. Smart Shell Command Execution Tool (Priority Implementation)

**Requirement**: Intelligent command execution with safety, isolation, and context awareness

#### 7.1 Core Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Infinite loops / Hangs** | Timeout mechanism with SIGTERM → SIGKILL escalation |
| **Stuck processes** | Watchdog thread monitoring, resource limits, process tree cleanup |
| **Large output flood** | Output streaming to file, chunked buffering, size limit cutoffs |
| **Main flow blocking** | Always run in parallel (threading/multiprocessing), non-blocking returns |
| **Unintended side effects** | Sandboxing, environment variable isolation, working directory isolation |
| **No context awareness** | Pre-execution validation, dry-run capability, LLM pre-analysis |
| **Resource exhaustion** | Memory/CPU limits per process, disk quota enforcement |
| **Interruptible execution** | Signal handling, graceful termination, cleanup procedures |

#### 7.2 Implementation Strategy

**Architecture Pattern**: Command Executor Service
- Dedicated background worker pool (thread/process based)
- Queue-based task distribution
- Non-blocking execution tracking
- Result callback mechanism

**Execution Flow**:
```
1. Agent requests command execution
2. Pre-flight validation:
   - Syntax check
   - Permission check
   - Environment variable validation
   - Estimated resource needs
   - LLM safety review (for suspicious commands)
3. Execute in background worker:
   - Isolation (namespace/chroot/Docker preferred)
   - Resource limits (cgroups)
   - Output capture (file + memory buffer)
   - Signal handling
   - Watchdog timer
4. Real-time monitoring:
   - Memory/CPU usage tracking
   - Output file tailing for logs
   - Status updates to Telegram
5. Graceful termination on timeout:
   - SIGTERM (15 seconds grace)
   - SIGKILL if needed
   - Process tree cleanup
   - Partial result collection
6. Return result with metadata:
   - Exit code
   - Stdout/stderr
   - Duration
   - Resource usage
   - Warnings/errors
```

**Data Structure**:
```python
CommandExecution {
  id: unique_id
  command: string
  working_dir: string
  timeout: int (seconds)
  environment: dict (isolated env vars)
  status: enum (pending, running, completed, timeout, failed, cancelled)
  exit_code: int
  stdout: string (or file reference)
  stderr: string (or file reference)
  start_time: timestamp
  end_time: timestamp
  duration: float
  resource_usage: {
    peak_memory_mb: float
    peak_cpu_percent: float
    process_count: int
  }
  output_truncated: bool
  max_output_size_bytes: int
  agent_id: string (who requested)
  request_id: string (for tracking)
}
```

**Configuration Options**:
```env
COMMAND_EXECUTOR_TIMEOUT_DEFAULT=300  # seconds
COMMAND_EXECUTOR_MAX_OUTPUT_SIZE=10485760  # 10MB
COMMAND_EXECUTOR_MEMORY_LIMIT=512  # MB per command
COMMAND_EXECUTOR_CPU_SHARES=1024
COMMAND_EXECUTOR_MAX_CONCURRENT=5
COMMAND_EXECUTOR_ENABLE_SANDBOX=true
COMMAND_EXECUTOR_DANGEROUS_COMMANDS_WHITELIST=""  # comma-separated
COMMAND_EXECUTOR_DANGEROUS_COMMANDS_BLACKLIST="rm -rf /,: () { : | : & };:"
```

**Safety Rules**:
- Blacklist dangerous patterns (rm -rf /, fork bombs, etc.)
- Whitelist mode for production (only approved commands)
- Never execute with elevated privileges
- Read-only filesystem option for sensitive areas
- Network isolation if needed

#### 7.3 Output Handling Strategy
- Stream large outputs to temporary file
- Keep last N lines in memory for quick access
- Provide file handle for agent to stream results
- Implement output tail capability (like `tail -f`)
- Compression for long-running command outputs

---

### 8. Human-in-Loop via Telegram
**Requirement**: Integration with Telegram for user input and agent status updates

#### 8.1 Telegram Bot Setup
- Bot token management (store in .env)
- User ID whitelist (store in .env)
- Webhook vs polling configuration
- Message queue for burst handling

#### 8.2 Input Channel
**Functionality**:
- User sends task/question to bot
- Bot forwards to Orchestrator Agent
- Agent processes and reports back
- Support multi-line inputs, file uploads
- Command-style inputs: `/task [description]`

**Tool Function**:
```python
{
  "name": "wait_for_human_input",
  "description": "Wait for user input from Telegram with timeout",
  "parameters": {
    "prompt": "string - what to ask user",
    "timeout": "int - seconds to wait",
    "expected_format": "string - guidance on expected format",
    "options": "[string] - predefined options for quick reply"
  }
}
```

#### 8.3 Output/Logging Channel
- Send task start/end notifications
- Real-time progress updates (milestone-based, not every step)
- Error alerts with context
- Final result summary
- Configurable verbosity levels (silent, summary, detailed, debug)

**Message Types**:
- `TASK_STARTED` - Agent starting new task
- `TASK_PROGRESS` - Milestone update (every X% or important checkpoint)
- `TASK_COMPLETED` - Final result
- `TASK_FAILED` - Error with stack trace
- `COMMAND_ALERT` - Important shell command output (errors, warnings)
- `HUMAN_INPUT_NEEDED` - Waiting for user response
- `SYSTEM_ALERT` - Resource issues, agent crashes, etc.

**Rate Limiting**: 
- Max messages per minute (configurable)
- Batch updates if too frequent
- Cancel low-priority updates if rate exceeded

---

### 9. Async Execution & Non-Streaming
**Requirement**: Background execution with optional streaming, default off

- **Execution Models**:
  1. **Fire & Forget**: Task submitted, returns immediately with task_id
  2. **Poll**: Client polls for status via task_id
  3. **Webhook Callback**: When done, POST to provided webhook
  4. **Telegram**: Status updates sent to Telegram (default)

- **Task Queue Management**:
  - Persistent queue (Redis/Database backed)
  - Priority queue support
  - Task persistence across restarts
  - Resume capability for interrupted tasks

- **Status Polling API**:
  ```python
  get_task_status(task_id) -> {
    id: string,
    status: string,
    progress: int (0-100),
    current_subtask: string,
    started_at: timestamp,
    estimated_completion: timestamp,
    logs: [string],
    intermediate_results: dict
  }
  ```

---

### 10. Environment Configuration (.env File)
**Requirement**: All credentials and config in .env

```env
# === OpenAI / LLM Configuration ===
LLM_MODEL=qwen3.5-plus
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://llm.shivrajan.com/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_REQUEST_TIMEOUT=60

# === Telegram Bot Configuration ===
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USER_IDS=123456789,987654321  # comma-separated whitelist
TELEGRAM_LOG_LEVEL=info  # debug, info, warning, error
TELEGRAM_MESSAGE_RATE_LIMIT=10  # max messages per minute
TELEGRAM_ENABLE_NOTIFICATIONS=true

# === Agent Configuration ===
AGENT_MAX_CONCURRENT_AGENTS=10
AGENT_TASK_TIMEOUT_DEFAULT=3600  # seconds (1 hour)
AGENT_MEMORY_CONTEXT_LIMIT=8000  # tokens
AGENT_MAX_RETRIES=3
AGENT_RETRY_BACKOFF_FACTOR=2  # exponential backoff
AGENT_ENABLE_REFLECTION=true  # agent reflects on tool use
AGENT_STREAMING_ENABLED=false  # disable streaming by default

# === Shell Command Executor Configuration ===
COMMAND_EXECUTOR_TIMEOUT_DEFAULT=300  # seconds
COMMAND_EXECUTOR_MAX_OUTPUT_SIZE=10485760  # 10MB
COMMAND_EXECUTOR_MEMORY_LIMIT=512  # MB per command
COMMAND_EXECUTOR_CPU_SHARES=1024
COMMAND_EXECUTOR_MAX_CONCURRENT=5
COMMAND_EXECUTOR_ENABLE_SANDBOX=true
COMMAND_EXECUTOR_DANGEROUS_COMMANDS_BLACKLIST="rm -rf /,: () { : | : & };:"
COMMAND_EXECUTOR_WORKING_DIR=/tmp/agent_workdir

# === Storage & Persistence ===
DATABASE_URL=sqlite:///./agent_tasks.db  # or postgresql://...
REDIS_URL=redis://localhost:6379/0  # for task queue
STORAGE_LOGS_DIR=/var/log/autogen-agent
STORAGE_TEMP_DIR=/tmp/autogen-agent

# === System Configuration ===
LOG_LEVEL=info  # debug, info, warning, error
DEBUG_MODE=false
MAX_RUN_ITERATIONS=50  # max iterations before stopping agent loop
HEARTBEAT_INTERVAL=30  # seconds - agent health check
TASK_PERSISTENCE_ENABLED=true

# === Docker/Container Configuration ===
CONTAINER_MEMORY_LIMIT=1g
CONTAINER_CPU_LIMIT=1.0
CONTAINER_NETWORK_ISOLATED=false  # true for security

# === Advanced Options ===
ENABLE_HUMAN_IN_LOOP=true
ENABLE_TASK_BREAKDOWN_VISUALIZATION=false  # for debugging
API_PORT=8000
API_HOST=0.0.0.0
```

---

### 11. Max Run / Iteration Limits
**Requirement**: Prevent infinite loops and runaway agent processes

- **Configuration**:
  - `MAX_RUN_ITERATIONS`: Global max iterations per task execution (default: 50)
  - `MAX_RETRIES_PER_TASK`: Max retries for failed tasks (default: 3)
  - `TASK_TIMEOUT`: Per-task execution timeout (default: 3600s = 1 hour)
  - `AGENT_SESSION_TIMEOUT`: Max agent instance lifetime (default: 86400s = 24 hours)

- **Monitoring & Enforcement**:
  - Track iteration counter in agent state
  - Check on each loop iteration
  - Graceful shutdown on limit approached (alert via Telegram)
  - Log final state before termination
  - Partial result collection

- **Implementation**:
  ```python
  while iteration < MAX_RUN_ITERATIONS:
    if iteration > MAX_RUN_ITERATIONS * 0.9:
      send_telegram_alert(f"Agent approaching limit: {iteration}/{MAX_RUN_ITERATIONS}")
    
    if task_completed(agent):
      break
    
    result = agent.perform_action()
    iteration += 1
    
    if iteration >= MAX_RUN_ITERATIONS:
      logger.error("Max iterations reached, terminating task")
      send_telegram_alert(f"Task {task_id} reached max iterations limit")
      break
  ```

---

## Additional Considerations (Beyond Initial Requirements)

### 12. Error Handling & Recovery

#### 12.1 Retry Strategy
- Exponential backoff for transient failures
- Different retry logic for different error types
- Circuit breaker pattern for API failures
- Dead letter queue for failed tasks

#### 12.2 Error Categories & Handling
```
- LLM API errors → Retry with backoff
- Agent crash → Restart agent, reassign task
- Resource exhaustion → Queue task, wait for resources
- Timeout → Partial result, escalate to human
- Network errors → Queue and retry
- Disk full → Alert and cleanup old logs
```

#### 12.3 Graceful Degradation
- Fallback to simpler agent profiles if advanced ones fail
- Reduce context window if memory constrained
- Skip non-critical tools if unavailable
- Continue with partial results

---

### 13. Context & Memory Management

#### 13.1 Shared Context Types
1. **Task Context**: Parent task info, related tasks, project context
2. **Execution Context**: Previous task outputs, intermediate results
3. **Agent Context**: Other agents' status, shared knowledge base
4. **Semantic Memory**: Learned information, patterns discovered

#### 13.2 Context Storage Options
- **Short-term**: In-memory cache (active only)
- **Medium-term**: Redis for fast access
- **Long-term**: Database (PostgreSQL) for persistence
- **Semantic**: Vector database (Pinecone/Weaviate) for similarity search

#### 13.3 Context Pruning
- Implement sliding window (keep last N interactions)
- Token budget enforcement per agent
- Context compression/summarization
- Archival of old context

---

### 14. Monitoring, Logging & Observability

#### 14.1 Metrics to Track
- Task completion rate (success/failure/timeout)
- Average task duration
- Agent utilization (active time vs idle)
- Token usage and costs
- Command execution success rate
- API rate limits and errors
- Memory and CPU usage trends

#### 14.2 Logging Strategy
- Structured logging (JSON format)
- Different log levels per component
- Rotating file logs (size + time based)
- Log aggregation (optional: ELK stack)
- Audit logging for sensitive operations

#### 14.3 Health Checks
- Agent heartbeat (30s interval)
- Queue monitoring (detect stuck jobs)
- Database connection health
- LLM API availability
- Telegram bot connectivity

---

### 15. Security & Access Control

#### 15.1 API Authentication
- API key for external task submission
- Rate limiting per API key
- Audit logging of API calls

#### 15.2 File System Security
- Chroot/sandbox for command execution
- Read-only access to sensitive directories
- File permission checks before I/O
- Path traversal prevention

#### 15.3 Agent Isolation
- Process isolation (separate memory space)
- Network isolation (no external network)
- Resource limits (prevent resource exhaustion attacks)
- Timeout enforcement

#### 15.4 Secret Management
- Never log sensitive values (API keys, passwords)
- Encrypt sensitive data at rest
- Rotate credentials periodically
- Audit access to secrets

---

### 16. Scalability & Performance

#### 16.1 Horizontal Scaling
- Stateless agent design enables scaling
- Distributed task queue shared across instances
- Load balancing across multiple agent workers
- Database-backed state for instance independence

#### 16.2 Performance Optimization
- Connection pooling for LLM API
- Batching API requests where possible
- Caching tool results (configurable TTL)
- Lazy loading of large contexts
- Parallel task execution where possible

#### 16.3 Cost Management
- Token usage tracking and alerts
- Cost per task calculation
- Budget limits and alerts
- Model selection optimization (use cheaper models where possible)

---

### 17. Testing Strategy

#### 17.1 Unit Tests
- Individual tool testing (file ops, commands)
- Agent decision logic
- Error handling paths
- Context management

#### 17.2 Integration Tests
- Multi-agent task execution
- Agent-to-agent communication
- Telegram integration (mock)
- Database persistence

#### 17.3 Load Tests
- Max concurrent agents
- Task queue throughput
- Command execution under load
- Database connection pool exhaustion

#### 17.4 Safety Tests
- Command injection prevention
- Path traversal attacks
- Resource limit enforcement
- Timeout functionality

---

### 18. Deployment & Operations

#### 18.1 Deployment Options
1. **Docker Container** - Single agent worker
2. **Docker Compose** - Multi-service setup (agent, queue, DB, API)
3. **Kubernetes** - Production-grade scaling
4. **Systemd Service** - Simple server deployment

#### 18.2 CI/CD Pipeline
- Code linting and formatting checks
- Unit test execution
- Integration tests
- Docker image building
- Deployment automation

#### 18.3 Monitoring & Alerting
- Prometheus metrics export
- Grafana dashboards
- Alert rules (high error rate, resource exhaustion)
- On-call escalation

---

## Implementation Phases

### Phase 1: Core Foundation (Week 1-2)
- [ ] Orchestrator Agent basic structure
- [ ] Task breakdown system
- [ ] Basic tool set (file ops, search)
- [ ] Database/storage setup
- [ ] .env configuration

### Phase 2: Advanced Agent System (Week 3-4)
- [ ] Dynamic agent factory
- [ ] Agent-as-tool pattern
- [ ] Agent lifecycle management
- [ ] Context management system
- [ ] Multi-agent communication

### Phase 3: Shell Command Tool (Week 5-6) - **CRITICAL**
- [ ] Background executor framework
- [ ] Timeout and safety mechanisms
- [ ] Resource limiting
- [ ] Output handling for large outputs
- [ ] Signal handling and graceful shutdown
- [ ] Comprehensive testing and safety validation

### Phase 4: Human-in-Loop & Async (Week 7-8)
- [ ] Telegram bot integration (input + logging)
- [ ] Async task execution
- [ ] Task queue and persistence
- [ ] Status polling API
- [ ] Callback mechanisms

### Phase 5: Production Hardening (Week 9-10)
- [ ] Error handling and recovery
- [ ] Monitoring and observability
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Documentation and tutorials

### Phase 6: Deployment & Scaling (Week 11-12)
- [ ] Docker containerization
- [ ] Kubernetes setup (optional)
- [ ] CI/CD pipeline
- [ ] Load testing
- [ ] Production deployment

---

## Success Criteria

- [ ] Agent can autonomously complete multi-step coding tasks
- [ ] Task breakdown produces accurate, non-redundant subtasks
- [ ] Dynamic agents created and assigned efficiently
- [ ] Shell commands execute safely with timeout enforcement
- [ ] Large command outputs handled without blocking main process
- [ ] Telegram integration provides real-time status updates
- [ ] System runs for 24+ hours without memory leaks
- [ ] Recovers gracefully from agent failures
- [ ] Achieves <500ms latency for quick tasks
- [ ] Costs optimized (uses efficient models)
- [ ] Comprehensive audit logging and monitoring
- [ ] Security validated (no shell injection, path traversal, etc.)

---

## Repository Structure

```
nixclaw/                         # Project root
├── TASK.md                      # This file
├── .env.example                 # Example environment variables
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata & PyPI config
├── Dockerfile                   # Container setup
├── docker-compose.yml           # Multi-service setup
│
├── nixclaw/                     # Main package (importable + CLI)
│   ├── __init__.py              # Public API exports (for library usage)
│   ├── __main__.py              # python -m nixclaw entry point
│   ├── main.py                  # CLI entry point (argparse)
│   ├── config.py                # Configuration loader (.env)
│   ├── logger.py                # Logging setup
│   │
│   ├── agents/
│   │   ├── orchestrator.py      # Main orchestrator agent
│   │   ├── agent_factory.py     # Dynamic agent creation
│   │   ├── agent_profiles.py    # Pre-defined agent types
│   │   └── base_agent.py        # Base agent class (ManagedAgent)
│   │
│   ├── tools/
│   │   ├── file_operations.py   # read, write, delete files
│   │   ├── directory_ops.py     # list, create directories
│   │   ├── search_tools.py      # search files and content
│   │   ├── shell_executor.py    # CRITICAL: Smart command execution
│   │   ├── agent_tool.py        # Agent-as-tool wrapper
│   │   └── telegram_tool.py     # Telegram integration
│   │
│   ├── core/
│   │   ├── task_manager.py      # Task tracking and state
│   │   ├── context_manager.py   # Context and memory management
│   │   ├── command_executor.py  # Background command execution service
│   │   └── event_bus.py         # Event-driven communication
│   │
│   ├── storage/
│   │   ├── database.py          # Database setup and queries
│   │   ├── models.py            # Pydantic data models
│   │   └── cache.py             # Redis caching layer
│   │
│   ├── api/
│   │   ├── app.py               # FastAPI application
│   │   ├── routes.py            # API endpoints
│   │   └── schemas.py           # Request/response schemas
│   │
│   └── integrations/
│       ├── telegram_bot.py      # Telegram bot setup
│       ├── openai_client.py     # LLM client wrapper
│       └── webhooks.py          # Callback/webhook handling
│
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── safety/                  # Security and safety tests
│   └── load/                    # Load and stress tests
│
├── docs/
│   └── examples/                # Example usage scenarios
│
└── scripts/
    ├── setup.sh                 # Environment setup
    └── run.sh                   # Start agent
```

---

## Key Decisions Made

1. **Data Persistence**: SQLite with SQLAlchemy + aiosqlite (async, upgradeable to PostgreSQL)
2. **Task Queue**: In-memory with database persistence (Redis optional for Phase 4)
3. **Async Framework**: AsyncIO (native, no Celery overhead)
4. **API Server**: FastAPI (Phase 4, stubs in place)
5. **Deployment**: Docker Compose (K8s optional for scale)
6. **Monitoring**: Structured logging + EventBus (Prometheus optional)
7. **Chat History**: In-memory with sliding window + token budget (ContextManager)
8. **Agent Profiles**: Hardcoded profiles with LLM-driven orchestrator selection

---

## Notes for Development Team

1. **Shell Executor is Critical**: This is the most complex and risky component. Allocate significant time for thorough testing, security audits, and edge case handling.

2. **Context Management**: The biggest issue with agents is context pollution and token budget exhaustion. Implement aggressive context pruning and summarization.

3. **Human-in-Loop**: Design careful prompts for human validation. Don't overwhelm users with too many questions.

4. **Cost Control**: Monitor token usage closely. Implement budget alerts and per-agent token limits.

5. **Observability**: From day one, instrument everything. Logging and metrics will be critical for debugging distributed agent issues.

6. **Database Schema**: Plan schema carefully. Agent state changes frequently; consider event sourcing pattern for audit trail.

7. **Testing Agent Failures**: Create chaos tests that deliberately crash agents mid-task and verify recovery.

8. **Documentation**: Document all agent decision logic. It's easy to lose track of why agents do what they do.

---

## Progress

### Phase 1: Core Foundation - COMPLETED
- [x] Project structure (nixclaw package)
- [x] Configuration system (.env / Pydantic)
- [x] Structured logging
- [x] Pydantic data models (Task, AgentMetadata, CommandExecution)
- [x] Core tools (file ops, dir ops, search, shell executor)
- [x] Agent system (base_agent, profiles, factory)
- [x] Orchestrator with task breakdown and delegation
- [x] Task manager with dependency resolution
- [x] Context manager with token budget
- [x] Event bus for decoupled communication
- [x] Command executor service with concurrency control
- [x] CLI entry point (one-shot, interactive, team modes)
- [x] Dual usage: importable library + CLI tool
- [x] Docker support

### Phase 2: Advanced Agent System - COMPLETED
- [x] SQLite database persistence (SQLAlchemy + aiosqlite)
- [x] SQLAlchemy ORM models (TaskRow, AgentRow, CommandRow)
- [x] Async repository layer (TaskRepository, CommandRepository)
- [x] TaskManager wired to database with fire-and-forget persistence
- [x] Task loading from database on startup (load_from_db)
- [x] Agent lifecycle management (factory, concurrency limits, cleanup)

### Phase 3: Shell Command Tool - COMPLETED
- [x] Background executor framework (CommandExecutorService)
- [x] Timeout with SIGTERM → SIGKILL escalation
- [x] Resource limiting (RLIMIT_AS for memory, RLIMIT_NPROC for fork bombs, RLIMIT_CPU)
- [x] Output truncation for large outputs
- [x] Signal handling and graceful shutdown
- [x] Safety pattern matching (13 dangerous patterns blocked)
- [x] Configurable blacklist from .env
- [x] Comprehensive safety test suite (23 safety tests)
- [x] Integration tests for all tools (17 tests)
- [x] Database persistence tests (9 tests)
- [x] Total: 71 tests passing

### Phase 4: Human-in-Loop & Async - COMPLETED
- [x] Telegram bot with python-telegram-bot (notifications, commands, human input)
- [x] Bot commands: /task, /status, /agents, /help
- [x] Human-in-the-loop: ask-and-wait pattern with timeout
- [x] Rate limiting on Telegram messages
- [x] User ID whitelisting for security
- [x] AsyncTaskQueue for background task execution with concurrency limits
- [x] Fire-and-forget task submission (returns task_id immediately)
- [x] Status polling by task_id
- [x] FastAPI REST API fully wired to Orchestrator
- [x] API endpoints: POST /tasks, GET /tasks/{id}, GET /tasks, POST /tasks/{id}/cancel, GET /agents/status, GET /health
- [x] Webhook callbacks on task completion via httpx
- [x] CLI modes: --serve (API server), --telegram (bot polling)
- [x] API + queue tests (11 new tests)
- [x] Total: 82 tests passing

### Phase 5: Production Hardening - COMPLETED
- [x] Retry logic with exponential backoff (retry_async, @with_retry decorator)
- [x] Secret masking in logs (API keys, tokens, passwords auto-masked)
- [x] Input sanitization (path traversal prevention, null byte removal)
- [x] Task input validation (empty check, length limits)
- [x] Health check system (LLM, database, Telegram, agents)
- [x] Health check wired to GET /health API endpoint
- [x] Verbose mode (--verbose/-v flag for debug output)
- [x] Clean output in normal mode (only final result, no AutoGen internals)
- [x] SQLite race condition fix (serial save queue)
- [x] Secondary Telegram log bot (TELEGRAM_BOT_TOKEN_LOG) for mirroring all output
- [x] Log bot uses requests in background thread (non-blocking, batched)
- [x] Security + retry tests (10 new tests)
- [x] Total: 97 tests passing

### Phase 6: Deployment & Publishing - COMPLETED
- [x] PyPI package published: `pip install nixclaw`
- [x] README.md with installation, quick start, API docs
- [x] MIT License
- [x] pyproject.toml with full metadata, classifiers, extras
- [x] Dockerfile and docker-compose.yml
- [x] 31 examples organized in docs/examples/ (cli, telegram, api, library)
- [x] GitHub repository: https://github.com/technicalheist/nixclaw
- [x] PyPI: https://pypi.org/project/nixclaw/

### All Phases Complete

---

**Document Version**: 1.4
**Last Updated**: Mar 23, 2026
**Project**: NixClaw
**PyPI**: https://pypi.org/project/nixclaw/
**GitHub**: https://github.com/technicalheist/nixclaw
