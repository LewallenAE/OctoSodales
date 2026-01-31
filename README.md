# 🐙 OctoSodales

**An 8-agent AI tutoring system that adapts to how you learn.**

OctoSodales uses a hierarchical multi-agent architecture with human-in-the-loop feedback to teach programming. Four primary agents (Curriculum, Teacher, Challenger, Reviewer) handle instruction, while four coaching agents observe learner performance and dynamically adjust teaching strategies—essentially RLHF applied to education.

## Architecture

```
                    ┌─────────────────┐
                    │     COUNCIL     │  (Future: approval layer)
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │        COACHING LAYER       │
              │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
              │  │Curr.│ │Teach│ │Chall│ │Revw │
              │  │Coach│ │Coach│ │Coach│ │Coach│
              │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
              └─────┼───────┼───────┼───────┼────┘
                    │       │       │       │
                    ▼       ▼       ▼       ▼
              ┌─────────────────────────────────┐
              │         PRIMARY AGENTS          │
              │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
              │  │Curric│ │Teach │ │Chall │ │Review│
              │  │ulum  │ │  er  │ │enger │ │  er  │
              │  └──────┘ └──────┘ └──────┘ └──────┘
              └─────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │     LEARNER     │
                    │  (JSON state)   │
                    └─────────────────┘
```

## How It Works

### Primary Agents

| Agent | Model | Role |
|-------|-------|------|
| **Curriculum** | Opus | Strategic decisions—assesses progress, identifies skill gaps, determines when to advance |
| **Teacher** | Sonnet | Delivers lessons using SAY→SEE→DO methodology with production-quality code examples |
| **Challenger** | Sonnet | Assigns tasks calibrated to skill level; reads your code to build on what exists |
| **Reviewer** | Sonnet | Code review with verdicts: `ship_it`, `needs_work`, `major_issues` |

### Coaching Layer (The RLHF Loop)

Each primary agent has a dedicated coach that observes learner performance and injects behavioral directives:

| Coach | Observes | Adjusts |
|-------|----------|---------|
| **Curriculum Coach** | Pacing, skill gaps, time-on-project | Path difficulty, project sequencing |
| **Teacher Coach** | Whether lessons land (recurring mistakes) | Explanation depth, teaching style |
| **Challenger Coach** | Task completion rate, frustration signals | Task difficulty, scaffolding level |
| **Reviewer Coach** | Feedback effectiveness, improvement trends | Review strictness, focus areas |

**The feedback loop:**
1. Learner attempts tasks → Reviewer grades code
2. Performance data accumulates (pass/fail, recurring issues, time spent)
3. Coaches analyze patterns and generate directives
4. Directives inject into agent system prompts
5. Agents adapt their behavior
6. Learner experiences personalized instruction

This is RLHF where learner outcomes optimize teaching agents.

### Adaptive Features

- **Auto-coaching**: Runs every 3 reviews automatically
- **Issue reporting**: Learner can flag problems → routed to coaches for analysis
- **Learning preferences**: Configure task size, explanation depth, pace
- **Project context**: Agents see your actual code (no copy/paste)
- **Modern standards**: Enforces Click/Typer, pathlib, pytest, type hints

## Curriculum

14 projects building toward a capstone:

```
FOUNDATION (1-3)
├── CLI File Processor      → Project structure, error handling
├── Async Data Fetcher      → asyncio, rate limiting, retries
└── Config & Secrets        → Pydantic, environment variables

LLM TOOLING (4-6)
├── Universal LLM Client    → Provider abstraction, streaming
├── Structured Outputs      → Force valid JSON from LLMs
└── Prompt Manager          → Versioning, testing prompts

EVAL SYSTEMS (7-9)
├── Simple Eval Runner      → Batch processing, caching
├── LLM-as-Judge            → Rubrics, position bias mitigation
└── Multi-Agent Debate      → Agent orchestration, iterative refinement

WEB & DEPLOYMENT (10-13)
├── FastAPI Backend         → REST API, WebSockets
├── Database & Auth         → SQLAlchemy, JWT, row-level security
├── React Frontend          → TypeScript, auth flow
└── Deployment              → Docker, CI/CD, cloud hosting

CAPSTONE (14)
└── Adaptive Learning Platform → Rebuild OctoSodales itself
```

## Usage

```bash
# Run from your project directory
cd your-project
python /path/to/OctoSodales.py
```

### Commands

| Key | Action |
|-----|--------|
| `2` | Get next task |
| `3` | Learn a concept |
| `r` | Review your code |
| `c` | Chat about your code |
| `t` | Run pytest |
| `m` | Run mypy |
| `!` | Report issue to coaches |
| `done` | Complete project (requires passing review) |

### Quality Gates

You cannot advance until:
- Code passes review (`ship_it` verdict)
- At least one task completed
- Reviewer confirms production requirements met

## Tech Stack

- **LLM**: Anthropic Claude (Opus for strategic agents, Sonnet for execution)
- **State**: JSON file persistence
- **Code Access**: Direct filesystem reading, subprocess for tests/linting
- **CLI**: Interactive Python REPL

## The Meta-Story

I built OctoSodales to teach myself Python. The system I used to learn is the system I'm rebuilding as the capstone. "I built OctoSodales to teach me how to build OctoSodales."

## License

MIT
