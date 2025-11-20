#!/usr/bin/env python3
"""
Test SMTP Email Sending

This script tests the SMTP email fallback functionality.
It verifies that emails can be sent using Office 365 SMTP.

Prerequisites:
- Update SMTP_PASSWORD in .env with your Microsoft password
- Ensure SMTP_ENABLED=true in .env
- Run from project root: python test_smtp_email.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.email_trigger_agent import EmailTriggerAgent

def test_smtp_email():
    """Test SMTP email sending with mock high-risk proposal."""
    
    # Load environment
    load_dotenv()
    
    # Check SMTP configuration
    print("\n" + "="*60)
    print("SMTP EMAIL TEST")
    print("="*60)
    
    smtp_enabled = os.getenv('SMTP_ENABLED', 'false').lower() == 'true'
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print(f"\nSMTP Enabled: {smtp_enabled}")
    print(f"SMTP Username: {smtp_username}")
    print(f"SMTP Password: {'***' if smtp_password and smtp_password != 'your_microsoft_password_here' else 'NOT SET'}")
    
    if not smtp_enabled:
        print("\n❌ ERROR: SMTP_ENABLED is false in .env")
        print("Set SMTP_ENABLED=true to enable SMTP email sending")
        return False
    
    if not smtp_password or smtp_password == 'your_microsoft_password_here':
        print("\n❌ ERROR: SMTP_PASSWORD not set in .env")
        print("\nTo enable SMTP email sending:")
        print("1. Open .env file")
        print("2. Set SMTP_PASSWORD=your_microsoft_password")
        print("3. Save the file and run this test again")
        print("\nNote: For Microsoft accounts with 2FA, you may need an app password:")
        print("https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944")
        return False
    
    print("\n" + "-"*60)
    print("Initializing Email Agent (SMTP mode)")
    print("-"*60)
    
    # Initialize agent with SMTP only (no Graph API)
    agent = EmailTriggerAgent(use_graph_api=False)
    
    # Create mock high-risk proposal data
    print("\nCreating mock high-risk proposal...")
    
    mock_risk_report = {
        'overall_score': 78.5,
        'risk_level': 'high',
        'confidence': 92.3,
        'risk_factors': [
            {
                'category': 'budget',
                'severity': 'high',
                'description': 'Significant budget discrepancies detected',
                'score': 85.0
            },
            {
                'category': 'compliance',
                'severity': 'high',
                'description': 'Missing required environmental impact assessments',
                'score': 80.0
            },
            {
                'category': 'timeline',
                'severity': 'medium',
                'description': 'Unrealistic project timeline',
                'score': 65.0
            }
        ]
    }
    
    mock_compliance_report = {
        'compliance_score': 45.2,
        'violations': [
            {
                'type': 'environmental',
                'severity': 'high',
                'message': 'Proposal does not address climate change mitigation requirements from EO 14008',
                'executive_order': 'EO 14008',
                'recommendation': 'Add comprehensive climate impact assessment and mitigation plan'
            },
            {
                'type': 'equity',
                'severity': 'high',
                'message': 'Insufficient community engagement plan violates EO 13985 equity requirements',
                'executive_order': 'EO 13985',
                'recommendation': 'Develop detailed community outreach and engagement strategy'
            },
            {
                'type': 'cybersecurity',
                'severity': 'medium',
                'message': 'Missing cybersecurity framework documentation required by EO 14028',
                'executive_order': 'EO 14028',
                'recommendation': 'Include cybersecurity assessment and compliance plan'
            }
        ],
        'warnings': [
            {'message': 'Budget justification needs more detail'},
            {'message': 'Timeline may be optimistic for stated deliverables'}
        ],
        'relevant_executive_orders': [
            'EO 14008 - Climate Crisis',
            'EO 13985 - Racial Equity',
            'EO 14028 - Cybersecurity'
        ],
        'recommendations': [
            {
                'priority': 'high',
                'action': 'Add Climate Impact Assessment',
                'description': 'Include detailed environmental analysis per EO 14008'
            },
            {
                'priority': 'high',
                'action': 'Develop Community Engagement Plan',
                'description': 'Create comprehensive outreach strategy per EO 13985'
            },
            {
                'priority': 'medium',
                'action': 'Add Cybersecurity Documentation',
                'description': 'Include security framework compliance per EO 14028'
            }
        ]
    }
    
    mock_summary = {
        'executive_summary': (
            'This grant proposal requests $2.5M for a community infrastructure project. '
            'The AI analysis has identified significant compliance concerns requiring immediate '
            'attorney review. Key issues include missing environmental impact assessments (EO 14008), '
            'insufficient community engagement planning (EO 13985), and incomplete cybersecurity '
            'documentation (EO 14028). The proposal shows a high risk score of 78.5% with 92.3% '
            'confidence. Budget discrepancies and timeline concerns were also flagged. '
            'Recommendation: Attorney review required before approval.'
        )
    }
    
    mock_metadata = {
        'upload_timestamp': datetime.now().isoformat(),
        'processor': 'test_script',
        'analysis_version': '1.0.0'
    }
    
    print("\n" + "-"*60)
    print("Preparing Email")
    print("-"*60)
    
    # Prepare email
    email_data = agent.prepare_email(
        proposal_filename='TEST_High_Risk_Proposal.pdf', # type: ignore
        risk_report=mock_risk_report,
        compliance_report=mock_compliance_report,
        summary=mock_summary,
        metadata=mock_metadata
    )
    
    print(f"\nTo: {email_data['to']}")
    print(f"From: {email_data['from']}")
    print(f"Subject: {email_data['subject']}")
    print(f"Priority: {email_data['priority']}")
    
    print("\n" + "-"*60)
    print("Sending Email via SMTP")
    print("-"*60)
    
    try:
        # Send email via SMTP
        result = agent.send_email(email_data)
        
        print("\n✅ SUCCESS: Email sent via SMTP!")
        print(f"\nMethod: {result['method']}")
        print(f"Status: {result['status']}")
        print(f"Message ID: {result['message_id']}")
        print(f"Sent At: {result['sent_at']}")
        print(f"SMTP Server: {result.get('smtp_server', 'N/A')}")
        
        print("\n" + "="*60)
        print("CHECK YOUR EMAIL: brittanypugh@microsoft.com")
        print("="*60)
        
        return True
        
    except Exception as e:
        print("\n❌ ERROR: Failed to send email")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify SMTP_PASSWORD is correct in .env")
        print("2. If you have 2FA enabled, use an app password")
        print("3. Check if your account allows SMTP authentication")
        print("4. Ensure smtp.office365.com is accessible from your network")
        return False

if __name__ == "__main__":
    success = test_smtp_email()
    sys.exit(0 if success else 1)
