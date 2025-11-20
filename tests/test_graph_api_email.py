#!/usr/bin/env python3
"""
Test Graph API Email Sending

This script tests real email sending via Microsoft Graph API.
Make sure to configure AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID in .env first.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.email_trigger_agent import EmailTriggerAgent
from dotenv import load_dotenv
import os

def test_graph_api():
    """Test Microsoft Graph API email sending."""
    
    print("=" * 70)
    print("📧 Microsoft Graph API Email Test")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    
    # Check configuration
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    sender_email = os.getenv('SENDER_EMAIL', 'compliance@county.gov')
    attorney_email = os.getenv('ATTORNEY_EMAIL', 'brittanypugh@microsoft.com')
    
    print("\n🔧 Configuration Check:")
    print(f"   Client ID: {'✓ Configured' if client_id and client_id != 'your_azure_client_id_here' else '✗ Not configured'}")
    print(f"   Client Secret: {'✓ Configured' if client_secret and client_secret != 'your_azure_client_secret_here' else '✗ Not configured'}")
    print(f"   Tenant ID: {'✓ Configured' if tenant_id and tenant_id != 'your_azure_tenant_id_here' else '✗ Not configured'}")
    print(f"   Sender: {sender_email}")
    print(f"   Recipient: {attorney_email}")
    
    if not all([
        client_id and client_id != 'your_azure_client_id_here',
        client_secret and client_secret != 'your_azure_client_secret_here',
        tenant_id and tenant_id != 'your_azure_tenant_id_here'
    ]):
        print("\n❌ Error: Microsoft Graph API credentials not configured")
        print("\n📝 Setup Instructions:")
        print("   1. See GRAPH_API_SETUP.md for detailed setup guide")
        print("   2. Update .env with your Azure AD app credentials:")
        print("      - AZURE_CLIENT_ID")
        print("      - AZURE_CLIENT_SECRET")
        print("      - AZURE_TENANT_ID")
        print("   3. Run this test again")
        return False
    
    # Initialize email agent with Graph API enabled
    print("\n🚀 Initializing Email Agent with Graph API...")
    try:
        email_agent = EmailTriggerAgent(use_graph_api=True)
        
        if not email_agent.use_graph_api:
            print("⚠️  Warning: Graph API not enabled (missing credentials)")
            return False
            
        print("   ✓ Email agent initialized successfully")
        
    except Exception as e:
        print(f"   ✗ Error initializing agent: {e}")
        return False
    
    # Create test email
    print("\n📝 Creating test email...")
    email_data = {
        'subject': '🧪 Test Email - Grant Compliance System',
        'body_text': '''This is a test email from the Grant Compliance System.

If you receive this email, Microsoft Graph API is configured correctly!

Test Details:
- Sender: {sender}
- Timestamp: {timestamp}
- Method: Microsoft Graph API

Next Steps:
1. Verify you received this email
2. Check that it's not in spam/junk folder
3. Confirm sender address is correct

If you have any issues, see GRAPH_API_SETUP.md for troubleshooting.
'''.format(sender=sender_email, timestamp='2025-11-17 23:48:17'),
        'body_html': '''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #0078D4;">🧪 Test Email - Grant Compliance System</h2>
    
    <p>This is a test email from the <strong>Grant Compliance System</strong>.</p>
    
    <div style="background-color: #DFF6DD; border-left: 4px solid #107C10; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>✓ Success!</strong> If you receive this email, Microsoft Graph API is configured correctly!</p>
    </div>
    
    <h3>Test Details:</h3>
    <ul>
        <li><strong>Sender:</strong> {sender}</li>
        <li><strong>Timestamp:</strong> 2025-11-17 23:48:17</li>
        <li><strong>Method:</strong> Microsoft Graph API</li>
    </ul>
    
    <h3>Next Steps:</h3>
    <ol>
        <li>Verify you received this email</li>
        <li>Check that it's not in spam/junk folder</li>
        <li>Confirm sender address is correct</li>
    </ol>
    
    <p style="color: #605E5C; font-size: 0.9em; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
        If you have any issues, see <code>GRAPH_API_SETUP.md</code> for troubleshooting.
    </p>
</body>
</html>
'''.format(sender=sender_email),
        'to': attorney_email,
        'from': sender_email,
        'priority': 'normal',
        'metadata': {
            'test': True,
            'purpose': 'Graph API Configuration Test'
        }
    }
    
    print(f"   Subject: {email_data['subject']}")
    print(f"   To: {email_data['to']}")
    print(f"   From: {email_data['from']}")
    
    # Send test email
    print("\n📤 Sending test email via Microsoft Graph API...")
    try:
        result = email_agent.send_email(email_data)
        
        print(f"\n   Status: {result['status'].upper()}")
        print(f"   Method: {result['method']}")
        print(f"   Sent At: {result['sent_at']}")
        
        if result['status'] == 'sent':
            print("\n" + "=" * 70)
            print("✅ SUCCESS! Email sent via Microsoft Graph API")
            print("=" * 70)
            print(f"\n📬 Check your inbox: {attorney_email}")
            print("   (Also check spam/junk folder)")
            print("\n💡 The email notification system is now fully configured!")
            return True
        else:
            print("\n" + "=" * 70)
            print("⚠️  Email was not sent")
            print("=" * 70)
            if 'error' in result:
                print(f"\nError details: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error sending email: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify API permissions in Azure AD app")
        print("   2. Check that admin consent was granted")
        print("   3. Ensure sender mailbox exists and is accessible")
        print("   4. See GRAPH_API_SETUP.md for detailed troubleshooting")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_graph_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
