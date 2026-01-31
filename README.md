# 🐙 OctoSodales

**A universal adaptive learning platform powered by 8 AI agents.**

Tell it what you want to learn. It builds you a personalized curriculum and adapts in real-time based on your performance.

> *"Teach me Rust."*  
> *"I want to get better at LeetCode."*  
> *"Help me understand systems design."*  
> *"I need to learn how to build AI applications."*

OctoSodales handles all of it—same architecture, any domain.

## Current Status

**Prototype**: Python curriculum (14 projects, CLI tools → full-stack deployment)  
**Dogfooding**: Using the system to teach myself, validating the methodology  
**Next**: Expand to Rust, Java, Assembly, LeetCode, systems design, AI/ML

## The Vision

Most learning platforms are static. Same content, same order, same pace for everyone.

OctoSodales is different:
- **You define the goal** → "I want to pass system design interviews"
- **Agents build your curriculum** → Based on your current level, time available, learning style
- **You learn by doing** → Challenges, not lectures
- **System adapts to you** → Struggling? Smaller chunks. Breezing through? Harder problems.

The 8-agent architecture makes this possible.

## Architecture

```
                    ┌─────────────────┐
                    │     COUNCIL     │  (Approves curriculum changes)
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

### Primary Agents

| Agent | Role |
|-------|------|
| **Curriculum** | Builds personalized learning path based on goals, skill level, time, learning style |
| **Teacher** | Delivers lessons—SAY (concept) → SEE (example) → DO (micro-steps) |
| **Challenger** | Assigns tasks calibrated to current ability; reads your work to build on what exists |
| **Reviewer** | Grades submissions; gates advancement until quality bar is met |

### Coaching Layer (The RLHF Loop)

Each primary agent has a coach observing learner performance:

| Coach | Observes | Adjusts |
|-------|----------|---------|
| **Curriculum Coach** | Pacing, skill gaps, time-on-topic | Path difficulty, sequencing |
| **Teacher Coach** | Whether lessons stick (recurring mistakes) | Explanation depth, teaching style |
| **Challenger Coach** | Completion rate, frustration signals | Task difficulty, scaffolding |
| **Reviewer Coach** | Feedback effectiveness, improvement trends | Strictness, focus areas |

**The feedback loop:**
1. Learner attempts challenges → Reviewer grades work
2. Performance data accumulates (pass/fail, patterns, time)
3. Coaches analyze and generate directives
4. Directives inject into agent prompts
5. Agents adapt behavior
6. Learner experiences personalized instruction

This is **RLHF applied to education**—learner outcomes are the reward signal that optimizes teaching agents.

### Council Layer (Planned)

Coaches propose curriculum changes → Council approves/rejects → Changes propagate down.

Adds governance to prevent oscillation and ensures coherent learning paths.

## How Onboarding Works (Full Version)

```
1. What do you want to learn?
   → "Rust programming"

2. What's your current level?
   → "I know Python, never touched Rust"

3. Do you have a target project or goal?
   → "Build a CLI tool and understand ownership"

4. How do you learn best?
   → "Show me code first, explain after"

5. How many hours per week?
   → "10 hours"

    ↓ Curriculum Agent (Opus) generates personalized path ↓

6. Your curriculum:
   - Week 1-2: Ownership & borrowing (small exercises)
   - Week 3-4: Error handling, Option/Result
   - Week 5-6: CLI with clap, file I/O
   - Week 7-8: Your CLI project
   
   Adapts as you go.
```

## Prototype: Python Curriculum

Currently validating the system with a 14-project Python path:

```
FOUNDATION (1-3)
├── CLI File Processor      → Project structure, error handling
├── Async Data Fetcher      → asyncio, rate limiting
└── Config & Secrets        → Pydantic, env vars

LLM TOOLING (4-6)
├── Universal LLM Client    → Provider abstraction
├── Structured Outputs      → Force valid JSON from LLMs
└── Prompt Manager          → Versioning, testing

EVAL SYSTEMS (7-9)
├── Simple Eval Runner      → Batch processing, caching
├── LLM-as-Judge            → Rubrics, bias mitigation
└── Multi-Agent Debate      → Agent orchestration

WEB & DEPLOYMENT (10-13)
├── FastAPI Backend
├── Database & Auth
├── React Frontend
└── Deployment (Docker, CI/CD)

CAPSTONE (14)
└── Rebuild OctoSodales
```

## Usage (Prototype)

```bash
cd your-project
python /path/to/OctoSodales.py
```

| Key | Action |
|-----|--------|
| `2` | Get next task |
| `3` | Learn a concept |
| `r` | Review your code |
| `c` | Chat about your code |
| `!` | Report issue to coaches |
| `done` | Complete project |

## Roadmap

- [x] 8-agent architecture with coaching layer
- [x] Python curriculum (14 projects)
- [x] Adaptive difficulty and pacing
- [x] File system integration (agents see your code)
- [ ] Domain-agnostic onboarding
- [ ] Rust curriculum
- [ ] LeetCode/DSA track
- [ ] Systems design track
- [ ] Web UI
- [ ] Multi-user deployment

## The Meta-Story

I'm using OctoSodales to teach myself how to build OctoSodales.

The capstone project is rebuilding the system that taught me. If it can teach me to build itself, it can teach anyone anything.

## Tech Stack

- **LLM**: Anthropic Claude (Opus for strategic, Sonnet for execution)
- **State**: JSON persistence
- **Code Access**: Direct filesystem, subprocess for tests/linting

## License

MIT
