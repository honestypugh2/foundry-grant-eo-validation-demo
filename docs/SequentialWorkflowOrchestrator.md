# Sequential Workflow Orchestrator

This is an alternative orchestrator implementation based on **Microsoft Agent Framework's Sequential Workflow** pattern. It provides a cleaner, more modular approach to coordinating the compliance validation pipeline.

## Overview

The Sequential Workflow Orchestrator uses Agent Framework's `WorkflowBuilder` and `Executor` patterns to create a pipeline where each agent processes the task in turn, with output flowing from one to the next.

### Architecture

```
┌─────────────────┐
│   Start Input   │
│  (file_path)    │
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│ Document Ingestion │
│    Executor        │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Summarization     │
│    Executor        │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Compliance         │
│ Validation         │
│    Executor        │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Risk Scoring      │
│    Executor        │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Email Notification │
│    Executor        │
│  (Terminal Node)   │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Workflow Output   │
│  (final results)   │
└────────────────────┘
```

## Key Features

### 1. Sequential Execution
- Each executor processes the task in order
- Output flows linearly from one executor to the next
- Full conversation history maintained throughout

### 2. Typed Context Passing
- `WorkflowState` dictionary passed between executors
- Each executor enriches the state with its results
- Type-safe context management with `WorkflowContext[T]`

### 3. Event Streaming
- Real-time workflow events via `run_stream()`
- Monitor execution progress through event types:
  - `WorkflowStatusEvent` - State changes
  - `WorkflowOutputEvent` - Final results
  - `ExecutorFailedEvent` - Executor errors
  - `WorkflowFailedEvent` - Workflow errors

### 4. Modular Executors
Each step is encapsulated in its own executor:

- **DocumentIngestionExecutor** - Process and extract metadata
- **SummarizationExecutor** - Generate summaries and key clauses
- **ComplianceValidationExecutor** - Validate against regulations
- **RiskScoringExecutor** - Calculate risk scores
- **EmailNotificationExecutor** - Send notifications (terminal node)

## Usage

### Basic Example

```python
from agents.sequential_workflow_orchestrator import SequentialWorkflowOrchestrator

# Initialize orchestrator
orchestrator = SequentialWorkflowOrchestrator(
    use_azure=True,
    send_email=False
)

# Process document (async)
results = await orchestrator.process_grant_proposal_async("path/to/proposal.pdf")

# Or use sync wrapper
results = orchestrator.process_grant_proposal("path/to/proposal.pdf")

# Get summary
summary = orchestrator.get_workflow_summary(results)
print(summary)
```

### Advanced Usage with Event Streaming

```python
import asyncio
from agent_framework import (
    WorkflowStatusEvent,
    WorkflowOutputEvent,
    ExecutorFailedEvent,
    WorkflowRunState
)

async def process_with_monitoring(file_path: str):
    orchestrator = SequentialWorkflowOrchestrator(use_azure=True)
    workflow = orchestrator._build_workflow()
    
    # Stream events for real-time monitoring
    async for event in workflow.run_stream(file_path):
        if isinstance(event, WorkflowStatusEvent):
            if event.state == WorkflowRunState.IN_PROGRESS:
                print("⏳ Workflow in progress...")
            elif event.state == WorkflowRunState.IDLE:
                print("✓ Workflow completed")
        
        elif isinstance(event, WorkflowOutputEvent):
            print(f"📤 Output received: {event.data}")
            return event.data
        
        elif isinstance(event, ExecutorFailedEvent):
            print(f"❌ Executor {event.executor_id} failed!")
            raise Exception(event.details.message)

# Run
results = asyncio.run(process_with_monitoring("proposal.pdf"))
```

## Comparison with Original Orchestrator

| Feature | Original Orchestrator | Sequential Workflow Orchestrator |
|---------|----------------------|----------------------------------|
| Pattern | Manual async coordination | Agent Framework Sequential Workflow |
| Modularity | Methods in single class | Separate Executor classes |
| State Management | Manual dictionary passing | Typed WorkflowContext |
| Event Streaming | ❌ No | ✅ Yes |
| Error Handling | Try-catch blocks | Event-based error handling |
| Extensibility | Add methods to class | Add new Executors to pipeline |
| Execution Order | Hardcoded in method | Defined by edge connections |

## Configuration

### Environment Variables

Required:
- `AZURE_AI_FOUNDRY_PROJECT_ENDPOINT` - Microsoft Foundry project endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Model deployment name (e.g., "gpt-4o")
- `AZURE_SEARCH_ENDPOINT` - Azure AI Search endpoint
- `AZURE_SEARCH_INDEX_NAME` - Search index name

Optional:
- `USE_MANAGED_IDENTITY` - Use managed identity (default: "true")
- `AZURE_OPENAI_API_KEY` - API key (if not using managed identity)
- `AZURE_SEARCH_API_KEY` - Search API key (if not using managed identity)
- `AZURE_SEARCH_DOCUMENT_CONTENT_TRUNCATION_SIZE` - Document truncation size (default: 10000)

### Authentication

The orchestrator supports two authentication methods:

1. **Managed Identity** (Recommended for production)
   ```bash
   export USE_MANAGED_IDENTITY=true
   ```

2. **API Keys** (For development)
   ```bash
   export USE_MANAGED_IDENTITY=false
   export AZURE_OPENAI_API_KEY="your-key"
   export AZURE_SEARCH_API_KEY="your-key"
   ```

## Testing

Run the test suite:

```bash
# Set environment variables
export AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="your-endpoint"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
export AZURE_SEARCH_ENDPOINT="your-search-endpoint"
export AZURE_SEARCH_INDEX_NAME="grant-compliance-index"

# Run tests
python tests/test_sequential_workflow_orchestrator.py
```

## Workflow Results

The workflow returns a comprehensive result dictionary:

```python
{
    'status': 'completed',
    'file_path': 'path/to/document.pdf',
    'document_data': {...},          # Raw document data
    'metadata': {...},               # Document metadata
    'summary': {...},                # Generated summary
    'compliance_report': {...},      # Compliance analysis
    'risk_report': {...},            # Risk assessment
    'email_sent': False,             # Email notification status
    'overall_status': 'requires_review',
    'steps': {                       # Individual step results
        'ingestion': {...},
        'summarization': {...},
        'compliance': {...},
        'risk_scoring': {...},
        'notification': {...}
    }
}
```

## Benefits of Sequential Workflow Pattern

### 1. **Clear Separation of Concerns**
Each executor has a single responsibility, making the code easier to understand and maintain.

### 2. **Flexible Pipeline Configuration**
Add, remove, or reorder executors by modifying the edge connections in `_build_workflow()`.

### 3. **Enhanced Observability**
Event streaming provides real-time visibility into workflow execution.

### 4. **Better Error Handling**
Executor-level error events make it easy to identify and handle failures.

### 5. **Reusable Components**
Executors can be reused in different workflow configurations.

### 6. **Scalable Architecture**
Easy to extend with new executors or create parallel execution paths.

## Future Enhancements

Possible improvements using Agent Framework capabilities:

1. **Parallel Execution** - Process independent steps concurrently
2. **Conditional Routing** - Dynamic paths based on intermediate results
3. **Custom Executors** - Add specialized processing steps
4. **Workflow Composition** - Nest workflows within executors
5. **Human-in-the-Loop** - Add approval/review steps

## References

- [Agent Framework Sequential Workflows](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/sequential?pivots=programming-language-python)
- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Workflow Builder API](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/)

## License

Same as parent project.
