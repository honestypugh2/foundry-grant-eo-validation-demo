# Evaluation Methodology for Grant Compliance Automation System

> **Comprehensive evaluation framework for measuring quality, safety, and performance of AI agents**  
> **Based on**: [Azure AI Foundry Observability Best Practices](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/observability?view=foundry-classic)

**Last Updated**: December 11, 2025  
**Document Version**: 1.0

---

## Table of Contents

- [Overview](#overview)
- [Evaluation Strategy](#evaluation-strategy)
- [Agent-Level Evaluation](#agent-level-evaluation)
- [System-Level Evaluation](#system-level-evaluation)
- [Evaluation Metrics](#evaluation-metrics)
- [Implementation Guide](#implementation-guide)
- [Continuous Monitoring](#continuous-monitoring)
- [Tools and Resources](#tools-and-resources)

---

## Overview

### Purpose

This document defines comprehensive evaluation methodologies for the Grant Proposal Compliance Automation system, ensuring:

- **Quality**: AI outputs meet accuracy and relevance standards
- **Safety**: No harmful, biased, or inappropriate content
- **Reliability**: Consistent performance across diverse grant proposals
- **Legal Compliance**: Attorney-validated outputs align with executive orders
- **Human Trust**: Legal professionals can confidently use AI-generated analyses

### Evaluation Philosophy

The system follows Azure AI Foundry's **three-stage evaluation lifecycle**:

1. **Base Model Selection**: Evaluate GPT-4 vs. GPT-4o for compliance analysis tasks
2. **Preproduction Evaluation**: Test agents with evaluation datasets before deployment
3. **Post-Production Monitoring**: Continuous quality and safety monitoring in production

### Key Principles

- **Human-in-the-Loop**: All AI outputs require attorney validation
- **Conservative Bias**: Over-flag ambiguous cases for human review
- **Traceability**: Every compliance finding must cite specific sources
- **Measurable Quality**: Quantitative metrics for continuous improvement
- **Safety First**: Zero tolerance for harmful, biased, or fabricated content

---

## Evaluation Strategy

### GenAIOps Lifecycle Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION LIFECYCLE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. MODEL SELECTION                                         │
│     ├── Compare GPT-4 vs GPT-4o                            │
│     ├── Evaluate accuracy, cost, latency                   │
│     └── Select optimal model for compliance analysis       │
│                                                             │
│  2. PREPRODUCTION EVALUATION                                │
│     ├── Agent-level testing (unit tests)                   │
│     ├── Integration testing (workflow tests)               │
│     ├── Adversarial testing (edge cases)                   │
│     └── Human evaluation (attorney review)                 │
│                                                             │
│  3. POST-PRODUCTION MONITORING                              │
│     ├── Continuous evaluation (sampled traffic)            │
│     ├── Scheduled evaluation (test datasets)               │
│     ├── Azure Monitor alerts (quality thresholds)          │
│     └── Attorney feedback loop (correction data)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Evaluation Dimensions

| Dimension | Description | Critical For |
|-----------|-------------|--------------|
| **Accuracy** | Correct identification of compliance issues | All agents |
| **Groundedness** | Responses cite actual executive order text | ComplianceAgent |
| **Relevance** | Analysis addresses grant proposal specifics | ComplianceAgent, SummarizationAgent |
| **Completeness** | All required sections/concerns identified | DocumentIngestionAgent, RiskScoringAgent |
| **Coherence** | Logical flow and consistency | SummarizationAgent |
| **Safety** | No harmful, biased, or inappropriate content | All agents |
| **Latency** | Response time for attorney workflows | All agents |
| **Cost Efficiency** | Token usage optimization | All agents |

---

## Agent-Level Evaluation

Each agent in the system requires tailored evaluation metrics and test datasets.

---

### 1. Document Ingestion Agent

**Purpose**: Extract text, metadata, and structure from PDF/DOCX grant proposals

#### Evaluation Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Text Extraction Accuracy** | >95% | Compare extracted text to ground truth OCR |
| **Metadata Completeness** | 100% | Verify all required fields populated |
| **Table Extraction** | >90% | Validate budget tables, staffing plans |
| **Processing Speed** | <30s per document | Measure end-to-end processing time |
| **Error Rate** | <2% | Track failed document ingestions |

#### Test Dataset

```python
# tests/evaluation_datasets/document_ingestion_tests.json
[
    {
        "test_id": "doc_001",
        "file_path": "tests/data/text_pdf_proposal.pdf",
        "expected": {
            "word_count": 5432,
            "page_count": 12,
            "has_budget_table": true,
            "metadata_fields": ["title", "organization", "amount"]
        }
    },
    {
        "test_id": "doc_002",
        "file_path": "tests/data/scanned_pdf_proposal.pdf",
        "expected": {
            "ocr_required": true,
            "text_quality": "high",
            "min_word_count": 4000
        }
    },
    {
        "test_id": "doc_003",
        "file_path": "tests/data/complex_tables_proposal.pdf",
        "expected": {
            "tables_extracted": 3,
            "budget_line_items": 15
        }
    }
]
```

#### Azure AI Foundry Evaluators

```python
from azure.ai.evaluation import (
    DocumentCompleteness,  # Custom evaluator
    ProcessingLatency
)

# Evaluate document extraction quality
document_evaluator = DocumentCompleteness(
    required_fields=["title", "organization", "budget", "timeline"],
    min_word_count=1000,
    table_extraction_required=True
)

results = document_evaluator.evaluate(
    extracted_data=ingestion_results,
    ground_truth=expected_data
)
```

#### Success Criteria

- ✅ All PDFs extract text without errors
- ✅ Metadata extraction rate: 100%
- ✅ OCR accuracy: >95% for scanned documents
- ✅ Table extraction: >90% accuracy
- ✅ Processing time: <30 seconds per document

---

### 2. Summarization Agent

**Purpose**: Generate executive summaries highlighting compliance-relevant content

#### Evaluation Metrics

| Metric | Target | Azure Evaluator |
|--------|--------|-----------------|
| **Coherence** | >0.8 | `CoherenceEvaluator()` |
| **Fluency** | >0.85 | `FluencyEvaluator()` |
| **Relevance** | >0.8 | `RelevanceEvaluator()` |
| **Similarity to Ground Truth** | >0.7 | `SimilarityEvaluator()` |
| **Summary Length** | 200-500 words | Custom validation |
| **Key Clause Extraction** | >90% recall | Custom evaluator |

#### Test Dataset

```python
# tests/evaluation_datasets/summarization_tests.json
[
    {
        "test_id": "sum_001",
        "proposal_text": "...",
        "ground_truth_summary": "Grant proposes $500K for affordable housing...",
        "expected_key_clauses": [
            "compliance with EO 14008 climate requirements",
            "budget allocation: $500,000",
            "timeline: 24 months"
        ],
        "expected_length_range": [200, 500]
    }
]
```

#### Azure AI Foundry Evaluators

```python
from azure.ai.evaluation import (
    CoherenceEvaluator,
    FluencyEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator
)

# Evaluate summary quality
coherence = CoherenceEvaluator()
fluency = FluencyEvaluator()
relevance = RelevanceEvaluator()
similarity = SimilarityEvaluator()

# Run evaluation
evaluation_results = {
    "coherence": coherence.evaluate(
        query=proposal_text,
        response=summary
    ),
    "fluency": fluency.evaluate(
        response=summary
    ),
    "relevance": relevance.evaluate(
        query=proposal_text,
        response=summary
    ),
    "similarity": similarity.evaluate(
        response=summary,
        ground_truth=expected_summary
    )
}
```

#### Success Criteria

- ✅ Coherence score: >0.8
- ✅ Fluency score: >0.85
- ✅ Summary captures all key sections
- ✅ No hallucinated information
- ✅ Appropriate length (200-500 words)

---

### 3. Compliance Agent

**Purpose**: Analyze grant proposals against executive order knowledge base

#### Evaluation Metrics (RAG-Specific)

| Metric | Target | Azure Evaluator |
|--------|--------|-----------------|
| **Groundedness** | >0.9 | `GroundednessEvaluator()` |
| **Retrieval Accuracy** | >0.85 | `RetrievalEvaluator()` |
| **Relevance** | >0.8 | `RelevanceEvaluator()` |
| **Citation Accuracy** | 100% | Custom validator |
| **F1 Score (vs. Attorney)** | >0.7 | `F1ScoreEvaluator()` |
| **Intent Resolution** | >0.85 | `IntentResolutionEvaluator()` |

#### Test Dataset

```python
# tests/evaluation_datasets/compliance_tests.json
[
    {
        "test_id": "comp_001",
        "proposal_snippet": "This grant will advance DEI initiatives...",
        "expected_eo_matches": ["EO_13985"],
        "expected_compliance_status": "Requires Review",
        "expected_concerns": [
            "DEI language may conflict with EO_14173"
        ],
        "expected_citations": [
            {
                "eo": "EO_13985",
                "section": "Section 2",
                "quote": "advancing racial equity..."
            }
        ],
        "ground_truth_label": "Non-Compliant"
    },
    {
        "test_id": "comp_002",
        "proposal_snippet": "Climate resilience infrastructure...",
        "expected_eo_matches": ["EO_14008"],
        "expected_compliance_status": "Compliant",
        "ground_truth_label": "Compliant"
    }
]
```

#### Azure AI Foundry Evaluators

```python
from azure.ai.evaluation import (
    GroundednessEvaluator,
    GroundednessProEvaluator,  # Preview - enhanced accuracy
    RetrievalEvaluator,
    RelevanceEvaluator,
    F1ScoreEvaluator,
    IntentResolutionEvaluator  # Agent-specific
)

# Evaluate RAG performance
groundedness = GroundednessEvaluator()
retrieval = RetrievalEvaluator()
relevance = RelevanceEvaluator()
f1_score = F1ScoreEvaluator()
intent_resolution = IntentResolutionEvaluator()

# Run compliance evaluation
evaluation_results = {
    "groundedness": groundedness.evaluate(
        query=proposal_snippet,
        context=retrieved_eo_text,
        response=compliance_analysis
    ),
    "retrieval": retrieval.evaluate(
        query=proposal_snippet,
        context=retrieved_eo_text
    ),
    "relevance": relevance.evaluate(
        query=proposal_snippet,
        response=compliance_analysis
    ),
    "f1_score": f1_score.evaluate(
        response=compliance_analysis,
        ground_truth=attorney_analysis
    ),
    "intent_resolution": intent_resolution.evaluate(
        query=proposal_snippet,
        response=compliance_analysis
    )
}
```

#### Citation Validation

```python
# Custom evaluator for citation accuracy
def validate_citations(compliance_report: dict) -> dict:
    """
    Verify all citations reference actual executive order text.
    
    Returns:
        {
            "citation_accuracy": 0.95,  # % of valid citations
            "invalid_citations": [],     # List of fabricated/incorrect citations
            "missing_citations": []      # Expected citations not included
        }
    """
    valid_citations = 0
    invalid_citations = []
    
    for citation in compliance_report.get('citations', []):
        # Check if citation exists in knowledge base
        eo_text = search_knowledge_base(citation['eo'], citation['section'])
        
        if citation['quote'] in eo_text:
            valid_citations += 1
        else:
            invalid_citations.append(citation)
    
    total_citations = len(compliance_report.get('citations', []))
    accuracy = valid_citations / total_citations if total_citations > 0 else 0
    
    return {
        "citation_accuracy": accuracy,
        "invalid_citations": invalid_citations,
        "total_citations": total_citations,
        "valid_citations": valid_citations
    }
```

#### Success Criteria

- ✅ Groundedness score: >0.9 (no hallucinations)
- ✅ Retrieval accuracy: >0.85 (correct EOs retrieved)
- ✅ Citation accuracy: 100% (all citations verifiable)
- ✅ F1 score vs. attorney: >0.7 (high agreement)
- ✅ Intent resolution: >0.85 (addresses compliance question)

---

### 4. Risk Scoring Agent

**Purpose**: Calculate comprehensive risk scores (compliance, quality, completeness)

#### Evaluation Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Score Consistency** | >0.9 correlation | Compare repeat evaluations |
| **Attorney Agreement** | >0.75 | Cohen's Kappa with attorney scores |
| **Threshold Accuracy** | >85% | Correct risk level classification |
| **Explainability** | 100% | All scores have factor breakdown |
| **Calibration** | Well-calibrated | Brier score <0.2 |

#### Test Dataset

```python
# tests/evaluation_datasets/risk_scoring_tests.json
[
    {
        "test_id": "risk_001",
        "compliance_score": 45,
        "confidence_score": 50,
        "quality_score": 70,
        "completeness_score": 80,
        "expected_risk_score": 55.5,  # Formula-based calculation
        "expected_risk_level": "High Risk",
        "expected_recommendation": "Recommend rejection or major rework",
        "attorney_risk_score": 52  # Ground truth
    }
]
```

#### Evaluation Implementation

```python
from scipy.stats import pearsonr
from sklearn.metrics import cohen_kappa_score, brier_score_loss

def evaluate_risk_scoring(test_dataset: list) -> dict:
    """
    Evaluate risk scoring agent against ground truth attorney scores.
    """
    ai_scores = []
    attorney_scores = []
    ai_levels = []
    attorney_levels = []
    
    for test_case in test_dataset:
        # Run risk scoring agent
        result = risk_agent.calculate_risk_score(
            compliance_report=test_case['compliance_report'],
            summary=test_case['summary'],
            metadata=test_case['metadata']
        )
        
        ai_scores.append(result['risk_score'])
        attorney_scores.append(test_case['attorney_risk_score'])
        
        ai_levels.append(result['risk_level'])
        attorney_levels.append(test_case['attorney_risk_level'])
    
    # Calculate metrics
    correlation, _ = pearsonr(ai_scores, attorney_scores)
    kappa = cohen_kappa_score(ai_levels, attorney_levels)
    
    return {
        "score_correlation": correlation,  # >0.9 target
        "level_agreement": kappa,          # >0.75 target
        "mean_absolute_error": np.mean(np.abs(np.array(ai_scores) - np.array(attorney_scores)))
    }
```

#### Success Criteria

- ✅ Score correlation with attorneys: >0.9
- ✅ Risk level agreement (Kappa): >0.75
- ✅ Mean absolute error: <10 points
- ✅ All scores have documented factors
- ✅ Well-calibrated probabilities

---

### 5. Email Trigger Agent

**Purpose**: Generate attorney notification emails with appropriate urgency

#### Evaluation Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Email Template Accuracy** | 100% | Validate all placeholders filled |
| **Priority Classification** | >90% | Compare to attorney priority labels |
| **Tone Appropriateness** | >0.8 | Fluency + coherence evaluators |
| **Delivery Success Rate** | >99% | Monitor Azure Function logs |
| **Latency** | <10s | End-to-end email generation time |

#### Test Dataset

```python
# tests/evaluation_datasets/email_trigger_tests.json
[
    {
        "test_id": "email_001",
        "risk_score": 45,
        "confidence_score": 50,
        "expected_priority": "High",
        "expected_subject_contains": "URGENT",
        "expected_body_contains": [
            "requires immediate review",
            "compliance concerns identified"
        ]
    },
    {
        "test_id": "email_002",
        "risk_score": 85,
        "confidence_score": 90,
        "expected_priority": "Normal",
        "expected_subject_contains": "Review",
        "expected_body_contains": [
            "for your review",
            "generally compliant"
        ]
    }
]
```

#### Success Criteria

- ✅ All emails formatted correctly
- ✅ Priority classification: >90% accuracy
- ✅ No missing placeholders
- ✅ Delivery success: >99%
- ✅ Generation latency: <10 seconds

---

## System-Level Evaluation

### End-to-End Workflow Testing

**Purpose**: Evaluate complete orchestration from document upload to attorney notification

#### Integration Test Scenarios

| Test Scenario | Description | Success Criteria |
|---------------|-------------|------------------|
| **Happy Path** | Compliant proposal, clear citations | Complete workflow in <2 minutes |
| **Non-Compliant Proposal** | Multiple EO conflicts | Correctly flags all concerns |
| **Ambiguous Case** | Unclear compliance status | Low confidence score, triggers review |
| **Complex Document** | Large PDF, multiple sections | Accurate extraction and analysis |
| **Edge Case: Scanned PDF** | Low-quality OCR | Successful text extraction |
| **Performance Test** | 10 concurrent proposals | No errors, consistent latency |

#### Evaluation Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Workflow Success Rate** | >95% | % of proposals processed without errors |
| **End-to-End Latency** | <2 minutes | From upload to email notification |
| **Attorney Validation Rate** | >80% | % of AI analyses approved by attorneys |
| **False Positive Rate** | <15% | Incorrect non-compliance flags |
| **False Negative Rate** | <5% | Missed compliance issues (critical) |

#### Multi-Agent Evaluation

```python
from azure.ai.evaluation import evaluate

# Define system-level evaluation dataset
test_dataset = [
    {
        "file_path": "tests/data/compliant_proposal.pdf",
        "expected_compliance_status": "Compliant",
        "expected_risk_level": "Low Risk",
        "expected_workflow_time": 120,  # seconds
        "attorney_validation": True
    }
]

# Run end-to-end evaluation
results = evaluate(
    evaluation_name="grant-compliance-system-v1",
    data=test_dataset,
    target=orchestrator.process_grant_proposal,
    evaluators={
        "groundedness": GroundednessEvaluator(),
        "relevance": RelevanceEvaluator(),
        "coherence": CoherenceEvaluator(),
        "latency": LatencyEvaluator(),
        "custom_workflow": WorkflowSuccessEvaluator()
    }
)

# View results in Azure AI Foundry portal
print(results)
```

---

## Evaluation Metrics

### Azure AI Foundry Evaluator Mapping

| Category | Evaluator | Use Case in System |
|----------|-----------|-------------------|
| **General Purpose** | `CoherenceEvaluator()` | Summarization, email generation |
| **General Purpose** | `FluencyEvaluator()` | Summarization, compliance reports |
| **RAG** | `GroundednessEvaluator()` | Compliance citations, no hallucinations |
| **RAG** | `GroundednessProEvaluator()` | Enhanced compliance validation (preview) |
| **RAG** | `RetrievalEvaluator()` | Knowledge base search accuracy |
| **RAG** | `RelevanceEvaluator()` | Compliance analysis relevance |
| **Textual Similarity** | `SimilarityEvaluator()` | Summary vs. ground truth |
| **Textual Similarity** | `F1ScoreEvaluator()` | Compliance findings vs. attorney |
| **Agents** | `IntentResolutionEvaluator()` | Compliance question understanding |
| **Agents** | `TaskAdherenceEvaluator()` | Agent follows compliance workflow |
| **Safety** | `ContentSafetyEvaluator()` | No harmful/biased content |
| **Safety** | `ProtectedMaterialsEvaluator()` | No copyright violations |

### Custom Metrics

#### 1. Citation Accuracy

```python
def citation_accuracy_evaluator(compliance_report: dict) -> float:
    """
    Verify all citations reference actual executive order text.
    
    Returns:
        Accuracy score (0-1): Percentage of valid citations
    """
    valid_citations = 0
    total_citations = len(compliance_report.get('citations', []))
    
    for citation in compliance_report.get('citations', []):
        # Verify citation exists in knowledge base
        if verify_citation_in_knowledge_base(citation):
            valid_citations += 1
    
    return valid_citations / total_citations if total_citations > 0 else 0.0
```

#### 2. Attorney Agreement Score

```python
def attorney_agreement_evaluator(
    ai_compliance_status: str,
    ai_risk_score: int,
    attorney_compliance_status: str,
    attorney_risk_score: int
) -> dict:
    """
    Measure agreement between AI and attorney assessments.
    
    Returns:
        {
            "compliance_agreement": bool,
            "risk_score_difference": int,
            "overall_agreement": float
        }
    """
    compliance_match = ai_compliance_status == attorney_compliance_status
    risk_difference = abs(ai_risk_score - attorney_risk_score)
    
    # Calculate overall agreement (0-1 scale)
    overall = 1.0 if compliance_match and risk_difference <= 10 else 0.5
    
    return {
        "compliance_agreement": compliance_match,
        "risk_score_difference": risk_difference,
        "overall_agreement": overall
    }
```

#### 3. Workflow Success Rate

```python
def workflow_success_evaluator(workflow_result: dict) -> dict:
    """
    Evaluate end-to-end workflow completion and quality.
    
    Returns:
        {
            "success": bool,
            "steps_completed": int,
            "errors": list,
            "latency_seconds": float
        }
    """
    required_steps = [
        'document_ingestion',
        'summarization',
        'compliance_analysis',
        'risk_scoring',
        'email_notification'
    ]
    
    completed_steps = [
        step for step in required_steps
        if workflow_result['steps'].get(step, {}).get('status') == 'success'
    ]
    
    return {
        "success": len(completed_steps) == len(required_steps),
        "steps_completed": len(completed_steps),
        "total_steps": len(required_steps),
        "errors": workflow_result.get('errors', []),
        "latency_seconds": workflow_result.get('total_time', 0)
    }
```

---

## Implementation Guide

### Step 1: Create Evaluation Datasets

```bash
# Directory structure
tests/
├── evaluation_datasets/
│   ├── document_ingestion_tests.json
│   ├── summarization_tests.json
│   ├── compliance_tests.json
│   ├── risk_scoring_tests.json
│   ├── email_trigger_tests.json
│   └── end_to_end_tests.json
├── data/
│   ├── ground_truth/
│   │   ├── attorney_analyses/      # Expert-labeled compliance reports
│   │   ├── expected_summaries/     # Human-written summaries
│   │   └── test_proposals/         # Sample grant proposals
│   └── adversarial/
│       ├── edge_cases/             # Ambiguous proposals
│       └── jailbreak_attempts/     # Safety testing
```

### Step 2: Configure Azure AI Foundry Evaluation SDK

```python
# evaluation_config.py
import os
from azure.ai.evaluation import evaluate
from azure.identity import DefaultAzureCredential

# Azure AI Foundry configuration
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Initialize credential
credential = DefaultAzureCredential()

# Evaluator configuration
EVALUATOR_CONFIG = {
    "groundedness": {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "threshold": 0.9
    },
    "relevance": {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "threshold": 0.8
    },
    "coherence": {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "threshold": 0.8
    },
    "f1_score": {
        "threshold": 0.7
    }
}
```

### Step 3: Implement Agent Evaluation Scripts

```python
# tests/evaluate_compliance_agent.py
import json
from azure.ai.evaluation import (
    GroundednessEvaluator,
    RelevanceEvaluator,
    RetrievalEvaluator,
    F1ScoreEvaluator
)
from agents.compliance_agent import ComplianceAgent

def load_test_dataset(dataset_path: str) -> list:
    """Load evaluation test dataset."""
    with open(dataset_path, 'r') as f:
        return json.load(f)

def evaluate_compliance_agent():
    """
    Run comprehensive evaluation of ComplianceAgent.
    """
    # Load test data
    test_dataset = load_test_dataset('tests/evaluation_datasets/compliance_tests.json')
    
    # Initialize evaluators
    groundedness = GroundednessEvaluator()
    relevance = RelevanceEvaluator()
    retrieval = RetrievalEvaluator()
    f1_score = F1ScoreEvaluator()
    
    # Initialize agent
    agent = ComplianceAgent(...)
    
    results = []
    
    for test_case in test_dataset:
        # Run agent
        compliance_report = agent.analyze_compliance(
            document_text=test_case['proposal_snippet'],
            metadata={}
        )
        
        # Evaluate
        test_result = {
            "test_id": test_case['test_id'],
            "groundedness": groundedness.evaluate(
                query=test_case['proposal_snippet'],
                context=compliance_report['retrieved_context'],
                response=compliance_report['analysis']
            ),
            "relevance": relevance.evaluate(
                query=test_case['proposal_snippet'],
                response=compliance_report['analysis']
            ),
            "retrieval": retrieval.evaluate(
                query=test_case['proposal_snippet'],
                context=compliance_report['retrieved_context']
            ),
            "f1_score": f1_score.evaluate(
                response=compliance_report['compliance_status'],
                ground_truth=test_case['ground_truth_label']
            ),
            "citation_accuracy": validate_citations(compliance_report)
        }
        
        results.append(test_result)
    
    # Aggregate results
    avg_groundedness = sum(r['groundedness']['score'] for r in results) / len(results)
    avg_relevance = sum(r['relevance']['score'] for r in results) / len(results)
    avg_f1 = sum(r['f1_score']['score'] for r in results) / len(results)
    
    print(f"Average Groundedness: {avg_groundedness:.2f}")
    print(f"Average Relevance: {avg_relevance:.2f}")
    print(f"Average F1 Score: {avg_f1:.2f}")
    
    return results

if __name__ == "__main__":
    results = evaluate_compliance_agent()
```

### Step 4: Run Evaluation in Azure AI Foundry

```python
# run_azure_evaluation.py
from azure.ai.evaluation import evaluate
from agents.orchestrator import AgentOrchestrator

# Define target function
def process_proposal_for_evaluation(file_path: str) -> dict:
    """
    Wrapper function for evaluation.
    """
    orchestrator = AgentOrchestrator(use_azure=True)
    return orchestrator.process_grant_proposal(file_path)

# Load evaluation dataset
evaluation_data = load_test_dataset('tests/evaluation_datasets/end_to_end_tests.json')

# Run evaluation in Azure AI Foundry
evaluation_results = evaluate(
    evaluation_name="grant-compliance-full-system-v1.0",
    data=evaluation_data,
    target=process_proposal_for_evaluation,
    evaluators={
        "groundedness": GroundednessEvaluator(),
        "relevance": RelevanceEvaluator(),
        "coherence": CoherenceEvaluator(),
        "f1_score": F1ScoreEvaluator()
    },
    evaluator_config=EVALUATOR_CONFIG,
    azure_ai_project={
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "resource_group_name": os.getenv("AZURE_RESOURCE_GROUP"),
        "project_name": os.getenv("AZURE_AI_PROJECT_NAME")
    }
)

# View results in Azure AI Foundry portal
print(f"Evaluation completed. View results at: {evaluation_results['studio_url']}")
```

### Step 5: View Results in Azure AI Foundry Portal

```
Navigate to:
Azure AI Foundry Portal → Evaluations → grant-compliance-full-system-v1.0

View:
- Aggregate scores (groundedness, relevance, coherence, F1)
- Individual test case results
- Detailed error analysis
- Score distributions
- Comparison with previous evaluation runs
```

---

## Continuous Monitoring

### Post-Production Observability

#### 1. Continuous Evaluation (Sampled Traffic)

```python
# Enable continuous evaluation in Azure AI Foundry
from azure.ai.evaluation import ContinuousEvaluator

continuous_eval = ContinuousEvaluator(
    project_endpoint=AZURE_AI_PROJECT_ENDPOINT,
    evaluation_name="grant-compliance-production",
    sampling_rate=0.1,  # Evaluate 10% of production traffic
    evaluators=[
        GroundednessEvaluator(),
        RelevanceEvaluator(),
        ContentSafetyEvaluator()
    ],
    alert_thresholds={
        "groundedness": 0.9,
        "relevance": 0.8,
        "content_safety": 1.0
    }
)

# Monitor production traffic
continuous_eval.start()
```

#### 2. Scheduled Evaluation (Test Dataset)

```python
# Schedule daily evaluation runs with test dataset
from azure.ai.evaluation import ScheduledEvaluator

scheduled_eval = ScheduledEvaluator(
    project_endpoint=AZURE_AI_PROJECT_ENDPOINT,
    evaluation_name="grant-compliance-daily-check",
    schedule="0 2 * * *",  # 2 AM daily (cron format)
    test_dataset_path="tests/evaluation_datasets/end_to_end_tests.json",
    evaluators=[
        GroundednessEvaluator(),
        RelevanceEvaluator(),
        F1ScoreEvaluator()
    ],
    alert_on_regression=True,
    regression_threshold=0.05  # Alert if scores drop >5%
)

scheduled_eval.start()
```

#### 3. Azure Monitor Alerts

```python
# Configure Azure Monitor alerts for evaluation failures
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential

logs_client = LogsQueryClient(credential=DefaultAzureCredential())

# Query for evaluation failures
query = """
AppTraces
| where Message contains "Evaluation Failed" or Message contains "Low Groundedness"
| where TimeGenerated > ago(1h)
| summarize Count=count() by Message
| where Count > 5
"""

# Set up alert rule (via Azure Portal or ARM template)
alert_rule = {
    "name": "grant-compliance-low-quality",
    "condition": "groundedness_score < 0.9",
    "action": "email legal-team@example.com",
    "severity": "High"
}
```

#### 4. Attorney Feedback Loop

```python
# Capture attorney corrections for model improvement
def record_attorney_feedback(
    proposal_id: str,
    ai_analysis: dict,
    attorney_analysis: dict,
    attorney_comments: str
):
    """
    Record attorney corrections to AI analysis for continuous learning.
    """
    feedback_entry = {
        "proposal_id": proposal_id,
        "timestamp": datetime.now().isoformat(),
        "ai_compliance_status": ai_analysis['compliance_status'],
        "ai_risk_score": ai_analysis['risk_score'],
        "attorney_compliance_status": attorney_analysis['compliance_status'],
        "attorney_risk_score": attorney_analysis['risk_score'],
        "disagreements": identify_disagreements(ai_analysis, attorney_analysis),
        "attorney_comments": attorney_comments
    }
    
    # Store in Azure Blob Storage for analysis
    save_feedback_to_blob(feedback_entry)
    
    # Periodically retrain with corrected data
    if should_trigger_retraining():
        trigger_model_fine_tuning()
```

### Observability Dashboard

**Azure AI Foundry Observability Dashboard Metrics**:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **Groundedness Score** | % of responses grounded in knowledge base | <0.9 |
| **Relevance Score** | % of responses relevant to query | <0.8 |
| **Attorney Agreement** | % of AI analyses approved by attorneys | <80% |
| **Citation Accuracy** | % of valid citations | <100% |
| **Error Rate** | % of failed workflow executions | >2% |
| **Latency P95** | 95th percentile processing time | >150s |
| **Token Usage** | Daily OpenAI token consumption | >500K |

**Access Dashboard**:
```
Azure AI Foundry Portal → Monitoring → Observability Dashboard
Filter by: grant-compliance-production
Time range: Last 7 days
```

---

## Tools and Resources

### Azure AI Foundry Evaluation Tools

| Tool | Purpose | Documentation |
|------|---------|---------------|
| **Azure AI Evaluation SDK** | Programmatic evaluation | [SDK Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk) |
| **Foundry Evaluation Wizard** | No-code evaluation UI | [Wizard Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/evaluate-generative-ai-app) |
| **AI Red Teaming Agent** | Adversarial testing | [Red Team Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/run-scans-ai-red-teaming-agent) |
| **Simulators** | Generate test data | [Simulator Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/simulator-interaction-data) |
| **Observability Dashboard** | Production monitoring | [Observability Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/observability) |

### Evaluation Dataset Templates

**GitHub Repository**: [Azure AI Samples - Evaluation Datasets](https://github.com/Azure-Samples/azureai-samples/tree/main/scenarios/evaluate)

**Dataset Templates**:
- `rag_evaluation_dataset.json` - RAG system evaluation template
- `agent_evaluation_dataset.json` - Agent behavior testing
- `safety_evaluation_dataset.json` - Safety and bias testing

### Sample Notebooks

```bash
# Clone Azure AI Samples repository
git clone https://github.com/Azure-Samples/azureai-samples.git

# Relevant notebooks
azureai-samples/
├── scenarios/
│   └── evaluate/
│       ├── Evaluate_Base_Model_Endpoint.ipynb
│       ├── Evaluate_RAG_Application.ipynb
│       ├── Evaluate_Agent_Application.ipynb
│       ├── Custom_Evaluators.ipynb
│       └── Adversarial_Simulation.ipynb
```

### Running Tests

```bash
# Run agent-level evaluations
python tests/evaluate_document_ingestion_agent.py
python tests/evaluate_summarization_agent.py
python tests/evaluate_compliance_agent.py
python tests/evaluate_risk_scoring_agent.py
python tests/evaluate_email_trigger_agent.py

# Run system-level evaluation
python tests/evaluate_end_to_end_workflow.py

# Run full evaluation suite with Azure AI Foundry
python run_azure_evaluation.py

# Run adversarial testing (AI Red Teaming)
python tests/run_red_team_scan.py
```

---

## Evaluation Checklist

### Preproduction Evaluation

- [ ] Document Ingestion Agent: Text extraction accuracy >95%
- [ ] Summarization Agent: Coherence >0.8, Fluency >0.85
- [ ] Compliance Agent: Groundedness >0.9, Citation accuracy 100%
- [ ] Risk Scoring Agent: Attorney agreement >0.75
- [ ] Email Trigger Agent: Priority classification >90%
- [ ] End-to-End Workflow: Success rate >95%, latency <2 min
- [ ] Safety Evaluation: No harmful/biased content
- [ ] Adversarial Testing: AI Red Teaming scan passed
- [ ] Attorney Human Evaluation: 10+ proposals reviewed and validated

### Post-Production Monitoring

- [ ] Continuous evaluation enabled (10% sampling)
- [ ] Scheduled daily evaluation runs configured
- [ ] Azure Monitor alerts set up for quality thresholds
- [ ] Attorney feedback loop implemented
- [ ] Observability dashboard monitoring enabled
- [ ] Monthly evaluation reports generated
- [ ] Quarterly model performance review scheduled

---

## Appendix: Evaluation Best Practices

### 1. Test Dataset Quality

- **Diversity**: Include proposals from multiple domains (housing, education, infrastructure)
- **Difficulty**: Mix easy, medium, and hard cases
- **Edge Cases**: Include ambiguous compliance scenarios
- **Ground Truth**: Attorney-validated labels for all test cases
- **Size**: Minimum 50-100 test cases per agent

### 2. Evaluation Frequency

| Stage | Evaluation Type | Frequency |
|-------|----------------|-----------|
| Development | Agent-level unit tests | Every code change |
| Preproduction | Full system evaluation | Before each deployment |
| Production | Continuous evaluation | 10% of traffic, real-time |
| Production | Scheduled evaluation | Daily at 2 AM |
| Production | Human review | Weekly attorney validation |
| Production | Comprehensive audit | Quarterly |

### 3. Human-in-the-Loop Best Practices

- **Attorney Training**: Provide attorneys with evaluation guidelines
- **Feedback Forms**: Structured forms for attorney corrections
- **Disagreement Analysis**: Investigate AI-attorney disagreements
- **Iterative Improvement**: Use feedback to refine prompts and models

### 4. Safety and Bias Testing

```python
# Run content safety evaluation
from azure.ai.evaluation import ContentSafetyEvaluator

safety_evaluator = ContentSafetyEvaluator()

# Test for bias, hate speech, violence, self-harm
safety_results = safety_evaluator.evaluate(
    query=proposal_text,
    response=compliance_analysis
)

# Ensure zero tolerance for safety violations
assert safety_results['hate_unfairness'] == 0
assert safety_results['violence'] == 0
assert safety_results['sexual'] == 0
assert safety_results['self_harm'] == 0
```

---

## Conclusion

This evaluation methodology provides a comprehensive framework for ensuring the Grant Proposal Compliance Automation system delivers:

- ✅ **High-quality AI outputs** validated by quantitative metrics
- ✅ **Safe and unbiased content** through safety evaluations
- ✅ **Attorney trust** through human-in-the-loop validation
- ✅ **Continuous improvement** via production monitoring and feedback loops
- ✅ **Compliance with legal standards** through rigorous citation validation

**Next Steps**:
1. Implement agent-level evaluation scripts
2. Create evaluation datasets with attorney-validated ground truth
3. Configure Azure AI Foundry continuous evaluation
4. Set up Azure Monitor alerts for quality thresholds
5. Establish attorney feedback loop for continuous learning

---

**Document Maintainer**: Technical Architecture Team  
**Review Frequency**: Quarterly (after each major system update)  
**Related Documents**:
- [Architecture.md](Architecture.md) - System architecture overview
- [ScoringSystem.md](ScoringSystem.md) - Risk scoring methodology
- [CostEstimation.md](CostEstimation.md) - Azure service costs
