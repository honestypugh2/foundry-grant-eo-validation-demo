#!/usr/bin/env python3
"""
Run All Agent Tests

Master test runner that executes all individual agent tests.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_test(test_script: str) -> tuple:
    """Run a test script and return success status."""
    print(f"\n{'='*70}")
    print(f"Running: {test_script}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, test_script],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        
        success = result.returncode == 0
        return success, result.returncode
        
    except Exception as e:
        print(f"❌ Error running {test_script}: {str(e)}")
        return False, -1


def main():
    """Run all agent tests."""
    
    print("=" * 70)
    print("🧪 Grant Compliance System - Agent Test Suite")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # List of test scripts
    test_scripts = [
        ('test_document_ingestion_agent.py', 'Document Ingestion Agent'),
        ('test_summarization_agent.py', 'Summarization Agent'),
        ('test_compliance_validator_agent.py', 'Compliance Validator Agent'),
        ('test_risk_scoring_agent.py', 'Risk Scoring Agent'),
        ('test_email_notification.py', 'Email Trigger Agent'),
        ('test_orchestrator.py', 'Agent Orchestrator'),
    ]
    
    results = []
    
    # Run each test
    for script, name in test_scripts:
        script_path = Path(__file__).parent / script
        
        if not script_path.exists():
            print(f"\n⚠️  Test script not found: {script}")
            results.append((name, False, 'not found'))
            continue
        
        success, returncode = run_test(str(script_path))
        results.append((name, success, returncode))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"Tests Run: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}\n")
    
    # Detailed results
    print("Detailed Results:")
    print("-" * 70)
    for name, success, returncode in results:
        status = "✅ PASS" if success else "❌ FAIL"
        code = f"(exit code: {returncode})" if returncode != 0 else ""
        print(f"{status:12} {name:40} {code}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Review output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
