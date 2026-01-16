"""
Azure Durable Function - Email Notifier
Handles email notifications for grant proposal compliance reviews
"""

import logging
import azure.functions as func
import azure.durable_functions as df
from typing import Dict, Any
import os
import json

def orchestrator_function(context: df.DurableOrchestrationContext):
    """
    Orchestrator function for email notification workflow.
    """
    # Get input data
    input_data = context.get_input()
    
    # Step 1: Prepare email
    email_data = yield context.call_activity('prepare_email', input_data)
    
    # Step 2: Send email
    send_result = yield context.call_activity('send_email', email_data)
    
    # Step 3: Log result
    yield context.call_activity('log_notification', {
        'email_data': email_data,
        'send_result': send_result
    })
    
    return send_result


app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)

# Orchestrator
app.orchestration_trigger(context_name="context")(orchestrator_function)


@app.activity_trigger(input_name="emailInput")
def prepare_email(emailInput: Dict[str, Any]):
    """
    Activity function to prepare email content.
    """
    logging.info("Preparing email content")
    
    risk_report = emailInput.get('risk_report', {})
    compliance_report = emailInput.get('compliance_report', {})
    metadata = emailInput.get('metadata', {})
    
    # Prepare email data
    email_data = {
        'to': os.environ.get('ATTORNEY_EMAIL', 'attorney@county.gov'),
        'from': os.environ.get('SENDER_EMAIL', 'compliance@county.gov'),
        'subject': f"Grant Proposal Review Required - {metadata.get('filename', 'Unknown')}",
        'body': generate_email_body(risk_report, compliance_report, metadata),
        'priority': 'high' if risk_report.get('risk_level') == 'high' else 'normal'
    }
    
    return email_data


@app.activity_trigger(input_name="emailData")
def send_email(emailData: Dict[str, Any]):
    """
    Activity function to send email via Microsoft Graph API.
    """
    logging.info(f"Sending email to {emailData['to']}")
    
    try:
        # Import here to avoid circular dependencies
        from msal import ConfidentialClientApplication
        import requests
        
        # Get Azure AD credentials
        client_id = os.environ.get('AZURE_CLIENT_ID')
        client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        tenant_id = os.environ.get('AZURE_TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            logging.warning("Azure AD credentials not configured. Simulating email send.")
            return {
                'status': 'simulated',
                'message': 'Email simulated (credentials not configured)'
            }
        
        # Get access token
        app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret
        )
        
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        
        if not result or "access_token" not in result:
            error_desc = result.get('error_description') if result else 'No result returned'
            raise Exception(f"Failed to acquire token: {error_desc}")
        
        access_token = result["access_token"]
        
        # Prepare email message
        message = {
            "message": {
                "subject": emailData['subject'],
                "body": {
                    "contentType": "HTML",
                    "content": emailData['body']
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": emailData['to']
                        }
                    }
                ],
                "importance": emailData['priority']
            },
            "saveToSentItems": "true"
        }
        
        # Send email
        endpoint = f"https://graph.microsoft.com/v1.0/users/{emailData['from']}/sendMail"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(endpoint, headers=headers, json=message)
        response.raise_for_status()
        
        logging.info("Email sent successfully")
        return {
            'status': 'sent',
            'message': 'Email sent successfully'
        }
        
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return {
            'status': 'failed',
            'message': str(e)
        }


@app.activity_trigger(input_name="logInput")
def log_notification(logInput: Dict[str, Any]):
    """
    Activity function to log notification results.
    """
    logging.info("Logging notification result")
    
    # In production, store in Azure Storage or database
    log_entry = {
        'timestamp': logInput.get('timestamp'),
        'email_to': logInput.get('email_data', {}).get('to'),
        'status': logInput.get('send_result', {}).get('status'),
        'message': logInput.get('send_result', {}).get('message')
    }
    
    logging.info(f"Notification logged: {json.dumps(log_entry)}")
    return log_entry


@app.route(route="email_trigger", auth_level=func.AuthLevel.FUNCTION)
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    """
    HTTP trigger to start the email notification orchestration.
    """
    try:
        # Get request data
        req_body = req.get_json()
        
        # Start orchestration
        instance_id = await client.start_new("orchestrator_function", None, req_body)
        
        logging.info(f"Started orchestration with ID = '{instance_id}'")
        
        return client.create_check_status_response(req, instance_id)
        
    except Exception as e:
        logging.error(f"Error starting orchestration: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )


def generate_email_body(risk_report: Dict[str, Any], compliance_report: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Generate HTML email body."""
    risk_level = risk_report.get('risk_level', 'unknown')
    risk_score = risk_report.get('overall_score', 0)
    compliance_score = compliance_report.get('compliance_score', 0)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background-color: #0078D4; color: white; padding: 20px; }}
        .content {{ padding: 20px; }}
        .metric {{ margin: 10px 0; }}
        .risk-high {{ color: #D13438; font-weight: bold; }}
        .risk-medium {{ color: #FFB900; font-weight: bold; }}
        .footer {{ padding: 20px; background-color: #F3F2F1; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Grant Proposal Compliance Review Required</h2>
    </div>
    <div class="content">
        <p><strong>Document:</strong> {metadata.get('filename', 'Unknown')}</p>
        <p><strong>Risk Level:</strong> <span class="risk-{risk_level}">{risk_level.upper()}</span></p>
        
        <div class="metric">
            <p><strong>Risk Score:</strong> {risk_score:.1f}%</p>
            <p><strong>Compliance Score:</strong> {compliance_score:.1f}%</p>
        </div>
        
        <p>This grant proposal requires attorney review. Please log in to the compliance system to review the full analysis.</p>
    </div>
    <div class="footer">
        <p>This is an automated message from the Grant Proposal Compliance System.</p>
    </div>
</body>
</html>
"""
    return html
