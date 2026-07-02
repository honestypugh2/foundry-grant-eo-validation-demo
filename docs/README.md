# Documentation Index

> Start here. This page tells you what to read and in what order.

---

## Reading Order

| # | If you want to... | Read this |
|---|-------------------|-----------|
| 1 | Understand the full system flow | [EndToEndWorkflow.md](EndToEndWorkflow.md) |
| 2 | See the technical architecture | [Architecture.md](Architecture.md) |
| 3 | Use the app as an end user | [UserGuide.md](UserGuide.md) |
| 4 | Understand the scoring outputs | [ScoringSystem.md](ScoringSystem.md) |
| 5 | Deploy to Azure | [Deployment.md](Deployment.md) |
| 6 | Estimate costs | [CostEstimation.md](CostEstimation.md) |

---

## All Documentation by Category

### Core (read these first)

| Document | Description |
|----------|-------------|
| [EndToEndWorkflow.md](EndToEndWorkflow.md) | Sequence diagrams and data flow for the full pipeline — upload to results |
| [Architecture.md](Architecture.md) | System architecture, component design, technology stack |
| [ScoringSystem.md](ScoringSystem.md) | How confidence, compliance, and risk scores are calculated |
| [UserGuide.md](UserGuide.md) | How to use the application (upload, interpret results, FAQs) |

### Deployment & Operations

| Document | Description |
|----------|-------------|
| [Deployment.md](Deployment.md) | Full deployment guide (azd, Bicep, manual) with TL;DR and checklist |
| [AzureFunctionsDurableDeployment.md](AzureFunctionsDurableDeployment.md) | Deploying as Azure Durable Functions (serverless hosting) |
| [ManagedIdentitySetup.md](ManagedIdentitySetup.md) | Zero-trust authentication setup (eliminate API keys) |
| [CostEstimation.md](CostEstimation.md) | Azure cost breakdown by scenario ($77–$2,707/month) |

### Document Processing

| Document | Description |
|----------|-------------|
| [DocumentIngestion.md](DocumentIngestion.md) | Adding, processing, and indexing documents (PDF guide + Azure Search indexing) |

### Orchestration Options

| Document | Description |
|----------|-------------|
| [SequentialWorkflowOrchestrator.md](SequentialWorkflowOrchestrator.md) | Agent Framework + Foundry Prompt agent orchestrators |
| [ComplianceWorkflowDiagram.md](ComplianceWorkflowDiagram.md) | Mermaid flowchart of the complete pipeline |

### Monitoring & Quality

| Document | Description |
|----------|-------------|
| [Observability.md](Observability.md) | OpenTelemetry tracing + Application Insights setup |
| [EvaluationMethodology.md](EvaluationMethodology.md) | GenAIOps evaluation framework, metrics, CI/CD integration |

### Enterprise / Optional

| Document | Description |
|----------|-------------|
| [sharepointIntegration.md](sharepointIntegration.md) | SharePoint document source with webhook auto-indexing (includes quick start) |

### Architecture Decisions (internal)

| Document | Description |
|----------|-------------|
| [decisions/PromptAgentRestructuring.md](decisions/PromptAgentRestructuring.md) | Analysis: consolidating into a single Prompt agent |
| [decisions/WorkflowAgentRestructuring.md](decisions/WorkflowAgentRestructuring.md) | Analysis: using Foundry Workflow agents (preview) |

---

## Key Concepts

| Concept | Where to learn more |
|---------|-------------------|
| The 5-step pipeline | [EndToEndWorkflow.md](EndToEndWorkflow.md) |
| Three scoring dimensions | [ScoringSystem.md](ScoringSystem.md) |
| Agent Framework vs Foundry agents | [SequentialWorkflowOrchestrator.md](SequentialWorkflowOrchestrator.md) |
| Human-in-the-loop design | [UserGuide.md](UserGuide.md), [Architecture.md](Architecture.md) |
| Azure Functions vs Foundry Hosted Agent | [AzureFunctionsDurableDeployment.md](AzureFunctionsDurableDeployment.md) |
| Knowledge base indexing | [DocumentIngestion.md](DocumentIngestion.md) |
