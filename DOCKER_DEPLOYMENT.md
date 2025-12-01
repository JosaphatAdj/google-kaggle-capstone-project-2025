# ============================================================
# ROBONEST - DOCKER DEPLOYMENT GUIDE
# ============================================================

## Quick Start

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
- `GOOGLE_API_KEY` - Your Gemini API key

**Optional (for full features):**
- `JIRA_*` - For ticket creation
- `GMAIL_*` - For HITL email notifications

### 2. Build Images

```bash
# Build all services
docker-compose build

# Or build individually
docker-compose build support-system
docker-compose build robot
docker-compose build simulator
```

### 3. Launch System

```bash
# Start support + robot (production)
docker-compose up -d

# Start with simulator (testing)
docker-compose --profile testing up -d

# View logs
docker-compose logs -f
```

### 4. Verify Health

```bash
# Check service status
docker-compose ps

# Expected:
# robonest-support    Up (healthy)
# robonest-robot      Up (healthy)

# Test A2A endpoint
curl http://localhost:8000/.well-known/agent-card.json

# Test robot status
curl http://localhost:8001/status
```

---

## Architecture

```
┌─────────────────────┐         
│  support-system     │ :8000   
│  - Alert Receiver   │         
│  - COO              │         
│  - Tech Support     │         
│  - ChromaDB         │         
└──────────┬──────────┘         
           │ Docker Network     
           │ (robonest-net)     
┌──────────▼──────────┐         
│  robot              │ :8001   
│  - main_agent       │         
│  - A2A client       │         
└──────────┬──────────┘         
           │                    
┌──────────▼──────────┐         
│  simulator          │ :8002   
│  (optional)         │         
└─────────────────────┘         
```

---

## Environment Variables

See `.env.example` for full list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Gemini API key |
| `JIRA_SERVER` | ⚪ Optional | Jira URL for tickets |
| `JIRA_API_TOKEN` | ⚪ Optional | Jira auth token |
| `GMAIL_SENDER_EMAIL` | ⚪ Optional | Email for HITL |
| `GMAIL_SENDER_PASSWORD` | ⚪ Optional | Gmail App Password |
| `ROBOT_ID` | ⚪ Optional | Robot identifier (default: XR25-001) |

---

## Testing

### Run E03 Demo (Low Battery)

```bash
# Access simulator container
docker-compose --profile testing exec simulator python start_simulator.py

# Or send direct HTTP request
curl -X POST http://localhost:8001/simulate/error/E03
```

**Expected:**
- Alert sent via A2A
- Solution generated: `["charge_battery", "return_to_dock"]`
- Jira ticket created (if configured)
- Actions executed
- Error resolved ✅

### Run E07 Demo (Critical HITL)

```bash
curl -X POST http://localhost:8001/simulate/error/E07
```

**Expected:**
- Critical alert escalated
- Email sent (if Gmail configured)
- Jira CRITICAL ticket created
- Robot waits for HITL ⏳

---

## Volumes

- `./rag/chroma_db:/app/rag/chroma_db:ro` - ChromaDB (read-only)
- `./logs:/app/logs` - Application logs

---

## Networks

- `robonest-net` - Bridge network for inter-service communication

---

## Troubleshooting

### Support System Not Healthy

```bash
# Check logs
docker-compose logs support-system

# Common issue: Missing GOOGLE_API_KEY
# Solution: Add to .env file
```

### Robot Cannot Connect to Support

```bash
# Verify network
docker network inspect robonest-net

# Verify support is running
curl http://localhost:8000/.well-known/agent-card.json

# Check robot logs
docker-compose logs robot
```

### ChromaDB Not Found

```bash
# Verify volume mount
docker-compose exec support-system ls -la /app/rag/chroma_db

# If empty, ensure rag/chroma_db exists locally
ls -la rag/chroma_db/
```

---

## Production Deployment

### Security Recommendations

1. **Use secrets management:**
   ```bash
   docker secret create google_api_key /path/to/key.txt
   ```

2. **Enable TLS:**
   - Add reverse proxy (nginx)
   - Configure SSL certificates

3. **Resource limits:**
   ```yaml
   services:
     support-system:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Scaling

```bash
# Scale robot instances
docker-compose up -d --scale robot=3

# Note: Each robot needs unique ROBOT_ID
```

---

## Stopping Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop robot
```

---

## Monitoring

```bash
# Watch logs in real-time
docker-compose logs -f --tail=100

# Check resource usage
docker stats

# Restart unhealthy services
docker-compose restart support-system
```

---

**For more information, see [README.md](README.md)**
