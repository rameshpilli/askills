# Claude Agent SDK Docker Environment

A Docker-based HTTP service for running the Claude Agent SDK with skills.

## Project Structure

```
AgentSkills/
├── Dockerfile
├── pyproject.toml
├── app/
│   └── main.py           # FastAPI HTTP service
├── skills/               # 17 skills from anthropics/skills
├── testdata/             # Sample PDFs and Excel files for testing
│   ├── earnings_report_q3_2024.pdf
│   ├── product_pricing_2024.pdf
│   ├── pricing_calculator.xlsx
│   └── financial_summary_2024.xlsx
└── k8s/                  # Kubernetes manifests
    ├── deployment.yaml
    ├── service.yaml
    └── secret.yaml
```

## Quick Start

### 1. Build the Image

```bash
docker build -t claude-agent-dev .
```

### 2. Run the Container

```bash
docker run -d --rm \
  -p 8080:8080 \
  -e ANTHROPIC_API_KEY=your_api_key_here \
  claude-agent-dev
```

### 3. Test the API

Health check:
```bash
curl http://localhost:8080/health
```

Send a chat message:
```bash
curl http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What skills are available?"}'
```

Test with a PDF skill:
```bash
curl http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Use the pdf skill to describe what it does."}'
```

## HTTP API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check, returns skills count |
| `/chat` | POST | Send message to agent, get reply |

### POST /chat

Request:
```json
{
  "message": "Your prompt here"
}
```

Response:
```json
{
  "reply": "Agent response text"
}
```

## Included Skills

From [anthropics/skills](https://github.com/anthropics/skills):

| Skill | Description |
|-------|-------------|
| `pdf` | PDF manipulation and form filling |
| `xlsx` | Excel spreadsheet handling |
| `pptx` | PowerPoint presentations |
| `docx` | Word documents |
| `frontend-design` | Frontend UI/UX design |
| `canvas-design` | Canvas-based design |
| `algorithmic-art` | Generative art |
| `mcp-builder` | MCP server builder |
| `skill-creator` | Create new skills |
| `webapp-testing` | Web app testing |
| `web-artifacts-builder` | Web artifacts |
| `brand-guidelines` | Brand identity |
| `internal-comms` | Internal communications |
| `slack-gif-creator` | Slack GIFs |
| `theme-factory` | Theme generation |
| `doc-coauthoring` | Document collaboration |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Anthropic |
| `LLM_GATEWAY_URL` | No | Custom gateway URL |
| `CLAUDE_AGENT_CWD` | No | Working directory (default: `/app`) |
| `CLAUDE_AGENT_SKILLS_DIR` | No | Skills source (default: `/app/skills`) |

## Test Data

Sample files are included in `testdata/` for testing skills:

- `earnings_report_q3_2024.pdf` - Q3 earnings report with financial tables
- `product_pricing_2024.pdf` - Product pricing guide
- `pricing_calculator.xlsx` - Pricing tiers and revenue calculator
- `financial_summary_2024.xlsx` - Quarterly financial data

To regenerate test data:
```bash
cd testdata && python create_samples.py
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Your MacBook (Host)                                        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker Desktop                                       │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Container (python:3.11-slim)                   │  │  │
│  │  │                                                 │  │  │
│  │  │  • Python 3.11 + FastAPI + uvicorn             │  │  │
│  │  │  • Claude Agent SDK                             │  │  │
│  │  │  • /app/.claude/skills/* (skill definitions)    │  │  │
│  │  │  • /bin/bash (for Bash tool)                    │  │  │
│  │  │                                                 │  │  │
│  │  │  Skills execute HERE                            │  │  │
│  │  └──────────────────┬──────────────────────────────┘  │  │
│  └─────────────────────┼─────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ HTTPS (API calls only)
                         ▼
              ┌─────────────────────┐
              │  Claude API         │
              │  (or your gateway)  │
              └─────────────────────┘
```

**What stays inside the container:**
- Skill loading (reading SKILL.md)
- Bash commands
- File read/write operations
- Python script execution
- All filesystem access

**What goes outside:**
- Only the API calls to Claude (model inference)

## Kubernetes Deployment

### 1. Build and push image

```bash
docker build -t YOUR_REGISTRY/claude-agent-sdk-skills:v1 .
docker push YOUR_REGISTRY/claude-agent-sdk-skills:v1
```

### 2. Create the secret

```bash
# Encode your API key
echo -n "your-api-key" | base64

# Edit k8s/secret.yaml with the encoded value, then apply
kubectl apply -f k8s/secret.yaml
```

### 3. Deploy

```bash
# Update k8s/deployment.yaml with your image registry
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 4. Test in cluster

```bash
# Port forward to test locally
kubectl port-forward deploy/claude-agent-skills 8080:8080

# Send a request
curl http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What skills are available?"}'
```

### Kubernetes manifests included

- `k8s/deployment.yaml` - Deployment with health probes and resource limits
- `k8s/service.yaml` - ClusterIP service on port 80
- `k8s/secret.yaml` - Template for API key secret

### Resource recommendations

| Setting | Value |
|---------|-------|
| CPU requests | 1 |
| CPU limits | 2 |
| Memory requests | 2Gi |
| Memory limits | 4Gi |

## Local vs Cluster Deployment

### Local

You run the Docker container on your laptop.
The Linux image inside the container becomes your small Linux runtime.
Skills run inside that container.

### Cluster

You deploy the same Docker image into a Kubernetes pod.
The pod is your runtime environment.
Skills run inside the pod.

This avoids requesting a dedicated VM from infra.

Only ask for a VM when:

* You want a long-lived host outside Kubernetes.
* You need direct OS control.
* Your platform policy does not allow long-running agent workloads in Kubernetes.
* You plan to add local storage or special networking.

For testing and early dev this container based setup covers everything.
