#!/usr/bin/env python3
"""
Test Email Notification Script

Tests the email notification functionality by creating a mock high-risk scenario
and triggering the email notification to brittanypugh@microsoft.com

Supports both Microsoft Graph API and SMTP email sending.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.email_trigger_agent import EmailTriggerAgent
from dotenv import load_dotenv

def create_mock_data():
    """Create mock data simulating a high-risk grant proposal."""
    
    # Mock risk report (high risk scenario)
    risk_report = {
        'overall_score': 78.5,
        'risk_level': 'high',
        'confidence': 92.0,
        'requires_notification': True,
        'risk_breakdown': {
            'compliance_risk': {
                'score': 85.0,
                'violations_count': 3,
                'warnings_count': 2
            },
            'quality_risk': {
                'score': 65.0,
                'word_count': 1200,
                'page_count': 4
            },
            'completeness_risk': {
                'score': 70.0
            }
        },
        'risk_factors': [
            {
                'factor': 'Multiple Compliance Violations',
                'severity': 'high',
                'description': 'Proposal conflicts with Executive Order 14028 (Cybersecurity) requirements'
            },
            {
                'factor': 'Incomplete Budget Justification',
                'severity': 'medium',
                'description': 'Budget section lacks detailed cost breakdowns'
            },
            {
                'factor': 'Missing Equity Statement',
                'severity': 'high',
                'description': 'No diversity, equity, and inclusion plan provided'
            }
        ],
        'recommendations': [
            {
                'priority': 'critical',
                'action': 'Address cybersecurity compliance violations',
                'description': 'Revise security protocols to align with EO 14028 requirements'
            },
            {
                'priority': 'high',
                'action': 'Add comprehensive DEI plan',
                'description': 'Include detailed diversity and inclusion strategies per EO 13985'
            },
            {
                'priority': 'medium',
                'action': 'Expand budget justification',
                'description': 'Provide itemized cost breakdown for all major expenses'
            }
        ]
    }
    
    # Mock compliance report
    compliance_report = {
        'compliance_score': 62.5,
        'overall_status': 'non_compliant',
        'relevant_executive_orders': [
            {
                'name': 'EO 14028 - Improving the Nation\'s Cybersecurity',
                'relevance': 95.0,
                'key_requirements': [
                    'Implement zero-trust architecture',
                    'Deploy multi-factor authentication',
                    'Conduct regular security audits',
                    'Encrypt sensitive data in transit and at rest'
                ]
            },
            {
                'name': 'EO 13985 - Advancing Racial Equity',
                'relevance': 88.0,
                'key_requirements': [
                    'Develop equity impact assessment',
                    'Include underserved communities in planning',
                    'Set measurable equity goals'
                ]
            },
            {
                'name': 'EO 14008 - Tackling the Climate Crisis',
                'relevance': 72.0,
                'key_requirements': [
                    'Assess environmental impact',
                    'Incorporate climate resilience',
                    'Use sustainable materials and practices'
                ]
            }
        ],
        'violations': [
            {
                'message': 'Missing mandatory cybersecurity protocols',
                'executive_order': 'EO 14028',
                'requirement': 'Zero-trust architecture implementation plan required but not found',
                'severity': 'high'
            },
            {
                'message': 'No diversity and inclusion plan provided',
                'executive_order': 'EO 13985',
                'requirement': 'Equity impact assessment must be included for all federal grants',
                'severity': 'high'
            },
            {
                'message': 'Incomplete climate impact analysis',
                'executive_order': 'EO 14008',
                'requirement': 'Environmental sustainability assessment incomplete',
                'severity': 'medium'
            }
        ],
        'warnings': [
            {
                'message': 'Budget justification lacks detail',
                'executive_order': 'General Grant Requirements',
                'description': 'More detailed cost breakdown recommended'
            },
            {
                'message': 'Timeline may be overly optimistic',
                'executive_order': 'General Grant Requirements',
                'description': 'Consider adding buffer time for deliverables'
            }
        ]
    }
    
    # Mock summary
    summary = {
        'executive_summary': 'This proposal requests $2.5M in federal funding to develop a community technology center providing digital literacy training and internet access to underserved neighborhoods. The project aims to bridge the digital divide but currently lacks sufficient detail on cybersecurity measures, equity planning, and environmental sustainability.',
        'key_clauses': [
            'Primary objective: Establish community technology center serving 5,000 residents annually',
            'Budget request: $2,500,000 over 3 years',
            'Target population: Low-income communities with limited internet access',
            'Key deliverables: Physical facility, equipment procurement, training programs, ongoing support services'
        ],
        'key_topics': [
            'digital literacy',
            'community development',
            'technology access',
            'workforce development'
        ]
    }
    
    # Mock metadata
    metadata = {
        'filename': 'Community_Tech_Center_Proposal_2025.pdf',
        'file_path': '/tmp/test_proposal.pdf',
        'word_count': 3542,
        'page_count': 12,
        'processing_timestamp': datetime.now().isoformat(),
        'file_size': 245678
    }
    
    return risk_report, compliance_report, summary, metadata


def test_email_notification():
    """Test the email notification system."""
    
    print("=" * 70)
    print("📧 Email Notification Test")
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Create mock data
    print("\n📋 Creating mock high-risk proposal data...")
    risk_report, compliance_report, summary, metadata = create_mock_data()
    
    print(f"   Risk Level: {risk_report['risk_level'].upper()}")
    print(f"   Risk Score: {risk_report['overall_score']:.1f}%")
    print(f"   Compliance Score: {compliance_report['compliance_score']:.1f}%")
    print(f"   Violations: {len(compliance_report['violations'])}")
    
    # Initialize email agent
    print("\n🔧 Initializing Email Trigger Agent...")
    email_agent = EmailTriggerAgent(use_graph_api=False)  # Demo mode
    
    print(f"   Target Email: {email_agent.attorney_email}")
    print(f"   Sender Email: {email_agent.sender_email}")
    print(f"   Mode: {'Graph API' if email_agent.use_graph_api else 'Demo (Simulated)'}")
    
    # Prepare email
    print("\n📝 Preparing email notification...")
    email_data = email_agent.prepare_email(
        risk_report=risk_report,
        compliance_report=compliance_report,
        summary=summary,
        metadata=metadata
    )
    
    print(f"   Subject: {email_data['subject']}")
    print(f"   Priority: {email_data['priority'].upper()}")
    
    # Send email
    print("\n📤 Sending email notification...")
    send_result = email_agent.send_email(email_data)
    
    print(f"   Status: {send_result['status'].upper()}")
    print(f"   Method: {send_result['method']}")
    print(f"   Sent At: {send_result['sent_at']}")
    
    if send_result['status'] == 'sent':
        print("\n✅ Email notification sent successfully!")
    else:
        print("\n⚠️ Email notification simulated (demo mode)")
        print("   In production, configure Microsoft Graph API credentials")
    
    # Display email preview
    print("\n" + "=" * 70)
    print("📧 EMAIL PREVIEW")
    print("=" * 70)
    print(f"\nFrom: {email_data['from']}")
    print(f"To: {email_data['to']}")
    print(f"Subject: {email_data['subject']}")
    print(f"Priority: {email_data['priority']}")
    print("\n" + "-" * 70)
    print("BODY (Text Version):")
    print("-" * 70)
    print(email_data['body_text'])
    print("-" * 70)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print("✓ Mock data generated")
    print("✓ Email agent initialized")
    print(f"✓ Email prepared: {email_data['subject']}")
    print(f"✓ Email {send_result['status']}: via {send_result['method']}")
    print(f"✓ Target: {email_agent.attorney_email}")
    
    print("\n💡 Email Sending Methods (in priority order):")
    print("   1. Microsoft Graph API - Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    print("   2. SMTP - Set SMTP_ENABLED=true, SMTP_PASSWORD in .env")
    print("   3. Simulation - Demo mode (current)")
    
    if send_result['status'] == 'sent':
        print(f"\n✅ EMAIL SENT via {send_result['method'].upper()}!")
        print(f"   Message ID: {send_result['message_id']}")
        print(f"   Check your inbox: {email_agent.attorney_email}")
    elif send_result['status'] == 'simulated':
        print("\n⚠️ EMAIL SIMULATED (demo mode)")
        print("   Configure Graph API or SMTP to send real emails")
    
    print("\n" + "=" * 70)
    print("✅ Test completed successfully!")
    print("=" * 70)
    
    return send_result


if __name__ == "__main__":
    try:
        result = test_email_notification()
        sys.exit(0 if result['status'] in ['sent', 'simulated'] else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
