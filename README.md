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

### 1. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=your_api_key_here
```

### 2. Build the Image

```bash
docker build -t claude-agent-dev .
```

### 3. Run the Container

```bash
# Option A: Use .env file
docker run -d --rm \
  -p 8080:8080 \
  --env-file .env \
  claude-agent-dev

# Option B: Pass environment variable directly
docker run -d --rm \
  -p 8080:8080 \
  -e ANTHROPIC_API_KEY=your_api_key_here \
  claude-agent-dev
```

### 4. Test the API

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
| `/chat/verbose` | POST | Send message with step-by-step execution logs |

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

### POST /chat/verbose

Use this endpoint to see exactly how the model picks skills and executes them.

Request:
```json
{
  "message": "Analyze the earnings PDF in testdata/"
}
```

Response:
```json
{
  "reply": "The Q3 2024 earnings report shows...",
  "steps": [
    {
      "step": 1,
      "timestamp": "2024-12-08T20:30:00",
      "type": "tool_use",
      "content": "Invoking tool: Skill",
      "tool_name": "Skill",
      "tool_input": {"skill": "pdf"}
    },
    {
      "step": 2,
      "timestamp": "2024-12-08T20:30:01",
      "type": "tool_use",
      "content": "Invoking tool: Read",
      "tool_name": "Read",
      "tool_input": {"file_path": "/app/testdata/earnings_report_q3_2024.pdf"}
    },
    {
      "step": 3,
      "timestamp": "2024-12-08T20:30:02",
      "type": "tool_result",
      "content": "PDF content extracted: TechCorp Inc Q3 2024..."
    },
    {
      "step": 4,
      "timestamp": "2024-12-08T20:30:03",
      "type": "text",
      "content": "The Q3 2024 earnings report shows revenue of $2.4B..."
    }
  ],
  "total_steps": 4,
  "tools_used": ["Skill", "Read"]
}
```

**Step types:**
- `tool_use` - Model decided to invoke a tool/skill
- `tool_result` - Output from executing the tool
- `text` - Model's text response
- `thinking` - Model's reasoning (if extended thinking enabled)
- `error` - Error occurred during execution

**Example curl:**
```bash
curl http://localhost:8080/chat/verbose \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze the earnings PDF in testdata/"}' | jq
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

## Example: Analyzing a PDF

```bash
curl http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze the earnings PDF in testdata/"}'
```

**What happens when you run this:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. HTTP Request                                                          │
│    curl POST /chat → FastAPI endpoint                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. Agent Query                                                           │
│    FastAPI → Claude Agent SDK query(prompt)                              │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. Model Decision                    ← HTTPS to Claude API               │
│    Claude sees the prompt and decides: "I should use the pdf skill"      │
├──────────────────────────────────────────────────────────────────────────┤
│ 4. Skill Execution (inside container)                                    │
│    Agent SDK invokes pdf skill:                                          │
│    - Reads SKILL.md from /app/.claude/skills/pdf/                        │
│    - Runs pdf2image to convert pages to images                           │
│    - Extracts text and tables from PDF                                   │
│    - All file I/O happens inside the container                           │
├──────────────────────────────────────────────────────────────────────────┤
│ 5. Skill Output → Claude             ← HTTPS to Claude API               │
│    PDF content sent back to Claude for analysis                          │
├──────────────────────────────────────────────────────────────────────────┤
│ 6. Response Generation                                                   │
│    Claude generates analysis: revenue, trends, key metrics               │
├──────────────────────────────────────────────────────────────────────────┤
│ 7. JSON Response                                                         │
│    {"reply": "The Q3 2024 earnings report shows revenue of $2.4B..."}    │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key points:**

- Steps 3, 5, 6 are HTTPS calls to Claude API (or your gateway)
- Step 4 runs entirely inside your container - no external calls
- The PDF file never leaves your container
- Only the extracted text/analysis goes to Claude

## How to Explain AgentSkills to Someone

### The Problem We're Solving

> "We can't get access to **Claude BM** (Anthropic's managed sandbox environment) which provides an isolated code execution environment with file system access, command execution, and LLM connectivity out of the box."

### Our Solution

> "So we're **building our own isolated execution environment** using Docker."

### Simple Explanation (Elevator Pitch)

> "We package everything Claude needs to run skills — Python, file system, bash, PDF tools — into a **Docker container**. The container talks to Claude through our **LLM Gateway**. Skills execute **inside the container**, and only API calls go out to Claude. It's like building our own mini Claude BM."

### Visual Explanation

```
┌─────────────────────────────────────────────────────────┐
│  Docker Container (Our "Claude BM" Replacement)         │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  What's Inside:                                   │  │
│  │  • Python 3.11 + FastAPI                          │  │
│  │  • Claude Agent SDK                               │  │
│  │  • 17 Skills (pdf, xlsx, pptx, etc.)              │  │
│  │  • Bash shell for command execution               │  │
│  │  • File system access (/app/*)                    │  │
│  │  • System tools (LibreOffice, poppler, etc.)      │  │
│  └───────────────────────────────────────────────────┘  │
│                           │                             │
│      Skills run HERE      │  Only API calls leave       │
│      (isolated)           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │ HTTPS
                            ▼
                 ┌─────────────────────┐
                 │  LLM Gateway        │
                 │  (Corporate Proxy)  │
                 └─────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Claude API         │
                 └─────────────────────┘
```

### Key Points to Emphasize

| What | How We Do It |
|------|--------------|
| **Isolated execution** | Docker container = sandbox |
| **File system access** | Container has `/app/` with full read/write |
| **Command execution** | Bash tool runs commands inside container |
| **LLM connectivity** | Routes through `LLM_GATEWAY_URL` (corporate proxy) |
| **Skills** | Packaged in container at `/app/skills/` |

### What Stays Inside vs. What Goes Out

| Inside Container (Private) | Goes to LLM Gateway (External) |
|---------------------------|-------------------------------|
| File contents (PDFs, Excel) | Prompts and extracted text |
| Bash command execution | Model inference requests |
| Skill logic execution | Claude's responses |
| All file I/O | Nothing else |

### One-Liner for Execs

> "Since we can't use Claude's managed sandbox, we built our own using Docker — skills run in an isolated container, and only LLM API calls go through our corporate gateway."