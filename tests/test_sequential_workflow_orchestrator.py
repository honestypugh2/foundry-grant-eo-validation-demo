"""
Test Sequential Workflow Orchestrator
Demonstrates usage of the Agent Framework-based sequential workflow orchestrator.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.sequential_workflow_orchestrator import SequentialWorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_sequential_workflow():
    """
    Test the sequential workflow orchestrator with a sample document.
    """
    # Path to test document
    test_doc = Path(__file__).parent / "Green_Infrastructure_Resilience_Project_2024.pdf" #"test_document.txt"
    
    if not test_doc.exists():
        logger.error(f"Test document not found: {test_doc}")
        return
    
    logger.info("=" * 60)
    logger.info("Testing Sequential Workflow Orchestrator")
    logger.info("=" * 60)
    
    # Initialize orchestrator
    orchestrator = SequentialWorkflowOrchestrator(
        use_azure=True,
        send_email=False  # Set to True to test email notification
    )
    
    try:
        # Process document through workflow
        logger.info(f"\nProcessing document: {test_doc}")
        results = await orchestrator.process_grant_proposal_async(str(test_doc))
        
        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW RESULTS")
        logger.info("=" * 60)
        
        summary = orchestrator.get_workflow_summary(results)
        print(summary)
        
        # Display detailed results
        logger.info("\n" + "=" * 60)
        logger.info("DETAILED RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"\nStatus: {results['status']}")
        logger.info(f"Overall Status: {results['overall_status']}")
        
        logger.info("\n--- Steps Completed ---")
        for step_name, step_data in results['steps'].items():
            logger.info(f"{step_name}: {step_data['status']}")
        
        logger.info("\n--- Key Clauses ---")
        key_clauses = results['summary'].get('key_clauses', [])
        for i, clause in enumerate(key_clauses[:5], 1):  # Show first 5
            logger.info(f"{i}. {clause}")
        
        logger.info("\n--- Compliance Analysis ---")
        logger.info(f"Compliance Score: {results['compliance_report']['compliance_score']:.1f}%")
        logger.info(f"Status: {results['compliance_report']['overall_status']}")
        
        relevant_eos = results['compliance_report'].get('relevant_executive_orders', [])
        if relevant_eos:
            logger.info("\n--- Relevant Executive Orders ---")
            for eo in relevant_eos[:3]:  # Show first 3
                logger.info(f"- {eo}")
        
        logger.info("\n--- Risk Assessment ---")
        logger.info(f"Risk Score: {results['risk_report']['overall_score']:.1f}%")
        logger.info(f"Risk Level: {results['risk_report']['risk_level']}")
        logger.info(f"Requires Notification: {results['risk_report']['requires_notification']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Test completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_sequential_workflow_sync():
    """
    Test the sequential workflow orchestrator using synchronous wrapper.
    """
    test_doc = Path(__file__).parent / "test_document.txt"
    
    if not test_doc.exists():
        logger.error(f"Test document not found: {test_doc}")
        return
    
    logger.info("=" * 60)
    logger.info("Testing Sequential Workflow Orchestrator (Sync)")
    logger.info("=" * 60)
    
    # Initialize orchestrator
    orchestrator = SequentialWorkflowOrchestrator(
        use_azure=True,
        send_email=False
    )
    
    try:
        # Process document through workflow (sync wrapper)
        logger.info(f"\nProcessing document: {test_doc}")
        results = orchestrator.process_grant_proposal(str(test_doc))
        
        # Display summary
        summary = orchestrator.get_workflow_summary(results)
        print(summary)
        
        logger.info("✓ Sync test completed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Sync test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check environment variables
    required_vars = [
        "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        sys.exit(1)
    
    # Run async test
    print("\n" + "=" * 60)
    print("Running Async Test")
    print("=" * 60 + "\n")
    asyncio.run(test_sequential_workflow())
    
    # Run sync test
    print("\n\n" + "=" * 60)
    print("Running Sync Test")
    print("=" * 60 + "\n")
    test_sequential_workflow_sync()
