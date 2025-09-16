# Healthcare Orchestrator Agent Project

A Python-based healthcare orchestrator that leverages Azure AI Foundry to create intelligent agents for healthcare-related tasks. This project demonstrates how to build and deploy AI agents using Azure's AI services with GPT models.

## Prerequisites

- Python 3.12 or higher
- Azure subscription with AI Foundry access
- Azure AI project with GPT model deployment

## Setup

1. Install Dependencies using Poetry (recommended): `poetry install`
1. Copy the example environment file: `cp .env.example .env`
1. Update the `.env` file with your LLM endpoint values

## Usage

### Running the Agent

```bash
python src/agents/sample.py
```

## Resources

- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-foundry/)