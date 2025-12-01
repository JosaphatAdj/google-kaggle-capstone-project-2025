"""
Gmail Tool - Email notifications for HITL escalations
Integrated with RoboNest multi-agent system
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class GmailTool:
    """
    Gmail Tool for sending escalation emails
    
    Division Emails:
    - support@robonest.com - Support division
    - marketing@robonest.com - Marketing division  
    - hr@robonest.com - HR division
    - ops@robonest.com - Operations (COO)
    
    Usage:
        gmail_tool = GmailTool()
        
        gmail_tool.send_escalation(
            to="support@robonest.com",
            subject="URGENT: Robot XR25-001 - Battery Swollen",
            issue_data={...}
        )
    """
    
    DIVISION_EMAILS = os.getenv("DIVISION_EMAILS", "")
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None
    ):
        """
        Initialize Gmail Tool
        
        Args:
            smtp_server: SMTP server (default: smtp.gmail.com)
            smtp_port: SMTP port (default: 587)
            sender_email: Sender email address
            sender_password: App password (not regular password!)
        
        Configuration:
            Set these in .env file:
            GMAIL_SMTP_SERVER=smtp.gmail.com
            GMAIL_SMTP_PORT=587
            GMAIL_SENDER_EMAIL=alerts@robonest.com
            GMAIL_SENDER_PASSWORD=your_app_password_here
        
        Note:
            Use App Password, not regular password!
            https://support.google.com/accounts/answer/185833
        """
        
        
        self.smtp_server = smtp_server or os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("GMAIL_SMTP_PORT", "587"))
        self.sender_email = sender_email or os.getenv("GMAIL_SENDER_EMAIL")
        self.sender_password = sender_password or os.getenv("GMAIL_SENDER_PASSWORD")
        
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Gmail credentials not configured")
        else:
            logger.info(f"✅ Gmail configured: {self.sender_email}")
    
    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email
        
        Args:
            to: Recipient email
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (fallback)
            cc: CC recipients
            attachments: File paths to attach
        
        Returns:
            {
                "success": bool,
                "message_id": str,
                "error": str (if failed)
            }
        """
        if not self.sender_email or not self.sender_password:
            return {
                "success": False,
                "error": "Gmail credentials not configured"
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            
            msg.attach(MIMEText(body_html, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                
                recipients = [to] + (cc or [])
                server.sendmail(self.sender_email, recipients, msg.as_string())
            
            logger.info(f"✅ Email sent to {to}")
            
            return {
                "success": True,
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_escalation(
        self,
        to: str,
        issue_data: Dict[str, Any],
        escalation_type: str = "HITL",
        cc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send escalation email using template
        
        Args:
            to: Recipient email or division name
            issue_data: Issue details
            escalation_type: HITL, technical, manager
            cc: CC recipients
        
        Returns:
            Result dictionary
        
        Example:
            >>> result = gmail_tool.send_escalation(
            ...     to="support",  # or "support@robonest.com"
            ...     issue_data={
            ...         "robot_id": "XR25-001",
            ...         "error_code": "E07",
            ...         "severity": "critical",
            ...         "description": "Battery swollen",
            ...         "jira_ticket": "ROBO-123"
            ...     },
            ...     escalation_type="HITL"
            ... )
        """
        # Resolve division email
        if to in self.DIVISION_EMAILS:
            to_email = self.DIVISION_EMAILS[to]
        else:
            to_email = to
        
        # Generate subject
        severity = issue_data.get("severity", "medium").upper()
        robot_id = issue_data.get("robot_id", "Unknown")
        error_code = issue_data.get("error_code", "Unknown")
        
        subject = f"[{escalation_type}] [{severity}] Robot {robot_id} - Error {error_code}"
        
        # Generate HTML body
        body_html = self._generate_escalation_html(issue_data, escalation_type)
        
        # Generate plain text fallback
        body_text = self._generate_escalation_text(issue_data, escalation_type)
        
        # Send
        return self.send_email(
            to=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            cc=cc
        )
    
    def _generate_escalation_html(
        self,
        issue_data: Dict[str, Any],
        escalation_type: str
    ) -> str:
        """Generate HTML email body"""
        
        robot_id = issue_data.get("robot_id", "Unknown")
        error_code = issue_data.get("error_code", "Unknown")
        severity = issue_data.get("severity", "medium").upper()
        description = issue_data.get("description", "No description provided")
        jira_ticket = issue_data.get("jira_ticket")
        timestamp = issue_data.get("timestamp", datetime.utcnow().isoformat())
        
        # Sensor data
        sensor_data = issue_data.get("sensor_data", {})
        battery = sensor_data.get("battery_level", "N/A")
        temperature = sensor_data.get("temperature", "N/A")
        
        # Diagnostic info
        diagnosis = issue_data.get("diagnosis", "Automated diagnosis pending")
        recommended_actions = issue_data.get("recommended_actions", [])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ background-color: #f5f5f5; padding: 20px; margin-top: 20px; border-radius: 5px; }}
        .field {{ margin-bottom: 15px; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ color: #333; }}
        .actions {{ background-color: #fff3cd; padding: 15px; margin-top: 20px; border-left: 4px solid #ffc107; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
        .critical {{ background-color: #d32f2f !important; }}
        .high {{ background-color: #f57c00; }}
        .medium {{ background-color: #ffa726; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header {'critical' if severity == 'CRITICAL' else severity.lower()}">
            <h1>🚨 Escalation Required: {escalation_type}</h1>
            <p>Severity: {severity}</p>
        </div>
        
        <div class="content">
            <h2>Robot Issue Details</h2>
            
            <div class="field">
                <span class="label">Robot ID:</span>
                <span class="value">{robot_id}</span>
            </div>
            
            <div class="field">
                <span class="label">Error Code:</span>
                <span class="value">{error_code}</span>
            </div>
            
            <div class="field">
                <span class="label">Timestamp:</span>
                <span class="value">{timestamp}</span>
            </div>
            
            <div class="field">
                <span class="label">Description:</span>
                <div class="value">{description}</div>
            </div>
            
            <h3>Sensor Data</h3>
            <div class="field">
                <span class="label">Battery Level:</span>
                <span class="value">{battery}%</span>
            </div>
            
            <div class="field">
                <span class="label">Temperature:</span>
                <span class="value">{temperature}°C</span>
            </div>
            
            <h3>Diagnosis</h3>
            <div class="field">
                <div class="value">{diagnosis}</div>
            </div>
"""
        
        # Add recommended actions
        if recommended_actions:
            html += """
            <div class="actions">
                <h3>Recommended Actions</h3>
                <ul>
"""
            for action in recommended_actions:
                html += f"                    <li>{action}</li>\n"
            
            html += """
                </ul>
            </div>
"""
        
        # Add Jira ticket link
        if jira_ticket:
            html += f"""
            <div class="field">
                <span class="label">Jira Ticket:</span>
                <span class="value"><a href="https://yourcompany.atlassian.net/browse/{jira_ticket}">{jira_ticket}</a></span>
            </div>
"""
        
        html += """
        </div>
        
        <div class="footer">
            <p>This is an automated escalation from the RoboNest Multi-Agent System.</p>
            <p>Please take appropriate action as soon as possible.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_escalation_text(
        self,
        issue_data: Dict[str, Any],
        escalation_type: str
    ) -> str:
        """Generate plain text email body"""
        
        robot_id = issue_data.get("robot_id", "Unknown")
        error_code = issue_data.get("error_code", "Unknown")
        severity = issue_data.get("severity", "medium").upper()
        description = issue_data.get("description", "No description")
        
        text = f"""
ESCALATION REQUIRED: {escalation_type}
Severity: {severity}

Robot ID: {robot_id}
Error Code: {error_code}
Description: {description}

This is an automated escalation from RoboNest.
Please take appropriate action.
"""
        
        return text.strip()


# ============================================================
# TOOL FUNCTIONS (for agents)
# ============================================================

_gmail_tool_instance = None

def get_gmail_tool() -> GmailTool:
    """Get or create Gmail tool instance"""
    global _gmail_tool_instance
    if _gmail_tool_instance is None:
        _gmail_tool_instance = GmailTool()
    return _gmail_tool_instance


def send_escalation_email(
    division: str,
    issue_data: dict,
    escalation_type: str = "HITL"
) -> dict:
    """
    Send escalation email (tool function for agents)
    
    Args:
        division: Division name (support, marketing, hr, ops)
        issue_data: Issue details
        escalation_type: Escalation type
    
    Returns:
        Result dictionary
    """
    gmail_tool = get_gmail_tool()
    return gmail_tool.send_escalation(
        to=division,
        issue_data=issue_data,
        escalation_type=escalation_type
    )


# ============================================================
# EXAMPLE USAGE & TESTING
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("GMAIL TOOL DEMO")
    print("="*60)
    print("\n⚠️  Make sure to set these in your .env file:")
    print("   GMAIL_SENDER_EMAIL=alerts@robonest.com")
    print("   GMAIL_SENDER_PASSWORD=your_app_password")
    print("\n   Note: Use App Password, not regular password!")
    print("   https://support.google.com/accounts/answer/185833")
    
    # Initialize
    gmail_tool = GmailTool()
    
    if not gmail_tool.sender_email or not gmail_tool.sender_password:
        print("\n❌ Gmail not configured. Set environment variables first.")
        exit(1)
    
    print("\n" + "="*60)
    print("TEST: Send escalation email")
    print("="*60)
    
    # Test escalation
    result = gmail_tool.send_escalation(
        to="support",  # Will resolve to support@robonest.com
        issue_data={
            "robot_id": "XR25-001",
            "error_code": "E07",
            "severity": "critical",
            "description": "Battery swollen, potential fire hazard",
            "timestamp": "2024-01-15T14:30:00Z",
            "sensor_data": {
                "battery_level": 95,
                "temperature": 65
            },
            "diagnosis": "Battery overheating detected. Immediate action required.",
            "recommended_actions": [
                "Stop robot operation immediately",
                "Disconnect power source",
                "Isolate robot from flammable materials",
                "Contact customer for retrieval"
            ],
            "jira_ticket": "ROBO-123"
        },
        escalation_type="HITL"
    )
    
    if result["success"]:
        print(f"✅ Escalation email sent to {result['to']}")
        print(f"   Subject: {result['subject']}")
    else:
        print(f"❌ Email failed: {result['error']}")
    
    print("\n" + "="*60)
    print("✅ GMAIL TOOL DEMO COMPLETE")
    print("="*60)