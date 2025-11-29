from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner

# Créer remote agent
support = RemoteA2aAgent(
    name="alert_receiver",
    agent_card="http://localhost:8000/.well-known/agent-card.json"
)

# Créer agent simple
robot = LlmAgent(
    model=Gemini(model="gemini-2.0-flash-lite"),
    name="robot",
    instruction="Contact alert_receiver sub-agent for error E01",
    sub_agents=[support]
)

# Run
runner = Runner(robot)
async for event in runner.run_async("XR25-001", "test", "Error E01 detected"):
    print(event)