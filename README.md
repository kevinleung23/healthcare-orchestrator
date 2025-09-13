# Healthcare Orchestrator Agent Project

A Python-based healthcare orchestrator that leverages Azure AI Foundry to create intelligent agents for healthcare-related tasks. This project demonstrates how to build and deploy AI agents using Azure's AI services with GPT models.

## Prerequisites

- Python 3.11 or higher
- Azure CLI
- Azure subscription with AI Foundry access
- Azure AI project with GPT model deployment

## Setup

1. Install Dependencies using Poetry (recommended): `poetry install`
1. Copy the example environment file: `cp .env.example .env`
1. Update the `.env` file with your Azure AI Foundry project details
1. Login to Azure CLI: `az login`
    - Or configure your Azure credentials using environment variables

## Usage

### Running the Agent

```bash
python src/healthcare_orchestrator/agent.py
```

## Resources

- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-foundry/)
- [Azure SDK for Python Samples](https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_1.0.0/sdk/ai/azure-ai-projects/samples)
