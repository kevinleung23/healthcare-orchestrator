import os
import time

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions, ListSortOrder
from azure.identity import DefaultAzureCredential

from dotenv import load_dotenv
load_dotenv()

# Replace these with your Azure AI Foundry project details
AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT")
AZURE_PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
AZURE_PROJECT_KEY = os.getenv("AZURE_PROJECT_KEY")
GPT_DEPLOYMENT_NAME = os.getenv("OPENAI_MODEL")


# Create a project client
project_client = AIProjectClient(
    endpoint=f"{AZURE_PROJECT_ENDPOINT}/projects/{AZURE_PROJECT_NAME}",
    credential=DefaultAzureCredential()
)

with project_client:
    agents_client = project_client.agents

    agent = agents_client.create_agent(
        model=GPT_DEPLOYMENT_NAME,
        name="sample-agent",
        instructions="You are a helpful assistant that tells jokes.",
    )
    print(f"✅ Created agent: {agent.name} | id: {agent.id}")

    # [START create_thread_and_run]
    # Prepare the initial user message
    initial_message = ThreadMessageOptions(role="user", content="Hello! Can you tell me a joke?")

    # Create a new thread and immediately start a run on it
    run = agents_client.create_thread_and_run(
        agent_id=agent.id,
        thread=AgentThreadCreationOptions(messages=[initial_message]),
    )
    # [END create_thread_and_run]

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(1)
        run = agents_client.runs.get(thread_id=run.thread_id, run_id=run.id)
        print(f"Run status: {run.status}")

    if run.status == "failed":
        print(f"Run error: {run.last_error}")

    # List all messages in the thread, in ascending order of creation
    messages = agents_client.messages.list(thread_id=run.thread_id, order=ListSortOrder.ASCENDING)

    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role}: {last_text.text.value}")

    # clean up
    agents_client.delete_agent(agent.id)
    print("🧹 Cleaned up all resources")
    print(f"Deleted agent: {agent.name}")
