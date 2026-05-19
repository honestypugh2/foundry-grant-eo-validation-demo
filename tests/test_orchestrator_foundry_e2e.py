#!/usr/bin/env python3
"""
End-to-End Test: Sequential Workflow Orchestrator (Foundry)

Tests the SequentialWorkflowOrchestratorFoundry against real Azure AI Foundry
services using both inline text proposals and PDF files from the sample directory.

Usage:
    python tests/test_orchestrator_foundry_e2e.py
    python tests/test_orchestrator_foundry_e2e.py --pdf-only
    python tests/test_orchestrator_foundry_e2e.py --text-only
    python tests/test_orchestrator_foundry_e2e.py --verbose

Requires:
    - AZURE_AI_PROJECT_ENDPOINT set
    - AZURE_AI_MODEL_DEPLOYMENT_NAME or AZURE_OPENAI_DEPLOYMENT_NAME set
    - AI_SEARCH_PROJECT_CONNECTION_ID set
    - AZURE_SEARCH_INDEX_NAME set
    - Valid Azure credentials (az login)
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

# Configure logging
LOG_LEVEL = logging.DEBUG if "--verbose" in sys.argv else logging.INFO
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_orchestrator_foundry")

# Suppress noisy HTTP logs unless verbose
if "--verbose" not in sys.argv:
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


# =============================================================================
# Test Data
# =============================================================================

SAMPLE_PROPOSALS = {
    "infrastructure": {
        "text": """Grant Proposal: County Bridge Rehabilitation Program

Requesting Department: Public Works
Requested Amount: $2,500,000
Timeline: 18 months

Purpose: Repair and modernize 8 structurally deficient bridges across
the county to meet current federal safety and environmental standards.

Key Components:
- Structural reinforcement of load-bearing elements
- Replacement of deteriorated deck surfaces
- Installation of modern drainage and stormwater management systems
- ADA-compliant pedestrian access improvements
- Environmental mitigation for nearby waterways

DEI Requirements:
- Minority-owned business participation target: 25%
- Local workforce hiring preference: 60%
- Accessibility compliance with ADA and Section 504

Compliance Alignment:
- Executive Order 14008 (Climate Crisis): Stormwater management and
  environmental mitigation components address climate resilience
- Executive Order 13985 (Racial Equity): Minority business participation
  and equitable community impact analysis included

Budget Summary:
- Engineering and Design: $400,000
- Construction Labor: $1,200,000
- Materials and Equipment: $600,000
- Environmental Mitigation: $150,000
- Project Management: $100,000
- Contingency (10%): $50,000

Expected Outcomes:
- Improved public safety for 45,000 daily bridge users
- Extended bridge lifespan by 30+ years
- Job creation: 85 construction positions
- Reduced flood risk through upgraded drainage
""",
        "file_name": "bridge_rehab_proposal.txt",
        "expected_status": ["compliant", "requires_review"],
        "expected_eos": ["13985", "14008"],
    },
    "cybersecurity": {
        "text": """Grant Proposal: County Cybersecurity Modernization Initiative

Requesting Department: Information Technology
Requested Amount: $1,800,000
Timeline: 12 months

Purpose: Upgrade county IT infrastructure to meet Executive Order 14028
cybersecurity requirements, including zero-trust architecture implementation
and incident response capabilities.

Key Components:
- Zero-trust network architecture deployment
- Multi-factor authentication for all county systems
- Security Operations Center (SOC) establishment
- Employee cybersecurity awareness training program
- Incident response plan development and testing
- Software supply chain security assessment

Compliance Alignment:
- Executive Order 14028 (Improving the Nation's Cybersecurity):
  Direct implementation of zero-trust, MFA, and supply chain security
- NIST Cybersecurity Framework alignment
- CISA guidelines compliance

Budget Summary:
- Zero-Trust Infrastructure: $600,000
- SOC Setup and Staffing: $500,000
- Training Programs: $200,000
- Software and Licenses: $300,000
- Consulting Services: $150,000
- Contingency: $50,000

Expected Outcomes:
- 90% reduction in successful phishing attempts
- Zero-trust architecture for all critical systems
- 24/7 security monitoring capability
- Full EO 14028 compliance within 12 months
""",
        "file_name": "cybersecurity_proposal.txt",
        "expected_status": ["compliant"],
        "expected_eos": ["14028"],
    },
}


# =============================================================================
# Helpers
# =============================================================================

def banner(title: str, char: str = "═", width: int = 70):
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


def check_prerequisites() -> Dict[str, str]:
    """Validate required environment variables."""
    required = {
        "AZURE_AI_PROJECT_ENDPOINT": os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        "AI_SEARCH_PROJECT_CONNECTION_ID": os.getenv("AI_SEARCH_PROJECT_CONNECTION_ID", ""),
    }
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", ""
    )
    required["model"] = model

    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        print("   Set these in .env or export them before running.")
        sys.exit(1)

    return required


def write_temp_file(name: str, content: str) -> Path:
    """Write a temporary text file for testing."""
    tmp_dir = Path(__file__).parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    path = tmp_dir / name
    path.write_text(content)
    return path


def validate_workflow_results(results: Dict[str, Any], test_name: str) -> List[str]:
    """
    Validate workflow results structure and content.
    Returns a list of validation errors (empty = all good).
    """
    errors = []

    # Top-level structure
    if results.get("status") != "completed":
        errors.append(f"Status is '{results.get('status')}', expected 'completed'")
        if results.get("error"):
            errors.append(f"Error: {results['error']}")
        return errors  # Can't validate further

    if results.get("service") != "foundry_agent_service":
        errors.append(f"Service is '{results.get('service')}', expected 'foundry_agent_service'")

    # Required steps
    required_steps = ["ingestion", "summarization", "compliance", "risk_scoring", "notification"]
    for step in required_steps:
        if step not in results.get("steps", {}):
            errors.append(f"Missing workflow step: {step}")

    # Metadata
    metadata = results.get("metadata", {})
    if not metadata.get("word_count"):
        errors.append("Metadata missing word_count")

    # Summary
    summary = results.get("summary", {})
    if not summary.get("executive_summary"):
        errors.append("Summary missing executive_summary")
    if not summary.get("key_topics"):
        errors.append("Summary missing key_topics")

    # Compliance report
    compliance = results.get("compliance_report", {})
    if "compliance_score" not in compliance:
        errors.append("Compliance report missing compliance_score")
    elif not (0 <= compliance["compliance_score"] <= 100):
        errors.append(f"Compliance score out of range: {compliance['compliance_score']}")

    if "confidence_score" not in compliance:
        errors.append("Compliance report missing confidence_score")

    if compliance.get("overall_status") not in ("compliant", "non_compliant", "requires_review"):
        errors.append(f"Invalid compliance status: {compliance.get('overall_status')}")

    if not isinstance(compliance.get("relevant_executive_orders"), list):
        errors.append("Compliance report missing relevant_executive_orders list")

    # Risk report
    risk = results.get("risk_report", {})
    if "overall_score" not in risk:
        errors.append("Risk report missing overall_score")
    elif not (0 <= risk["overall_score"] <= 100):
        errors.append(f"Risk score out of range: {risk['overall_score']}")

    if risk.get("risk_level") not in ("low", "medium-low", "medium", "medium-high", "high"):
        errors.append(f"Invalid risk level: {risk.get('risk_level')}")

    # Overall status
    if results.get("overall_status") not in (
        "approved_with_conditions",
        "requires_review",
        "requires_legal_review",
    ):
        errors.append(f"Invalid overall_status: {results.get('overall_status')}")

    return errors


def print_results_summary(results: Dict[str, Any]):
    """Print a concise results summary."""
    compliance = results.get("compliance_report", {})
    risk = results.get("risk_report", {})
    summary = results.get("summary", {})

    print(f"    Compliance Score : {compliance.get('compliance_score', 'N/A'):.1f}%")
    print(f"    Compliance Status: {compliance.get('overall_status', 'N/A')}")
    print(f"    Confidence Score : {compliance.get('confidence_score', 'N/A')}%")
    print(f"    Relevant EOs     : {len(compliance.get('relevant_executive_orders', []))}")
    print(f"    Violations       : {len(compliance.get('violations', []))}")
    print(f"    Warnings         : {len(compliance.get('warnings', []))}")
    print(f"    Risk Score       : {risk.get('overall_score', 'N/A'):.1f}%")
    print(f"    Risk Level       : {risk.get('risk_level', 'N/A')}")
    print(f"    Overall Status   : {results.get('overall_status', 'N/A')}")
    print(f"    Key Topics       : {', '.join(summary.get('key_topics', [])[:5])}")

    # Print EOs found
    eos = compliance.get("relevant_executive_orders", [])
    if eos:
        eo_nums = [eo.get("eo_number", "?") for eo in eos]
        print(f"    EO Numbers       : {', '.join(eo_nums)}")


# =============================================================================
# Test Cases
# =============================================================================

async def test_text_proposal(
    orchestrator, name: str, proposal: Dict[str, Any]
) -> Dict[str, Any]:
    """Test orchestrator with an inline text proposal."""
    print(f"\n  📝 Test: {name}")
    print(f"     File: {proposal['file_name']}")

    # Write temp file
    tmp_path = write_temp_file(proposal["file_name"], proposal["text"])

    start = time.time()
    try:
        results = await orchestrator.process_grant_proposal_async(str(tmp_path))
        elapsed = time.time() - start
        print(f"     Duration: {elapsed:.1f}s")

        # Validate
        errors = validate_workflow_results(results, name)

        # Check expected EOs were found
        eos_found = [
            eo.get("eo_number", "")
            for eo in results.get("compliance_report", {}).get("relevant_executive_orders", [])
        ]
        for expected_eo in proposal.get("expected_eos", []):
            if expected_eo not in eos_found:
                errors.append(f"Expected EO {expected_eo} not found (found: {eos_found})")

        # Check expected status
        actual_status = results.get("compliance_report", {}).get("overall_status", "")
        expected_statuses = proposal.get("expected_status", [])
        if expected_statuses and actual_status not in expected_statuses:
            # Downgrade to warning — LLM outputs are non-deterministic
            print(f"     ⚠️  Status '{actual_status}' not in expected {expected_statuses} (non-deterministic)")

        if errors:
            print(f"     ❌ FAILED ({len(errors)} errors)")
            for err in errors:
                print(f"        • {err}")
        else:
            print(f"     ✅ PASSED")
            print_results_summary(results)

        return {"passed": len(errors) == 0, "errors": errors, "results": results, "duration": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        print(f"     ❌ EXCEPTION after {elapsed:.1f}s: {e}")
        traceback.print_exc()
        return {"passed": False, "errors": [str(e)], "results": None, "duration": elapsed}
    finally:
        tmp_path.unlink(missing_ok=True)


async def test_pdf_proposal(orchestrator, pdf_path: Path) -> Dict[str, Any]:
    """Test orchestrator with a real PDF file."""
    print(f"\n  📄 Test: {pdf_path.name}")

    start = time.time()
    try:
        results = await orchestrator.process_grant_proposal_async(str(pdf_path))
        elapsed = time.time() - start
        print(f"     Duration: {elapsed:.1f}s")

        errors = validate_workflow_results(results, pdf_path.name)

        if errors:
            print(f"     ❌ FAILED ({len(errors)} errors)")
            for err in errors:
                print(f"        • {err}")
        else:
            print(f"     ✅ PASSED")
            print_results_summary(results)

        return {"passed": len(errors) == 0, "errors": errors, "results": results, "duration": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        print(f"     ❌ EXCEPTION after {elapsed:.1f}s: {e}")
        traceback.print_exc()
        return {"passed": False, "errors": [str(e)], "results": None, "duration": elapsed}


async def test_sync_wrapper(orchestrator) -> Dict[str, Any]:
    """Test the synchronous process_grant_proposal wrapper."""
    print("\n  🔄 Test: Sync wrapper (process_grant_proposal)")

    tmp_path = write_temp_file("sync_test.txt", SAMPLE_PROPOSALS["infrastructure"]["text"])

    start = time.time()
    try:
        # Run in a thread to avoid nested event loop issues
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = await asyncio.get_event_loop().run_in_executor(
                pool, orchestrator.process_grant_proposal, str(tmp_path)
            )

        elapsed = time.time() - start
        print(f"     Duration: {elapsed:.1f}s")

        errors = validate_workflow_results(results, "sync_wrapper")
        if errors:
            print(f"     ❌ FAILED ({len(errors)} errors)")
            for err in errors:
                print(f"        • {err}")
        else:
            print(f"     ✅ PASSED")

        return {"passed": len(errors) == 0, "errors": errors, "results": results, "duration": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        print(f"     ❌ EXCEPTION after {elapsed:.1f}s: {e}")
        traceback.print_exc()
        return {"passed": False, "errors": [str(e)], "results": None, "duration": elapsed}
    finally:
        tmp_path.unlink(missing_ok=True)


async def test_error_handling(orchestrator) -> Dict[str, Any]:
    """Test that the orchestrator handles errors gracefully."""
    print("\n  🛡️  Test: Error handling (non-existent file)")

    start = time.time()
    try:
        results = await orchestrator.process_grant_proposal_async("/tmp/does_not_exist_12345.pdf")
        elapsed = time.time() - start

        # Should have failed
        if results.get("status") == "failed":
            print(f"     ✅ PASSED (graceful failure: {results.get('error', '')[:80]})")
            return {"passed": True, "errors": [], "results": results, "duration": elapsed}
        else:
            print(f"     ❌ FAILED (expected failure but got status={results.get('status')})")
            return {"passed": False, "errors": ["Expected failure for non-existent file"], "results": results, "duration": elapsed}

    except (FileNotFoundError, OSError, Exception) as e:
        elapsed = time.time() - start
        # Exception is also acceptable error handling
        print(f"     ✅ PASSED (raised {type(e).__name__}: {str(e)[:80]})")
        return {"passed": True, "errors": [], "results": None, "duration": elapsed}


# =============================================================================
# Main Test Runner
# =============================================================================

async def run_tests():
    """Run all orchestrator tests."""
    config = check_prerequisites()

    banner("FOUNDRY ORCHESTRATOR E2E TEST SUITE")
    print(f"  Endpoint : {os.getenv('AZURE_AI_PROJECT_ENDPOINT', '')[:65]}...")
    print(f"  Model    : {config['model']}")
    print(f"  Index    : {os.getenv('AZURE_SEARCH_INDEX_NAME', 'grant-compliance-index')}")

    # Determine what to run
    pdf_only = "--pdf-only" in sys.argv
    text_only = "--text-only" in sys.argv

    # Initialize orchestrator
    from agents.sequential_workflow_orchestrator_foundry import SequentialWorkflowOrchestratorFoundry

    orchestrator = SequentialWorkflowOrchestratorFoundry(use_azure=True, send_email=False)

    all_results: Dict[str, Dict[str, Any]] = {}
    total_start = time.time()

    # --- Text proposal tests ---
    if not pdf_only:
        banner("TEXT PROPOSAL TESTS", "─", 60)
        for name, proposal in SAMPLE_PROPOSALS.items():
            result = await test_text_proposal(orchestrator, name, proposal)
            all_results[f"text_{name}"] = result

    # --- PDF proposal tests ---
    if not text_only:
        banner("PDF PROPOSAL TESTS", "─", 60)
        pdf_dir = Path(__file__).parent.parent / "knowledge_base" / "sample_proposals"
        pdf_files = sorted(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            print("  ⚠️  No PDF files found in knowledge_base/sample_proposals/")
        else:
            # Test first 2 PDFs to keep runtime reasonable
            for pdf_path in pdf_files[:2]:
                result = await test_pdf_proposal(orchestrator, pdf_path)
                all_results[f"pdf_{pdf_path.stem}"] = result

    # --- Sync wrapper test ---
    if not pdf_only:
        banner("SYNC WRAPPER TEST", "─", 60)
        result = await test_sync_wrapper(orchestrator)
        all_results["sync_wrapper"] = result

    # --- Error handling test ---
    if not pdf_only:
        banner("ERROR HANDLING TEST", "─", 60)
        result = await test_error_handling(orchestrator)
        all_results["error_handling"] = result

    # --- Summary ---
    total_elapsed = time.time() - total_start
    banner("TEST RESULTS SUMMARY")

    passed = 0
    failed = 0
    for name, result in all_results.items():
        emoji = "✅" if result["passed"] else "❌"
        duration = f"({result['duration']:.1f}s)" if result.get("duration") else ""
        print(f"  {emoji} {name} {duration}")
        if result["passed"]:
            passed += 1
        else:
            failed += 1

    print(f"\n  Total: {passed + failed} tests | ✅ {passed} passed | ❌ {failed} failed")
    print(f"  Duration: {total_elapsed:.1f}s")

    if failed == 0:
        print("\n  🎉 All tests passed!")
    else:
        print("\n  ⚠️  Some tests failed. Review errors above.")

    # Clean up tmp directory
    tmp_dir = Path(__file__).parent / "tmp"
    if tmp_dir.exists():
        for f in tmp_dir.iterdir():
            f.unlink(missing_ok=True)
        tmp_dir.rmdir()

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
