"""
Email Trigger Agent
Prepares and triggers email notifications using Microsoft Graph API or SMTP.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class EmailTriggerAgent:
    """
    Agent responsible for preparing and sending email notifications
    to attorneys when proposals require review.
    """
    
    def __init__(self, use_graph_api: bool = False):
        """
        Initialize the Email Trigger Agent.
        
        Args:
            use_graph_api: If True, use Microsoft Graph API. Otherwise, try SMTP or simulate.
        """
        self.use_graph_api = use_graph_api
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.sender_email = os.getenv('SENDER_EMAIL', 'brittanypugh@microsoft.com')
        self.attorney_email = os.getenv('ATTORNEY_EMAIL', 'brittanypugh@microsoft.com')
        
        # SMTP configuration
        self.smtp_enabled = os.getenv('SMTP_ENABLED', 'false').lower() == 'true'
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.office365.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if self.use_graph_api and not self.client_id:
            logger.info("Microsoft Graph API not configured. Will try SMTP fallback.")
            self.use_graph_api = False
    
    def prepare_email(
        self,
        risk_report: Dict[str, Any],
        compliance_report: Dict[str, Any],
        summary: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare email content for attorney notification.
        
        Args:
            risk_report: Results from RiskScoringAgent
            compliance_report: Results from ComplianceAgent or ComplianceAgentFoundry
            summary: Summary from SummarizationAgent
            metadata: Document metadata
            
        Returns:
            Dictionary containing email subject, body, and metadata
        """
        logger.info("Preparing email notification")
        
        risk_level = risk_report['risk_level']
        risk_score = risk_report['overall_score']
        # Check both 'file_name' and 'filename' for compatibility
        filename = metadata.get('file_name') or metadata.get('filename', 'Unknown Document')
        
        # Determine priority
        priority = self._determine_priority(risk_level)
        
        # Generate subject
        subject = self._generate_subject(filename, risk_level, risk_score)
        
        # Generate body
        body_html = self._generate_html_body(
            filename,
            risk_report,
            compliance_report,
            summary,
            metadata
        )
        
        body_text = self._generate_text_body(
            filename,
            risk_report,
            compliance_report,
            summary
        )
        
        email_data = {
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text,
            'priority': priority,
            'to': self.attorney_email,
            'from': self.sender_email,
            'metadata': {
                'prepared_at': datetime.now().isoformat(),
                'document': filename,
                'risk_level': risk_level,
                'risk_score': risk_score
            }
        }
        
        logger.info(f"Email prepared: {subject}")
        return email_data
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email notification with fallback support.
        
        Tries methods in order:
        1. Microsoft Graph API (if configured)
        2. SMTP (if enabled and configured)
        3. Simulation (demo mode)
        
        Args:
            email_data: Email content and metadata
            
        Returns:
            Dictionary containing send status and details
        """
        logger.info(f"Sending email: {email_data['subject']}")
        
        try:
            # Try Graph API first if configured
            if self.use_graph_api:
                try:
                    result = self._send_via_graph_api(email_data)
                    logger.info(f"Email sent via Graph API: {result['message_id']}")
                    return result
                except Exception as graph_error:
                    logger.warning(f"Graph API failed: {graph_error}. Trying SMTP fallback...")
            
            # Try SMTP if enabled
            if self.smtp_enabled and self.smtp_username and self.smtp_password:
                try:
                    result = self._send_via_smtp(email_data)
                    logger.info(f"Email sent via SMTP: {result['message_id']}")
                    return result
                except Exception as smtp_error:
                    logger.warning(f"SMTP failed: {smtp_error}. Using simulation...")
            
            # Fall back to simulation
            result = self._simulate_email_send(email_data)
            logger.info(f"Email simulated: {result['message_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
    
    def _determine_priority(self, risk_level: str) -> str:
        """Determine email priority based on risk level."""
        if risk_level == 'high':
            return 'high'
        elif risk_level == 'medium-high':
            return 'high'
        elif risk_level == 'medium':
            return 'normal'
        else:
            return 'low'
    
    def _generate_subject(self, filename: str, risk_level: str, risk_score: float) -> str:
        """Generate email subject line."""
        urgency = ""
        if risk_level == 'high':
            urgency = "[URGENT] "
        elif risk_level == 'medium-high':
            urgency = "[PRIORITY] "
        
        return f"{urgency}Grant Proposal Review Required - {filename} (Risk: {risk_score:.1f}%)"
    
    def _generate_html_body(
        self,
        filename: str,
        risk_report: Dict[str, Any],
        compliance_report: Dict[str, Any],
        summary: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate HTML email body."""
        risk_level = risk_report['risk_level']
        risk_score = risk_report['overall_score']
        compliance_score = compliance_report.get('compliance_score', 0)
        # Use the AI's confidence in its analysis (from compliance agent)
        # NOT the risk-derived confidence which correlates with overall_score
        confidence = compliance_report.get('confidence_score', risk_report.get('confidence', 70))
        
        # Risk level color
        risk_color = {
            'high': '#dc3545',
            'medium-high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }.get(risk_level, '#6c757d')
        
        violations = compliance_report.get('violations', [])
        warnings = compliance_report.get('warnings', [])
        recommendations = risk_report.get('recommendations', [])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid {risk_color}; }}
        .risk-badge {{ display: inline-block; padding: 5px 10px; background-color: {risk_color}; 
                      color: white; border-radius: 4px; font-weight: bold; }}
        .section {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 4px; }}
        .section h3 {{ margin-top: 0; color: #495057; }}
        .violation {{ background-color: #f8d7da; padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .warning {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .recommendation {{ background-color: #d1ecf1; padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; 
                   font-size: 12px; color: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background-color: #e9ecef; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Grant Proposal Compliance Review Required</h2>
        <p><strong>Document:</strong> {filename}</p>
        <p><strong>Risk Level:</strong> <span class="risk-badge">{risk_level.upper()}</span></p>
        <p><strong>Risk Score:</strong> {risk_score:.1f}%</p>
        <p><strong>Compliance Score:</strong> {compliance_score:.1f}% (AI Confidence: {confidence:.1f}%)</p>
    </div>
    
    <div class="section">
        <h3>📋 Executive Summary</h3>
        <p>{summary.get('executive_summary', 'No summary available')[:500]}...</p>
    </div>
    
    <div class="section">
        <h3>⚠️ Compliance Status</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Compliance Score</td>
                <td>{compliance_report.get('compliance_score', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Violations</td>
                <td>{len(violations)}</td>
            </tr>
            <tr>
                <td>Warnings</td>
                <td>{len(warnings)}</td>
            </tr>
            <tr>
                <td>Relevant Executive Orders</td>
                <td>{len(compliance_report.get('relevant_executive_orders', []))}</td>
            </tr>
        </table>
    </div>
"""
        
        # Add violations
        if violations:
            html += """
    <div class="section">
        <h3>🚨 Compliance Violations</h3>
"""
            for i, violation in enumerate(violations[:5], 1):
                html += f"""
        <div class="violation">
            <strong>Violation {i}:</strong> {violation.get('message', 'Unknown violation')}<br>
            <em>Executive Order:</em> {violation.get('executive_order', 'Unknown')}<br>
            <em>Requirement:</em> {violation.get('requirement', 'Unknown')[:150]}...
        </div>
"""
            html += "    </div>\n"
        
        # Add warnings
        if warnings:
            html += """
    <div class="section">
        <h3>⚡ Warnings</h3>
"""
            for i, warning in enumerate(warnings[:5], 1):
                html += f"""
        <div class="warning">
            <strong>Warning {i}:</strong> {warning.get('message', 'Unknown warning')}<br>
            <em>Executive Order:</em> {warning.get('executive_order', 'Unknown')}
        </div>
"""
            html += "    </div>\n"
        
        # Add recommendations
        if recommendations:
            html += """
    <div class="section">
        <h3>💡 Recommendations</h3>
"""
            for i, rec in enumerate(recommendations, 1):
                html += f"""
        <div class="recommendation">
            <strong>Priority {rec.get('priority', 'medium').upper()}:</strong> {rec.get('action', 'Unknown')}<br>
            {rec.get('description', 'No description')}
        </div>
"""
            html += "    </div>\n"
        
        # Footer
        html += f"""
    <div class="section">
        <h3>📎 Document Information</h3>
        <table>
            <tr>
                <td><strong>File Name:</strong></td>
                <td>{filename}</td>
            </tr>
            <tr>
                <td><strong>Word Count:</strong></td>
                <td>{metadata.get('word_count', 'Unknown')}</td>
            </tr>
            <tr>
                <td><strong>Page Count:</strong></td>
                <td>{metadata.get('page_count', 'Unknown')}</td>
            </tr>
            <tr>
                <td><strong>Processed:</strong></td>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p><strong>Action Required:</strong> Please review this grant proposal and validate the AI-generated 
        compliance analysis. Log in to the system to approve, modify, or reject.</p>
        <p>This is an automated message from the Grant Proposal Compliance System.</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_text_body(
        self,
        filename: str,
        risk_report: Dict[str, Any],
        compliance_report: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> str:
        """Generate plain text email body."""
        risk_level = risk_report['risk_level']
        risk_score = risk_report['overall_score']
        compliance_score = compliance_report.get('compliance_score', 0)
        # Use AI's confidence from compliance analysis, not risk-derived confidence
        confidence = compliance_report.get('confidence_score', risk_report.get('confidence', 70))
        
        text = f"""
GRANT PROPOSAL COMPLIANCE REVIEW REQUIRED

Document: {filename}
Risk Level: {risk_level.upper()}
Risk Score: {risk_score:.1f}%
Compliance Score: {compliance_score:.1f}%
AI Confidence: {confidence:.1f}%

EXECUTIVE SUMMARY:
{summary.get('executive_summary', 'No summary available')[:500]}...

COMPLIANCE STATUS:
- Compliance Score: {compliance_report.get('compliance_score', 0):.1f}%
- Violations: {len(compliance_report.get('violations', []))}
- Warnings: {len(compliance_report.get('warnings', []))}
- Relevant Executive Orders: {len(compliance_report.get('relevant_executive_orders', []))}

"""
        
        violations = compliance_report.get('violations', [])
        if violations:
            text += "COMPLIANCE VIOLATIONS:\n"
            for i, v in enumerate(violations[:5], 1):
                text += f"{i}. {v.get('message', 'Unknown violation')}\n"
                text += f"   EO: {v.get('executive_order', 'Unknown')}\n\n"
        
        recommendations = risk_report.get('recommendations', [])
        if recommendations:
            text += "\nRECOMMENDATIONS:\n"
            for i, rec in enumerate(recommendations, 1):
                text += f"{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('action', 'Unknown')}\n"
                text += f"   {rec.get('description', 'No description')}\n\n"
        
        text += f"""
Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACTION REQUIRED: Please review this grant proposal and validate the AI-generated compliance analysis.

---
This is an automated message from the Grant Proposal Compliance System.
"""
        return text
    
    def _send_via_smtp(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email using SMTP (open-source fallback).
        
        Args:
            email_data: Email content and metadata
            
        Returns:
            Dictionary containing send status and details
        """
        logger.info(f"Sending email via SMTP to {email_data['to']}")
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data['subject']
            msg['From'] = email_data['from']
            msg['To'] = email_data['to']
            
            # Map priority to X-Priority header
            priority_map = {
                'high': '1',
                'normal': '3',
                'low': '5'
            }
            msg['X-Priority'] = priority_map.get(email_data['priority'], '3')
            
            # Attach plain text and HTML parts
            part1 = MIMEText(email_data['body_text'], 'plain')
            part2 = MIMEText(email_data['body_html'], 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect and send
            logger.info(f"Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.smtp_use_tls:
                    server.starttls()
                    logger.info("TLS enabled")
                
                server.login(self.smtp_username, self.smtp_password)
                logger.info(f"Authenticated as {self.smtp_username}")
                
                server.send_message(msg)
                logger.info("Email sent successfully via SMTP")
            
            return {
                'status': 'sent',
                'method': 'smtp',
                'message_id': f"smtp-{datetime.now().timestamp()}",
                'sent_at': datetime.now().isoformat(),
                'smtp_server': f"{self.smtp_host}:{self.smtp_port}"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise Exception("SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD in .env")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise Exception(f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Error sending via SMTP: {e}")
            raise
    def _send_via_graph_api(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Microsoft Graph API."""
        try:
            from msal import ConfidentialClientApplication
            
            logger.info("Acquiring access token from Microsoft Identity Platform...")
            logger.info("Acquiring access token from Microsoft Identity Platform...")
            
            # Get access token
            app = ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            # Request token with Mail.Send scope
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if not result or "access_token" not in result:
                error_desc = result.get('error_description', 'Unknown error') if result else 'No result returned'
                error_msg = f"Failed to acquire token: {error_desc}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            access_token = result["access_token"]
            logger.info("Access token acquired successfully")
            
            # Prepare email message
            message = {
                "message": {
                    "subject": email_data['subject'],
                    "body": {
                        "contentType": "HTML",
                        "content": email_data['body_html']
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": email_data['to']
                            }
                        }
                    ],
                    "importance": email_data['priority']
                },
                "saveToSentItems": "true"
            }
            
            # Send email
            endpoint = f"https://graph.microsoft.com/v1.0/users/{email_data['from']}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Sending email via Graph API to {email_data['to']}...")
            response = requests.post(endpoint, headers=headers, json=message)
            
            # Check for errors
            if response.status_code == 401:
                error_msg = "401 Unauthorized: Check that the Azure AD app has 'Mail.Send' application permission with admin consent"
                logger.error(error_msg)
                raise Exception(error_msg)
            elif response.status_code == 403:
                error_msg = "403 Forbidden: The application doesn't have permission to send mail on behalf of this user"
                logger.error(error_msg)
                raise Exception(error_msg)
            elif response.status_code == 404:
                error_msg = f"404 Not Found: User mailbox not found for {email_data['from']}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            response.raise_for_status()
            
            logger.info("Email sent successfully via Graph API")
            return {
                'status': 'sent',
                'method': 'graph_api',
                'message_id': response.headers.get('request-id', f"graph-{datetime.now().timestamp()}"),
                'sent_at': datetime.now().isoformat()
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Graph API HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Graph API error: {str(e)}")
            raise
    
    def _simulate_email_send(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate email sending for demo purposes."""
        logger.info("Simulating email send (demo mode)")
        
        # In demo mode, save email to local file
        email_log = {
            'timestamp': datetime.now().isoformat(),
            'to': email_data['to'],
            'from': email_data['from'],
            'subject': email_data['subject'],
            'priority': email_data['priority'],
            'body_preview': email_data['body_text'][:200] + '...',
            'status': 'simulated'
        }
        
        # Log to console for demo
        logger.info(f"[DEMO EMAIL] To: {email_data['to']}")
        logger.info(f"[DEMO EMAIL] Subject: {email_data['subject']}")
        logger.info(f"[DEMO EMAIL] Priority: {email_data['priority']}")
        
        return {
            'status': 'simulated',
            'method': 'demo',
            'message_id': f"demo-{datetime.now().timestamp()}",
            'sent_at': datetime.now().isoformat(),
            'log': email_log
        }
