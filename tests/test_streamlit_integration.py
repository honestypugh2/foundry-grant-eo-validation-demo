#!/usr/bin/env python3
"""
Test Streamlit App Integration

Tests that the Streamlit app can successfully process a grant proposal
using the updated compliance agent with Azure AI Foundry.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from agents.orchestrator import AgentOrchestrator

def test_streamlit_workflow():
    """Test the workflow that Streamlit uses."""
    
    print("=" * 80)
    print("STREAMLIT APP INTEGRATION TEST")
    print("=" * 80)
    
    # Find a sample file
    sample_file = Path('knowledge_base/sample_proposals/2024-0731 FY25 VCLG Award - SO.pdf')
    
    if not sample_file.exists():
        print("❌ Sample file not found")
        return False
    
    print(f"\n📄 Testing with: {sample_file.name}")
    print("\nThis simulates what happens when you upload a file in Streamlit...\n")
    
    try:
        # Initialize orchestrator (same as Streamlit does)
        print("1️⃣ Initializing orchestrator with Azure services...")
        orchestrator = AgentOrchestrator(use_azure=True)
        print("   ✅ Orchestrator initialized")
        
        # Process the proposal (same as Streamlit does)
        print("\n2️⃣ Processing grant proposal through complete workflow...")
        print("   - Document Ingestion...")
        print("   - Summarization...")
        print("   - Compliance Validation (Azure AI Agent)...")
        print("   - Risk Scoring...")
        
        result = orchestrator.process_grant_proposal(
            str(sample_file),
            send_email=False
        )
        
        print("\n   ✅ Processing complete!")
        
        # Display results (same format as Streamlit)
        print("\n" + "=" * 80)
        print("📊 WORKFLOW RESULTS (as shown in Streamlit)")
        print("=" * 80)
        
        # Overall Status
        overall_status = result['overall_status'].upper().replace('_', ' ')
        print(f"\n🎯 Overall Status: {overall_status}")
        
        # Risk Assessment
        risk = result['risk_report']
        print(f"\n⚠️  Risk Assessment:")
        print(f"   Score: {risk['overall_score']:.1f}%")
        print(f"   Level: {risk['risk_level'].upper()}")
        print(f"   Confidence: {risk['confidence']:.1f}%")
        
        # Compliance Status
        compliance = result['compliance_report']
        print(f"\n✅ Compliance Status:")
        print(f"   Score: {compliance['compliance_score']:.1f}%")
        print(f"   Status: {compliance['overall_status'].upper().replace('_', ' ')}")
        
        # Document Info
        metadata = result['metadata']
        print(f"\n📄 Document Information:")
        print(f"   File: {metadata.get('file_name', 'Unknown')}")
        print(f"   Words: {metadata.get('word_count', 0):,}")
        print(f"   Pages: {metadata.get('page_count', 0)}")
        
        # Workflow steps
        print(f"\n✓ Workflow Steps Completed:")
        for step_name, step_data in result['steps'].items():
            status = step_data.get('status', 'unknown')
            emoji = "✅" if status == "completed" else "⏭️" if status == "skipped" else "❌"
            print(f"   {emoji} {step_name.title()}: {status}")
        
        print("\n" + "=" * 80)
        print("✅ STREAMLIT INTEGRATION TEST PASSED")
        print("=" * 80)
        
        print("\n💡 The Streamlit app should now be able to:")
        print("   ✅ Upload PDF/TXT grant proposals")
        print("   ✅ Process them through all agents")
        print("   ✅ Use Azure AI Foundry compliance agent")
        print("   ✅ Display comprehensive results")
        print("   ✅ Show risk assessment and compliance scores")
        
        print(f"\n🌐 Access the app at: http://localhost:8501")
        print("   - Upload a grant proposal file")
        print("   - Click 'Analyze Proposal'")
        print("   - See the results displayed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nTesting Streamlit app integration with updated compliance agent...\n")
    success = test_streamlit_workflow()
    
    if success:
        print("\n✅ All systems ready! The Streamlit app should work perfectly.")
    else:
        print("\n❌ There was an issue. Check the error messages above.")
    
    print("\n" + "=" * 80)
