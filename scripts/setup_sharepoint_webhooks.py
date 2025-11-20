"""
Setup script for SharePoint webhook subscriptions.
Creates webhooks for all configured document libraries.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_access_token():
    """Get access token for SharePoint API using client credentials."""
    import msal
    
    authority = f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}"
    app = msal.ConfidentialClientApplication(
        os.getenv('SHAREPOINT_CLIENT_ID'),
        authority=authority,
        client_credential=os.getenv('SHAREPOINT_CLIENT_SECRET')
    )
    
    # Get token for SharePoint
    site_url = os.getenv('SHAREPOINT_SITE_URL', '')
    tenant_domain = site_url.split('/')[2]  # Extract domain from URL
    resource = f"https://{tenant_domain}"
    
    result = app.acquire_token_for_client(scopes=[f"{resource}/.default"])
    
    if result and "access_token" in result:
        return result["access_token"]
    else:
        error_desc = result.get('error_description') if result else 'No result returned'
        raise Exception(f"Failed to get access token: {error_desc}")


def create_sharepoint_webhook(site_url, list_id, notification_url):
    """
    Create a webhook subscription for a SharePoint list/library.
    
    Args:
        site_url: SharePoint site URL
        list_id: GUID of the document library
        notification_url: Your Azure Function endpoint URL
    
    Returns:
        Webhook subscription info or None
    """
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions"
    
    # Webhook expires after 6 months (max)
    expiration = (datetime.utcnow() + timedelta(days=180)).isoformat() + 'Z'
    
    payload = {
        "resource": f"{site_url}/_api/web/lists(guid'{list_id}')",
        "notificationUrl": notification_url,
        "expirationDateTime": expiration,
        "clientState": os.getenv('WEBHOOK_CLIENT_STATE', 'your-secret-state-value')
    }
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    
    if response.status_code == 201:
        subscription = response.json()
        print("✓ Webhook created successfully")
        print(f"  ID: {subscription['id']}")
        print(f"  Expires: {subscription['expirationDateTime']}")
        return subscription
    else:
        print(f"✗ Webhook creation failed: {response.status_code}")
        print(f"  {response.text}")
        return None


def check_webhook_status(site_url, list_id):
    """Check status of all webhooks for a list."""
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions"
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        subscriptions = response.json().get('value', [])
        
        if not subscriptions:
            print("  No webhooks found")
            return []
        
        for sub in subscriptions:
            expiration = datetime.fromisoformat(sub['expirationDateTime'].rstrip('Z'))
            days_until_expiry = (expiration - datetime.utcnow()).days
            
            print(f"  Webhook ID: {sub['id']}")
            print(f"    Notification URL: {sub['notificationUrl']}")
            print(f"    Expires in {days_until_expiry} days")
            
            if days_until_expiry < 30:
                print("    ⚠️  NEEDS RENEWAL")
        
        return subscriptions
    else:
        print(f"  Error checking webhooks: {response.status_code}")
        return []


def delete_webhook(site_url, list_id, subscription_id):
    """Delete a webhook subscription."""
    endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/subscriptions('{subscription_id}')"
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }
    
    response = requests.delete(endpoint, headers=headers)
    
    if response.status_code == 204:
        print(f"✓ Webhook deleted: {subscription_id}")
        return True
    else:
        print(f"✗ Failed to delete webhook: {response.status_code}")
        return False


def setup_all_webhooks():
    """Set up webhooks for all configured SharePoint libraries."""
    
    # Load environment variables
    load_dotenv()
    
    site_url = os.getenv('SHAREPOINT_SITE_URL')
    if not site_url:
        print("❌ SHAREPOINT_SITE_URL not configured in .env")
        return
    
    # Get Function App URL
    function_app_name = os.getenv('FUNCTION_APP_NAME', 'grant-compliance-webhook-handler')
    function_url = f"https://{function_app_name}.azurewebsites.net/api/SharePointWebhookHandler"
    
    print("=" * 80)
    print("SharePoint Webhook Setup")
    print("=" * 80)
    print(f"Site URL: {site_url}")
    print(f"Function URL: {function_url}")
    print()
    
    # Define libraries to configure
    # Note: You need to get the actual list GUIDs from SharePoint
    libraries = [
        {
            "name": "GrantProposals",
            "list_id": os.getenv('SHAREPOINT_GRANT_PROPOSALS_LIST_ID', '')
        },
        {
            "name": "ExecutiveOrders",
            "list_id": os.getenv('SHAREPOINT_EXECUTIVE_ORDERS_LIST_ID', '')
        },
        {
            "name": "ComplianceReports",
            "list_id": os.getenv('SHAREPOINT_COMPLIANCE_REPORTS_LIST_ID', '')
        }
    ]
    
    for library in libraries:
        if not library['list_id']:
            print(f"\n⚠️  Skipping {library['name']} - List ID not configured")
            continue
        
        print(f"\n📚 {library['name']}")
        print("-" * 80)
        
        # Check existing webhooks
        print("Checking existing webhooks...")
        existing = check_webhook_status(site_url, library['list_id'])
        
        # Ask to create new webhook
        if not existing:
            print(f"\nCreating webhook for {library['name']}...")
            create_sharepoint_webhook(
                site_url=site_url,
                list_id=library['list_id'],
                notification_url=function_url
            )
        else:
            print(f"\nWebhook already exists for {library['name']}")
    
    print("\n" + "=" * 80)
    print("Setup complete!")
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage SharePoint webhooks")
    parser.add_argument('action', choices=['setup', 'check', 'delete'],
                        help='Action to perform')
    parser.add_argument('--list-id', help='List ID for check/delete actions')
    parser.add_argument('--subscription-id', help='Subscription ID for delete action')
    
    args = parser.parse_args()
    
    load_dotenv()
    site_url = os.getenv('SHAREPOINT_SITE_URL')
    
    if args.action == 'setup':
        setup_all_webhooks()
    elif args.action == 'check':
        if not args.list_id:
            print("Error: --list-id required for check action")
            return
        print(f"Checking webhooks for list {args.list_id}...")
        check_webhook_status(site_url, args.list_id)
    elif args.action == 'delete':
        if not args.list_id or not args.subscription_id:
            print("Error: --list-id and --subscription-id required for delete action")
            return
        delete_webhook(site_url, args.list_id, args.subscription_id)


if __name__ == "__main__":
    main()
