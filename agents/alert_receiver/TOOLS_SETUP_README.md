# 🛠️ Tools & Alert Receiver - Setup Guide

## 📋 What Was Created

### ✅ **1. Jira Tool** (`tools/jira/jira_tool.py`)
- Automatic ticket creation
- Ticket updates and comments
- Full Jira API integration
- **460 lines**

### ✅ **2. Gmail Tool** (`tools/gmail/gmail_tool.py`)  
- HITL escalation emails
- HTML email templates
- Division email routing
- **450 lines**

### ✅ **3. Alert Receiver Agent** (`agents/alert_receiver/alert_receiver_agent.py`)
- REST API for robot alerts (PORT 8000)
- RAG-powered error classification
- Message Bus integration
- Audit logging
- **550 lines**

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
pip install jira python-dotenv fastapi uvicorn pydantic
```

### Step 2: Configure Jira

1. **Get Jira API Token:**
   - Go to: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token

2. **Add to `.env`:**
   ```env
   JIRA_SERVER=https://yourcompany.atlassian.net
   JIRA_EMAIL=your.email@company.com
   JIRA_API_TOKEN=paste_your_token_here
   JIRA_PROJECT_KEY=ROBO
   ```

3. **Test Jira:**
   ```bash
   python tools/jira/jira_tool.py
   ```

### Step 3: Configure Gmail

1. **Enable 2-Factor Authentication** on your Google account

2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "RoboNest Alerts"
   - Copy the 16-character password

3. **Add to `.env`:**
   ```env
   GMAIL_SENDER_EMAIL=alerts@robonest.com
   GMAIL_SENDER_PASSWORD=paste_app_password_here
   ```

4. **Test Gmail:**
   ```bash
   python tools/gmail/gmail_tool.py
   ```

### Step 4: Start Alert Receiver

```bash
# Start the Alert Receiver API
python agents/alert_receiver/alert_receiver_agent.py
```

**API will be available at:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 📡 Robot Alert Schema

### What the Robot Must Send

```python
POST http://localhost:8000/alerts/robot-issue
Content-Type: application/json

{
    "robot_id": "XR25-001",
    "error_code": "E01",
    "severity": "medium",  # low, medium, high, critical
    "timestamp": "2024-01-15T14:30:00Z",
    "description": "Wheels blocked, robot unable to move",
    "sensor_data": {
        "battery_level": 85,
        "temperature": 45,
        "location": {"x": 10, "y": 20}
    }
}
```

### Response

```json
{
    "status": "success",
    "task_id": "ALERT-XR25-001-1642253400",
    "urgency": "medium",
    "forwarded_to": "coo_agent"
}
```

---

## 🔄 Complete Workflow

```
1. 🤖 Robot (PORT 8001)
   └─ Detects error E01
   └─ POST /alerts/robot-issue
      ↓
2. 🚨 Alert Receiver (PORT 8000)
   └─ Receives alert
   └─ Queries RAG for error code
   └─ Classifies urgency
   └─ Forwards to COO via MessageBus
      ↓
3. 👑 COO Agent
   └─ Receives formatted alert
   └─ Consults RAG for workflow
   └─ Delegates to Technical Support
      ↓
4. 🛠️ Technical Support Agent
   └─ Creates Jira ticket
   └─ Prepares procedure
   └─ If critical → Sends HITL email
```

---

## 🧪 Testing

### Test 1: Jira Tool

```bash
python tools/jira/jira_tool.py
```

**Expected output:**
```
✅ Ticket created: ROBO-123
   URL: https://yourcompany.atlassian.net/browse/ROBO-123
✅ Ticket updated: ROBO-123
✅ Ticket retrieved: ROBO-123
```

### Test 2: Gmail Tool

```bash
python tools/gmail/gmail_tool.py
```

**Expected output:**
```
✅ Escalation email sent to support@robonest.com
   Subject: [HITL] [CRITICAL] Robot XR25-001 - Error E07
```

### Test 3: Alert Receiver

**Start server:**
```bash
python agents/alert_receiver/alert_receiver_agent.py
```

**Send test alert:**
```bash
curl -X POST http://localhost:8000/alerts/robot-issue \
  -H "Content-Type: application/json" \
  -d '{
    "robot_id": "XR25-001",
    "error_code": "E01",
    "severity": "medium",
    "description": "Wheels blocked",
    "sensor_data": {
      "battery_level": 85,
      "temperature": 45
    }
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "task_id": "ALERT-XR25-001-...",
  "urgency": "medium",
  "forwarded_to": "coo_agent"
}
```

---

## 🎯 Error Code Classification

### Critical (Immediate Escalation + Email)
- **E07**: Battery swollen / Fire hazard
- **E08**: Firmware corruption  
- **E09**: Safety sensor failure
- **Any temperature > 60°C**

### High Priority
- **E01**: Wheels blocked
- **E02**: Navigation failure
- **E03**: Charging issues

### Medium Priority
- **E04**: Software glitches
- **E05**: Performance issues

---

## 📧 Email Recipients (by Division)

```python
# Automatically handled by Gmail Tool
DIVISION_EMAILS = {
    "support": "support@robonest.com",
    "marketing": "marketing@robonest.com",
    "hr": "hr@robonest.com",
    "coordinator": "ops@robonest.com",
    "ops": "ops@robonest.com"
}
```

**Usage in code:**
```python
# Send to support division
gmail_tool.send_escalation(
    to="support",  # Auto-resolves to support@robonest.com
    issue_data={...}
)

# Or use email directly
gmail_tool.send_escalation(
    to="manager@robonest.com",
    issue_data={...}
)
```

---

## 🔧 Tool Functions (for Agents)

### Jira Tool Functions

```python
from tools.jira.jira_tool import create_jira_ticket, update_jira_ticket

# Create ticket
result = create_jira_ticket(
    summary="Robot XR25-001 - Error E01",
    description="Detailed description...",
    priority="High",
    labels=["robot", "error-e01"]
)

# Update ticket
update_jira_ticket(
    ticket_key="ROBO-123",
    status="In Progress",
    comment="Investigating..."
)
```

### Gmail Tool Functions

```python
from tools.gmail.gmail_tool import send_escalation_email

# Send escalation
send_escalation_email(
    division="support",  # or email address
    issue_data={
        "robot_id": "XR25-001",
        "error_code": "E07",
        "severity": "critical",
        "description": "Battery swollen",
        "jira_ticket": "ROBO-123"
    },
    escalation_type="HITL"
)
```

---

## 📊 Integration with Agents

### Example: Technical Support Agent

```python
from agents.base import BaseAgent
from tools.jira.jira_tool import create_jira_ticket
from tools.gmail.gmail_tool import send_escalation_email

class TechnicalSupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="tech_support_001",
            agent_type="technical_support",
            department="support"
        )
        
        # Add tools
        self.add_tool(create_jira_ticket)
        self.add_tool(send_escalation_email)
    
    async def process_task(self, task_description: str, context=None):
        # 1. Create Jira ticket
        ticket = create_jira_ticket(
            summary=f"Robot {context['robot_id']} - {context['error_code']}",
            description=task_description,
            priority="High"
        )
        
        # 2. If critical, escalate via email
        if context.get("severity") == "critical":
            send_escalation_email(
                division="support",
                issue_data={
                    **context,
                    "jira_ticket": ticket["ticket_key"]
                }
            )
        
        return {"status": "success", "ticket": ticket["ticket_key"]}
```

---

## 🐛 Troubleshooting

### Jira Connection Failed

**Error:** `Jira connection failed: 401 Unauthorized`

**Solution:**
1. Verify API token is correct
2. Check email matches Jira account
3. Ensure you have project permissions

### Gmail Auth Failed

**Error:** `Authentication failed`

**Solution:**
1. Use App Password, NOT regular password
2. Enable 2-Factor Authentication first
3. Generate new App Password if needed

### Alert Receiver Port Conflict

**Error:** `Port 8000 already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

## 📁 File Structure

```
robonest-system/
├── tools/
│   ├── jira/
│   │   ├── __init__.py
│   │   └── jira_tool.py          ✅ NEW
│   └── gmail/
│       ├── __init__.py
│       └── gmail_tool.py          ✅ NEW
│
├── agents/
│   └── alert_receiver/
│       ├── __init__.py
│       └── alert_receiver_agent.py ✅ NEW
│
├── .env.example                    ✅ UPDATED
└── TOOLS_SETUP_README.md           ✅ NEW
```

---

## ✅ Checklist

Before first test:
- [ ] Jira configured and tested
- [ ] Gmail configured and tested  
- [ ] Alert Receiver running on port 8000
- [ ] COO Agent running
- [ ] Message Bus started
- [ ] RAG system indexed
- [ ] Environment variables set

---

## 🚀 Next Steps

1. **Test Jira integration**
   ```bash
   python tools/jira/jira_tool.py
   ```

2. **Test Gmail integration**
   ```bash
   python tools/gmail/gmail_tool.py
   ```

3. **Start Alert Receiver**
   ```bash
   python agents/alert_receiver/alert_receiver_agent.py
   ```

4. **Send test alert**
   ```bash
   curl -X POST http://localhost:8000/alerts/robot-issue \
     -H "Content-Type: application/json" \
     -d '{"robot_id":"XR25-001","error_code":"E01",...}'
   ```

5. **Verify workflow:**
   - Check Jira for new ticket
   - Check email for escalation (if critical)
   - Check logs for full trace

---

## 📞 Support

**Issues?**
- Check `.env` file is configured
- Verify API credentials
- Check logs in `logs/` directory
- Test each tool individually first

**Ready for full E2E test!** 🎉