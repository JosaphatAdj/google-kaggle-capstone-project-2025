"""
Jira Tool - Automatic ticket creation and management
Integrated with RoboNest multi-agent system
"""

from typing import Dict, Any, Optional, List
from jira import JIRA
from jira.exceptions import JIRAError
import logging
from pathlib import Path
import sys

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class JiraTool:
    """
    Jira Tool for ticket management
    
    Usage:
        jira_tool = JiraTool()
        
        ticket = jira_tool.create_ticket(
            summary="Robot XR25-001 - Wheels blocked (E01)",
            description="Robot reported error E01...",
            issue_type="Bug",
            priority="Medium"
        )
    """
    
    def __init__(
        self,
        server: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: str = "ROB"
    ):
        """
        Initialize Jira Tool
        
        Args:
            server: Jira server URL (e.g., "https://yourcompany.atlassian.net")
            email: Your Jira account email
            api_token: Your Jira API token
            project_key: Project key (default: "ROB")
        
        Configuration:
            Set these in .env file:
            JIRA_SERVER=https://yourcompany.atlassian.net
            JIRA_EMAIL=your.email@company.com
            JIRA_API_TOKEN=your_api_token_here
            JIRA_PROJECT_KEY=ROB
        """
        # Load from environment if not provided
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.server = server if server is not None else os.getenv("JIRA_SERVER")
        self.email = email if email is not None else os.getenv("JIRA_EMAIL")
        self.api_token = api_token if api_token is not None else os.getenv("JIRA_API_TOKEN")
        self.project_key = project_key if project_key is not None else os.getenv("JIRA_PROJECT_KEY", "ROB")
        
        # Initialize Jira client
        try:
            self.jira = JIRA(
                server=self.server,
                basic_auth=(self.email, self.api_token)
            )
            logger.info(f"✅ Jira connected: {self.server}")
        except Exception as e:
            logger.error(f"❌ Jira connection failed: {e}")
            self.jira = None
    
    def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Jira ticket
        
        Args:
            summary: Ticket summary (title)
            description: Detailed description
            issue_type: Type (Bug, Task, Story, Incident)
            priority: Priority (Lowest, Low, Medium, High, Highest)
            labels: List of labels
            components: List of component names
            custom_fields: Custom field values
        
        Returns:
            {
                "success": bool,
                "ticket_id": str,
                "ticket_key": str,
                "url": str,
                "error": str (if failed)
            }
        
        Example:
            >>> result = jira_tool.create_ticket(
            ...     summary="Robot XR25-001 - Error E01",
            ...     description="Wheels blocked, needs cleaning",
            ...     priority="High",
            ...     labels=["robot", "error-e01", "xr25"]
            ... )
            >>> print(result["ticket_key"])
            ROBO-123
        """
        if not self.jira:
            return {
                "success": False,
                "error": "Jira client not initialized"
            }
        
        try:
            # Build issue dict
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            # Add optional fields
            if labels:
                issue_dict['labels'] = labels
            
            if components:
                issue_dict['components'] = [{'name': comp} for comp in components]
            
            if custom_fields:
                issue_dict.update(custom_fields)
            
            # Create issue
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            ticket_data = {
                "success": True,
                "ticket_id": new_issue.id,
                "ticket_key": new_issue.key,
                "url": f"{self.server}/browse/{new_issue.key}",
                "status": str(new_issue.fields.status)
            }
            
            logger.info(f"✅ Ticket created: {ticket_data['ticket_key']}")
            
            return ticket_data
            
        except JIRAError as e:
            logger.error(f"❌ Jira ticket creation failed: {e.text}")
            return {
                "success": False,
                "error": f"Jira error: {e.text}"
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_ticket(
        self,
        ticket_key: str,
        status: Optional[str] = None,
        comment: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a Jira ticket
        
        Args:
            ticket_key: Ticket key (e.g., "ROBO-123")
            status: New status (e.g., "In Progress", "Done")
            comment: Comment to add
            fields: Other fields to update
        
        Returns:
            {
                "success": bool,
                "ticket_key": str,
                "error": str (if failed)
            }
        
        Example:
            >>> result = jira_tool.update_ticket(
            ...     ticket_key="ROBO-123",
            ...     status="In Progress",
            ...     comment="Technical support investigating..."
            ... )
        """
        if not self.jira:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            issue = self.jira.issue(ticket_key)
            
            # Update fields
            if fields:
                issue.update(fields=fields)
            
            # Add comment
            if comment:
                self.jira.add_comment(issue, comment)
            
            # Transition status
            if status:
                transitions = self.jira.transitions(issue)
                transition_id = None
                
                for t in transitions:
                    if t['name'].lower() == status.lower():
                        transition_id = t['id']
                        break
                
                if transition_id:
                    self.jira.transition_issue(issue, transition_id)
                else:
                    logger.warning(f"⚠️ Status '{status}' not found for {ticket_key}")
            
            logger.info(f"✅ Ticket updated: {ticket_key}")
            
            return {
                "success": True,
                "ticket_key": ticket_key
            }
            
        except JIRAError as e:
            logger.error(f"❌ Jira update failed: {e.text}")
            return {"success": False, "error": f"Jira error: {e.text}"}
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_ticket(self, ticket_key: str) -> Dict[str, Any]:
        """
        Get ticket details
        
        Args:
            ticket_key: Ticket key (e.g., "ROBO-123")
        
        Returns:
            Ticket details or error
        """
        if not self.jira:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            issue = self.jira.issue(ticket_key)
            
            return {
                "success": True,
                "ticket_key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": str(issue.fields.status),
                "priority": str(issue.fields.priority),
                "assignee": str(issue.fields.assignee) if issue.fields.assignee else None,
                "created": str(issue.fields.created),
                "updated": str(issue.fields.updated),
                "url": f"{self.server}/browse/{issue.key}"
            }
            
        except JIRAError as e:
            logger.error(f"❌ Ticket not found: {e.text}")
            return {"success": False, "error": f"Ticket not found: {e.text}"}
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# TOOL FUNCTIONS (for agents)
# ============================================================

# Global instance (initialized on first use)
_jira_tool_instance = None

def get_jira_tool() -> JiraTool:
    """Get or create Jira tool instance"""
    global _jira_tool_instance
    if _jira_tool_instance is None:
        _jira_tool_instance = JiraTool()
    return _jira_tool_instance


def create_jira_ticket(
    summary: str,
    description: str,
    priority: str = "Medium",
    labels: Optional[List[str]] = None
) -> dict:
    """
    Create Jira ticket (tool function for agents)
    
    Args:
        summary: Ticket summary
        description: Detailed description
        priority: Priority level
        labels: Labels to add
    
    Returns:
        Result dictionary
    """
    jira_tool = get_jira_tool()
    return jira_tool.create_ticket(
        summary=summary,
        description=description,
        priority=priority,
        labels=labels or []
    )


def update_jira_ticket(
    ticket_key: str,
    status: Optional[str] = None,
    comment: Optional[str] = None
) -> dict:
    """
    Update Jira ticket (tool function for agents)
    
    Args:
        ticket_key: Ticket key (e.g., "ROBO-123")
        status: New status
        comment: Comment to add
    
    Returns:
        Result dictionary
    """
    jira_tool = get_jira_tool()
    return jira_tool.update_ticket(
        ticket_key=ticket_key,
        status=status,
        comment=comment
    )


# ============================================================
# EXAMPLE USAGE & TESTING
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("JIRA TOOL DEMO")
    print("="*60)
    print("\n⚠️  Make sure to set these in your .env file:")
    print("   JIRA_SERVER=https://yourcompany.atlassian.net")
    print("   JIRA_EMAIL=your.email@company.com")
    print("   JIRA_API_TOKEN=your_api_token_here")
    print("   JIRA_PROJECT_KEY=ROBO")
    
    # Initialize
    jira_tool = JiraTool()
    
    if not jira_tool.jira:
        print("\n❌ Jira not configured. Please set environment variables.")
        print("   Or pass credentials directly:")
        print("   jira_tool = JiraTool(")
        print("       server='https://yourcompany.atlassian.net',")
        print("       email='your.email@company.com',")
        print("       api_token='your_token'")
        print("   )")
        exit(1)
    
    print("\n" + "="*60)
    print("TEST 1: Create ticket")
    print("="*60)
    
    result = jira_tool.create_ticket(
        summary="Robot XR25-001 - Error E01 (Wheels blocked)",
        description="""
**Robot ID:** XR25-001
**Error Code:** E01
**Severity:** Medium
**Description:** Robot wheels are blocked, unable to move.

**Diagnostic Data:**
- Battery: 85%
- Temperature: 45°C
- Location: Zone A (x: 10, y: 20)

**Recommended Action:**
Clean wheels and check for obstacles.
        """.strip(),
        priority="High",
        labels=["robot", "error-e01", "xr25", "auto-created"]
    )
    
    if result["success"]:
        print(f"✅ Ticket created: {result['ticket_key']}")
        print(f"   URL: {result['url']}")
        
        ticket_key = result["ticket_key"]
        
        print("\n" + "="*60)
        print("TEST 2: Update ticket")
        print("="*60)
        
        update_result = jira_tool.update_ticket(
            ticket_key=ticket_key,
            comment="Technical support is investigating the issue."
        )
        
        if update_result["success"]:
            print(f"✅ Ticket updated: {ticket_key}")
        
        print("\n" + "="*60)
        print("TEST 3: Get ticket")
        print("="*60)
        
        get_result = jira_tool.get_ticket(ticket_key)
        
        if get_result["success"]:
            print(f"✅ Ticket retrieved: {ticket_key}")
            print(f"   Status: {get_result['status']}")
            print(f"   Priority: {get_result['priority']}")
    else:
        print(f"❌ Ticket creation failed: {result['error']}")
    
    print("\n" + "="*60)
    print("✅ JIRA TOOL DEMO COMPLETE")
    print("="*60)