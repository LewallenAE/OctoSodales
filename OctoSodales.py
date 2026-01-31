"""
OCTO SODALES: BUILD-FIRST PYTHON MASTERY
=========================================

Now with file system access:
- Agents see your code directly (no copy/paste)
- Run commands (pytest, mypy)
- Chat about your code like Copilot

Run from your PROJECT directory:
    cd your-project
    python /path/to/OctoSodales.py
"""

import anthropic
import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path

client = anthropic.Anthropic()

# Save file location
SAVE_FILE = Path.home() / ".octosodales_progress.json"

# Model configuration
MODELS = {
    "opus": "claude-opus-4-5-20251101",
    "sonnet": "claude-sonnet-4-20250514",
}

# =============================================================================
# MODERN STANDARDS - All agents use this
# =============================================================================

MODERN_STANDARDS = """
🚨 MODERN PYTHON STANDARDS (applies to ALL agents):

ALWAYS USE/ACCEPT THESE MODERN TOOLS:
| Old/Outdated      | Modern (USE THIS)           |
|-------------------|----------------------------|
| argparse          | Click or Typer             |
| urllib            | httpx or requests          |
| os.path           | pathlib.Path               |
| configparser      | Pydantic                   |
| unittest          | pytest                     |
| threading (for IO)| asyncio + aiohttp          |
| Optional[X]       | X | None (Python 3.10+)    |
| Dict, List typing | dict, list (Python 3.9+)   |
| setup.py          | pyproject.toml             |

If a task mentions an outdated tool, USE THE MODERN ONE INSTEAD.
If reviewing code that uses modern tools, ACCEPT IT even if task said otherwise.
Modern > outdated. Always.
"""


# =============================================================================
# PROJECT CONTEXT - Agents can see your files
# =============================================================================

class ProjectContext:
    """Gives agents access to your project files."""
    
    IGNORE_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.mypy_cache', '.pytest_cache', 'dist', 'build', '*.egg-info'}
    CODE_EXTENSIONS = {'.py', '.toml', '.yaml', '.yml', '.json', '.md', '.txt', '.cfg', '.ini'}
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        print(f"📁 Project directory: {self.project_dir}")
    
    def get_tree(self, max_depth: int = 3) -> str:
        """Get project file tree."""
        lines = [f"📁 {self.project_dir.name}/"]
        self._walk_tree(self.project_dir, lines, "  ", max_depth, 0)
        return "\n".join(lines) if len(lines) > 1 else "📁 (empty project)"
    
    def _walk_tree(self, path: Path, lines: list, prefix: str, max_depth: int, depth: int):
        if depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            return
        
        for item in items:
            if item.name.startswith('.') and item.name not in ['.env.example']:
                continue
            if item.name in self.IGNORE_DIRS:
                continue
            
            if item.is_dir():
                lines.append(f"{prefix}📁 {item.name}/")
                self._walk_tree(item, lines, prefix + "  ", max_depth, depth + 1)
            else:
                lines.append(f"{prefix}📄 {item.name}")
    
    def read_file(self, relative_path: str) -> str:
        """Read a file's contents."""
        file_path = self.project_dir / relative_path
        if not file_path.exists():
            return f"❌ File not found: {relative_path}"
        if not file_path.is_file():
            return f"❌ Not a file: {relative_path}"
        
        try:
            content = file_path.read_text(encoding='utf-8')
            ext = file_path.suffix
            lang = "python" if ext == ".py" else "toml" if ext == ".toml" else ""
            return f"📄 {relative_path}:\n```{lang}\n{content}\n```"
        except Exception as e:
            return f"❌ Error reading {relative_path}: {e}"
    
    def read_all_python_files(self) -> str:
        """Read all Python files in the project."""
        files_content = []
        
        for py_file in self.project_dir.rglob("*.py"):
            # Skip ignored directories
            if any(part in self.IGNORE_DIRS for part in py_file.parts):
                continue
            
            relative = py_file.relative_to(self.project_dir)
            try:
                content = py_file.read_text(encoding='utf-8')
                files_content.append(f"📄 {relative}:\n```python\n{content}\n```")
            except:
                continue
        
        if not files_content:
            return "📁 No Python files found yet."
        
        return "\n\n".join(files_content)
    
    def read_project_config(self) -> str:
        """Read pyproject.toml, setup.py, or setup.cfg if they exist."""
        configs = []
        
        for config_file in ['pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt']:
            path = self.project_dir / config_file
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    configs.append(f"📄 {config_file}:\n```\n{content}\n```")
                except:
                    continue
        
        return "\n\n".join(configs) if configs else "📁 No config files yet."
    
    def run_command(self, command: str) -> str:
        """Run a shell command in the project directory."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = ""
            if result.stdout:
                output += f"{result.stdout}\n"
            if result.stderr:
                output += f"{result.stderr}\n"
            if result.returncode != 0:
                output += f"(Exit code: {result.returncode})"
            return output.strip() or "✅ Command completed (no output)"
        except subprocess.TimeoutExpired:
            return "❌ Command timed out after 60 seconds"
        except Exception as e:
            return f"❌ Error running command: {e}"
    
    def run_pytest(self) -> str:
        """Run pytest."""
        return self.run_command("python -m pytest -v")
    
    def run_mypy(self) -> str:
        """Run mypy type checking."""
        return self.run_command("python -m mypy .")
    
    def get_full_context(self) -> str:
        """Get full project context for agents."""
        return f"""
PROJECT STRUCTURE:
{self.get_tree()}

CONFIG FILES:
{self.read_project_config()}

PYTHON CODE:
{self.read_all_python_files()}
"""


# Initialize global project context
project = ProjectContext(".")


class Agent:
    def __init__(self, name: str, system_prompt: str, use_opus: bool = False):
        self.name = name
        self.system_prompt = system_prompt
        self.model = MODELS["opus"] if use_opus else MODELS["sonnet"]
        self.coaching_directive = ""  # Injected by coach
    
    def set_coaching(self, directive: str):
        """Set coaching directive that modifies agent behavior."""
        self.coaching_directive = directive
    
    def run(self, user_message: str, learner: 'BuilderProfile', include_code: bool = False) -> str:
        # Build context
        context = learner.to_context()
        
        # Add project code if requested
        if include_code:
            context += f"\n\nCURRENT PROJECT CODE:\n{project.get_full_context()}"
        
        # Inject coaching directive if present - PUT IT FIRST so it has highest priority
        coaching_section = ""
        if self.coaching_directive:
            coaching_section = f"""
🚨 MANDATORY COACHING DIRECTIVE - YOU MUST FOLLOW THIS:
{self.coaching_directive}

This directive comes from your coach based on student feedback. FOLLOW IT.
---

"""
        
        # ALL agents get modern standards, coaching comes FIRST
        full_system = f"{coaching_section}{MODERN_STANDARDS}\n\n{self.system_prompt}\n\n{context}"
        
        response = client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=full_system,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text


# =============================================================================
# THE BUILD PATH - Each project teaches specific skills
# =============================================================================

PROJECTS = {
    # =========================================================================
    # FOUNDATION: Learn Python by building useful tools
    # =========================================================================
    "01_cli_file_processor": {
        "name": "CLI File Processor",
        "what_you_build": "A CLI tool that processes files (JSON/CSV/text) with proper error handling",
        "why": "Every serious project needs good CLI interfaces. Learn the foundation.",
        "ships_as": "Installable CLI tool (pip install -e .)",
        "skills": [
            "Project structure (src layout, pyproject.toml)",
            "Type hints everywhere",
            "argparse or typer for CLI",
            "pathlib for file handling",
            "Custom exceptions",
            "Logging (not print)",
        ],
        "production_requirements": [
            "Typed with mypy passing",
            "Has --help that actually helps",
            "Graceful error messages (not tracebacks)",
            "Works on files that don't exist (helpful error)",
            "Has at least 3 tests",
        ],
        "time": "2-3 days",
    },
    
    "02_async_data_fetcher": {
        "name": "Async Data Fetcher",
        "what_you_build": "Async HTTP client that fetches from multiple APIs with rate limiting",
        "why": "LLM work = lots of API calls. Master async and HTTP.",
        "ships_as": "Reusable library + CLI",
        "skills": [
            "asyncio and aiohttp",
            "Rate limiting (token bucket)",
            "Retry with exponential backoff",
            "Connection pooling",
            "Progress bars (rich or tqdm)",
            "Structured logging",
        ],
        "production_requirements": [
            "Respects rate limits (no hammering APIs)",
            "Retries transient failures",
            "Shows progress for long operations",
            "Can be cancelled cleanly (Ctrl+C)",
            "Timeout handling",
        ],
        "time": "3-4 days",
    },
    
    "03_config_and_secrets": {
        "name": "Config & Secrets Manager",
        "what_you_build": "A config system with env vars, files, validation, and secrets handling",
        "why": "Real projects need proper config. Not hardcoded API keys.",
        "ships_as": "Reusable config library",
        "skills": [
            "Pydantic for validation",
            "Environment variables",
            "YAML/TOML config files",
            "Secrets handling (never log secrets)",
            "Config hierarchy (defaults < file < env < cli)",
            "dataclasses and __post_init__",
        ],
        "production_requirements": [
            "Validates config on load (fail fast)",
            "Secrets never appear in logs or errors",
            "Works in Docker (env vars)",
            "Works locally (config file)",
            "Clear error messages for missing config",
        ],
        "time": "2-3 days",
    },
    
    # =========================================================================
    # LLM TOOLING: Build the tools you need for AI work
    # =========================================================================
    "04_llm_client": {
        "name": "Universal LLM Client",
        "what_you_build": "A client that talks to OpenAI, Anthropic, local models with same interface",
        "why": "Abstract away providers. Switch models without changing code.",
        "ships_as": "Python library",
        "skills": [
            "ABC and Protocols (interfaces)",
            "Factory pattern",
            "Dependency injection",
            "Streaming responses",
            "Token counting",
            "Cost tracking",
        ],
        "production_requirements": [
            "Same interface for all providers",
            "Streaming works correctly",
            "Tracks token usage and cost",
            "Handles API errors gracefully",
            "Easy to add new providers",
        ],
        "time": "4-5 days",
    },
    
    "05_structured_outputs": {
        "name": "Structured Output Parser",
        "what_you_build": "Force LLMs to return valid JSON/Pydantic models with retries",
        "why": "LLMs return garbage sometimes. Make them reliable.",
        "ships_as": "Library that wraps LLM calls",
        "skills": [
            "Pydantic models for schemas",
            "JSON extraction from messy text",
            "Retry logic with validation",
            "Prompt engineering for structure",
            "Generic types (TypeVar)",
            "Decorators",
        ],
        "production_requirements": [
            "Returns typed Pydantic models",
            "Retries on parse failure (with better prompt)",
            "Validates against schema",
            "Works with streaming",
            "Handles partial JSON",
        ],
        "time": "3-4 days",
    },
    
    "06_prompt_manager": {
        "name": "Prompt Template System",
        "what_you_build": "A system for managing, versioning, and testing prompts",
        "why": "Prompts are code. Treat them like code.",
        "ships_as": "Library + CLI for prompt management",
        "skills": [
            "Jinja2 templating",
            "YAML-based prompt storage",
            "Version control for prompts",
            "Prompt testing framework",
            "Variable validation",
            "Context managers",
        ],
        "production_requirements": [
            "Prompts stored as files (not hardcoded)",
            "Variables are validated before rendering",
            "Can diff prompt versions",
            "Can test prompts against expected outputs",
            "CLI to list/render/test prompts",
        ],
        "time": "3-4 days",
    },
    
    # =========================================================================
    # EVAL SYSTEMS: Build tools to measure AI quality
    # =========================================================================
    "07_simple_eval": {
        "name": "Simple Eval Runner",
        "what_you_build": "Run a model against a dataset and compute metrics",
        "why": "Can't improve what you can't measure.",
        "ships_as": "CLI tool + library",
        "skills": [
            "Dataset loading (HuggingFace, JSON, CSV)",
            "Batch processing with progress",
            "Metrics computation (accuracy, F1, etc.)",
            "Results serialization",
            "Parallel execution",
            "Caching (don't re-run completed items)",
        ],
        "production_requirements": [
            "Resumable (can stop and continue)",
            "Caches results (don't waste API calls)",
            "Outputs structured results (JSON)",
            "Shows progress and ETA",
            "Handles failures gracefully (skip, retry, or fail)",
        ],
        "time": "4-5 days",
    },
    
    "08_llm_judge": {
        "name": "LLM-as-Judge System",
        "what_you_build": "Use one LLM to evaluate another LLM's outputs",
        "why": "This is how modern evals work. MT-Bench, Chatbot Arena, etc.",
        "ships_as": "Library + CLI",
        "skills": [
            "Judge prompt engineering",
            "Rubric design",
            "Pairwise comparisons",
            "Position bias mitigation",
            "Inter-rater reliability",
            "Structured judge outputs",
        ],
        "production_requirements": [
            "Configurable rubrics",
            "Handles position bias (swap order, average)",
            "Returns structured scores + reasoning",
            "Can use different judge models",
            "Computes agreement metrics",
        ],
        "time": "5-6 days",
    },
    
    "09_multi_agent_debate": {
        "name": "Multi-Agent Debate System",
        "what_you_build": "Agents that critique and improve each other's responses",
        "why": "Self-improvement through debate. Cutting edge technique.",
        "ships_as": "Framework + examples",
        "skills": [
            "Agent orchestration",
            "Conversation management",
            "Critique prompt design",
            "Iterative refinement",
            "Stopping conditions",
            "Logging agent interactions",
        ],
        "production_requirements": [
            "Configurable number of rounds",
            "Different agent roles (generator, critic, judge)",
            "Full conversation logging",
            "Quality improves over rounds (measurable)",
            "Cost tracking per debate",
        ],
        "time": "5-6 days",
    },
    
    # =========================================================================
    # WEB & DEPLOYMENT: Full-stack skills for the capstone
    # =========================================================================
    "10_fastapi_backend": {
        "name": "FastAPI Backend",
        "what_you_build": "A REST API that wraps your LLM client and eval tools",
        "why": "Your capstone needs a backend. Learn FastAPI now.",
        "ships_as": "Running API server + OpenAPI docs",
        "skills": [
            "FastAPI basics (routes, request/response models)",
            "Pydantic for API schemas",
            "Dependency injection",
            "Background tasks",
            "WebSockets (for streaming)",
            "CORS configuration",
            "API versioning",
        ],
        "production_requirements": [
            "OpenAPI docs auto-generated and accurate",
            "Proper HTTP status codes",
            "Request validation with helpful errors",
            "Streaming endpoint for LLM responses",
            "Health check endpoint",
            "Structured logging with request IDs",
        ],
        "time": "4-5 days",
    },
    
    "11_database_and_auth": {
        "name": "Database & Auth",
        "what_you_build": "Add persistence and user authentication to your API",
        "why": "Multi-user apps need databases and auth. No shortcuts.",
        "ships_as": "API with login, users, and persistent data",
        "skills": [
            "SQLAlchemy or SQLModel ORM",
            "Database migrations (Alembic)",
            "User model and sessions",
            "Password hashing (bcrypt)",
            "JWT tokens",
            "OAuth basics (optional: GitHub login)",
            "Row-level security (users see only their data)",
        ],
        "production_requirements": [
            "Users can register and login",
            "Passwords are hashed (never stored plain)",
            "JWT tokens with expiration",
            "Protected routes require auth",
            "Users can only access their own data",
            "Database migrations work cleanly",
        ],
        "time": "5-6 days",
    },
    
    "12_frontend": {
        "name": "React Frontend",
        "what_you_build": "A web UI that talks to your FastAPI backend",
        "why": "CLI is for devs. Real users need a UI.",
        "ships_as": "React app connected to your API",
        "skills": [
            "React basics (components, state, hooks)",
            "TypeScript for frontend",
            "API calls (fetch or axios)",
            "Auth flow (login, store token, protected routes)",
            "Forms and validation",
            "Loading states and error handling",
            "Basic styling (Tailwind or CSS modules)",
        ],
        "production_requirements": [
            "Login/register screens that work",
            "Auth state persists across refresh",
            "Protected routes redirect to login",
            "API errors shown to user helpfully",
            "Loading spinners during API calls",
            "Mobile-responsive layout",
        ],
        "time": "5-6 days",
    },
    
    "13_deployment": {
        "name": "Deployment & DevOps",
        "what_you_build": "Deploy your full-stack app to the cloud",
        "why": "Not deployed = not real. Ship it for real.",
        "ships_as": "Live URL anyone can access",
        "skills": [
            "Docker (containerize backend and frontend)",
            "Docker Compose (local multi-container)",
            "Cloud hosting (Railway, Render, or Fly.io)",
            "Environment variables in production",
            "Database hosting (managed Postgres)",
            "Domain and HTTPS",
            "CI/CD basics (GitHub Actions)",
        ],
        "production_requirements": [
            "App runs in Docker locally",
            "Deployed to cloud with real URL",
            "HTTPS enabled",
            "Environment variables not in code",
            "Database is hosted (not SQLite in prod)",
            "Can deploy updates with git push",
            "Has basic CI (run tests before deploy)",
        ],
        "time": "3-4 days",
    },
    
    # =========================================================================
    # CAPSTONE: The adaptive learning platform
    # =========================================================================
    "14_capstone_adaptive_learning_platform": {
        "name": "CAPSTONE: Adaptive Learning Platform",
        "what_you_build": """The full OctoSodales platform - the system that taught you, rebuilt and productized:
        
        ONBOARDING:
        - What's your Python level? (none / some / solid)
        - What do you want to build? (CLI tools / web apps / AI-ML / automation)
        - How do you learn best? (reading / examples / trial and error)
        - Do you have a capstone project in mind?
        
        CURRICULUM GENERATION:
        - Opus agent analyzes answers
        - Generates personalized project sequence
        - Each project builds toward THEIR capstone
        
        THE LOOP:
        - 4 primary agents (Curriculum, Teacher, Challenger, Reviewer)
        - 4 coaching agents (optimize each primary agent)
        - Your performance = feedback signal
        - Agents adapt to YOU (the RLHF loop)
        
        FULL STACK:
        - FastAPI backend (from Project 10)
        - React frontend (from Project 12)
        - Auth & persistence (from Project 11)
        - Deployed live (from Project 13)""",
        "why": "You learned with this system. Now you rebuild it. 'I built OctoSodales to teach me how to build OctoSodales.'",
        "ships_as": "Deployed web app at a real URL + GitHub repo",
        "skills": [
            "Everything from Projects 1-13 combined",
            "Dynamic curriculum generation",
            "Multi-agent orchestration at scale",
            "Human-in-the-loop feedback systems",
            "Product thinking (onboarding UX, user journey)",
            "Full-stack integration",
        ],
        "production_requirements": [
            "Onboarding flow asks questions and generates custom curriculum",
            "8 agents working together (4 primary + 4 coaches)",
            "Agents adapt based on learner performance",
            "Web UI that non-technical users could navigate",
            "User accounts with persistent progress",
            "At least ONE other person completes a project using it",
            "Deployed at a real URL with HTTPS",
            "README explains the architecture and the RLHF loop",
            "Code is production quality (typed, tested, documented)",
        ],
        "time": "3-4 weeks",
        "portfolio_value": "MAXIMUM - Product + RLHF system + origin story",
        "interview_story": "I learned Python using an 8-agent AI tutor. Then I rebuilt the tutor as my capstone. It generates personalized curriculums and adapts to each learner - essentially RLHF where learner performance optimizes the teaching agents. It's deployed live and other people have used it.",
    },
}

# Alternative capstones if the learning platform doesn't fit their goals
ALTERNATIVE_CAPSTONES = {
    "eval_harness": {
        "name": "Full Eval Harness",
        "what_you_build": "A complete LLM evaluation framework with plugin system, multiple judge types, leaderboards, CI/CD integration",
        "skills": ["Plugin architecture", "Report generation", "GitHub Actions", "Package publishing"],
    },
    "agent_framework": {
        "name": "Lightweight Agent Framework",
        "what_you_build": "A framework for building tool-using agents (like a mini LangChain but not bloated)",
        "skills": ["Tool registration", "Execution loops", "Memory systems", "Observability"],
    },
    "fine_tune_pipeline": {
        "name": "Fine-tuning Pipeline",
        "what_you_build": "End-to-end pipeline: data prep → training → eval → deployment",
        "skills": ["Data processing", "Training loops", "Checkpointing", "Model serving"],
    },
    "rag_system": {
        "name": "Production RAG System",
        "what_you_build": "RAG with proper chunking, retrieval, reranking, and evaluation",
        "skills": ["Embeddings", "Vector stores", "Retrieval strategies", "RAG evaluation"],
    },
}


# =============================================================================
# AGENT PROMPTS - Focused on BUILDING
# =============================================================================

CURRICULUM_PROMPT = """You are guiding someone through a BUILD-FIRST Python curriculum.

PHILOSOPHY:
- They learn by BUILDING, not reading
- Every lesson produces something real and shippable
- Production quality from day 1 (types, tests, error handling)
- Fast path to mastery through deliberate practice

PROJECTS BUILD ON EACH OTHER:
1-3: Foundation tools (CLI, async, config)
4-6: LLM tooling (clients, structured outputs, prompts)
7-9: Eval systems (runners, judges, debates)
10: Capstone portfolio piece

YOUR JOB:
- Assess their current project progress
- Decide if they're ready to move on or need to improve current project
- Keep them moving FAST but not sloppy

OUTPUT FORMAT:
{
    "current_project": "project_id",
    "status": "in_progress" | "needs_improvement" | "ready_to_ship",
    "next_action": "what they should do right now",
    "blockers": ["anything holding them back"],
    "time_estimate": "how long until they can move on",
    "motivation": "keep them pumped"
}
"""

LECTURE_PROMPT = """You are a TEACHER using the SAY → SEE → DO method.

ALWAYS USE MODERN TOOLS:
- CLI: Click or Typer (NOT argparse)
- HTTP: httpx or requests (NOT urllib)  
- Paths: pathlib (NOT os.path)
- Testing: pytest (NOT unittest)
- Type hints: Modern syntax (str | None for 3.10+)

STRUCTURE EVERY LESSON IN THREE PARTS:

## 📖 SAY: [Concept Name]
Explain in plain English (2-3 sentences, NO CODE):
- What is it?
- Why does it matter?

## 👀 SEE: Minimal Example
Show the SMALLEST possible example (5-10 lines MAX):
- ONE concept only
- Must actually run
- This is NOT the full implementation - just the pattern

## 🔨 DO: Micro-Steps
Break implementation into TINY numbered steps. Each step is ONE action:

Step 1: [One tiny action - "Add this import"]
VERIFY: [How to check it worked]

Step 2: [Next tiny action - "Create this class (3 lines)"]  
VERIFY: [How to check it worked]

Step 3: [Next tiny action - "Add one line here"]
VERIFY: [How to check it worked]

---

EXAMPLE LESSON (custom exceptions):

## 📖 SAY: Custom Exceptions

Custom exceptions tell users exactly what went wrong in YOUR code. Instead of generic "ValueError", you raise "FileProcessingError" so logs are clear.

## 👀 SEE: Minimal Example

```python
class FileProcessingError(Exception):
    pass

raise FileProcessingError("file not found")
```

That's it. A class that inherits from Exception.

## 🔨 DO: Micro-Steps

Step 1: Add this to the TOP of processor.py:
```python
class FileProcessingError(Exception):
    pass
```

VERIFY: `python -c "from processor import FileProcessingError; print('OK')"`

Step 2: Find where you check if file exists in process_file. Add:
```python
if not path.exists():
    raise FileProcessingError(f"File not found: {path}")
```

VERIFY: Run your CLI with a fake file. Should see "FileProcessingError"

Done when Step 2 passes.

---

RULES:
- SAY: 2-3 sentences, no code
- SEE: 5-10 lines MAX, one concept
- DO: Micro-steps with VERIFY after each
- NEVER dump 40 lines and say "implement this"
- NEVER skip the VERIFY step
"""

CHALLENGE_PROMPT = """You are assigning BUILD challenges - small, concrete, achievable tasks.

🚨 CRITICAL: LOOK AT THE CODE FIRST!
Before assigning a task, check what already exists in the project.
BUILD ON what exists. DON'T rebuild it.

🚨 TASKS MUST BE INTEGRATED - NOT BOLTED ON LATER:
When you assign "build function X", it MUST include from the start:
- Error handling (try/except with custom exceptions)
- Type hints
- The happy path AND the failure path

BAD (separate tasks):
1. "Build process_file function"
2. "Add error handling to process_file"  ← NO! This is refactoring!

GOOD (integrated task):
1. "Build process_file that reads a file, handles FileNotFoundError, and returns a result"

NEVER assign tasks that require refactoring existing code. Get it right the first time.

TASK SIZING:
- 15-30 minutes MAX
- ONE function or ONE small feature
- Must include error handling from the start

TASK PROGRESSION (based on what EXISTS):
- No code yet → "Create X with error handling for Y"
- Function exists → "Add new feature Z" (not "fix X")
- Tests needed → "Write test for the happy path of X"

OUTPUT FORMAT:
{
    "task": "Build [specific thing] that handles [error case] and returns [result type]",
    "context": "How this builds on existing code",
    "includes": ["error handling", "type hints", "specific edge case"],
    "acceptance_criteria": ["1-2 testable requirements"],
    "estimated_time": "15-30 minutes"
}

Integrated from the start. No refactoring tasks.
"""

REVIEW_PROMPT = """You are a SENIOR ENGINEER doing code review.

🚨 CRITICAL RULE - READ THIS FIRST:
If the task mentions "argparse" but they used Click or Typer → THAT'S FINE. PASS THEM.
If the task mentions "requests" but they used httpx → THAT'S FINE. PASS THEM.
If the task mentions "unittest" but they used pytest → THAT'S FINE. PASS THEM.
MODERN LIBRARIES ARE ALWAYS ACCEPTABLE. Never fail someone for using a better tool.
The task description may be outdated. Judge the CODE, not library compliance.

WHAT MATTERS:
1. Does it WORK? (Can you run it? Does it do the thing?)
2. Is it TYPED? (Type hints present, mypy would pass)
3. Is it CLEAN? (Readable, not clever)
4. Is it ROBUST? (Handles errors gracefully)

WHAT DOES NOT MATTER:
- Which specific library they used (Click vs argparse vs Typer - ALL FINE)
- Exact flag names (--input-file vs --input vs positional arg - ALL FINE if it works)
- Minor style differences

VERDICT RULES:
- "ship_it" = Code works, is typed, handles errors. SHIP IT.
- "needs_work" = Minor issues but mostly there
- "major_issues" = Doesn't run, crashes, no error handling

If the code WORKS and is TYPED, lean toward "ship_it" even with minor issues.

OUTPUT FORMAT:
{
    "verdict": "ship_it" | "needs_work" | "major_issues",
    "task_reviewed": "what they built (not what the task said to use)",
    "works": true | false,
    "typed": true | false,
    "clean": true | false,
    "robust": true | false,
    "start_here": "THE ONE THING to fix (or 'none' if shipping)",
    "must_fix": ["blocking issues only"],
    "should_fix": ["suggestions for next time"],
    "overall": "Direct feedback on the code quality"
}
"""


# =============================================================================
# COACHING PROMPTS - Meta-layer that optimizes the primary agents
# =============================================================================

CURRICULUM_COACH_PROMPT = """You are the CURRICULUM COACH. You optimize the Curriculum Agent.

YOU OBSERVE:
- How fast the learner is moving through projects
- Whether they're skipping foundations or getting stuck
- Skill gaps that keep appearing in reviews
- Whether the pacing matches their ability

YOU ADVISE THE CURRICULUM AGENT ON:
- Should they slow down or speed up?
- Are there skills being skipped that will bite them later?
- Should they repeat a project or move on?
- Is the path still right for their goals?

OUTPUT FORMAT:
{
    "pacing_assessment": "too_fast" | "good" | "too_slow",
    "skill_gaps_detected": ["skills they're missing"],
    "recommendation": "specific advice for curriculum agent",
    "adjust_path": true | false,
    "reasoning": "why this adjustment"
}
"""

TEACHER_COACH_PROMPT = """You are the TEACHER COACH. You optimize the Teacher Agent.

YOU OBSERVE:
- Are the learner's code submissions improving after lessons?
- Do they keep making the same mistakes (lesson didn't land)?
- Are they asking for clarification (too complex)?
- Are they breezing through (too basic)?

YOU ADVISE THE TEACHER AGENT ON:
- More code examples or more theory?
- Shorter or longer explanations?
- Different analogies or approaches?
- What concepts need re-teaching?

OUTPUT FORMAT:
{
    "lessons_landing": true | false,
    "recurring_confusion": ["concepts not sticking"],
    "style_adjustment": "more_code" | "more_theory" | "simpler" | "deeper",
    "recommendation": "specific advice for teacher agent",
    "concepts_to_reteach": ["if any"]
}
"""

CHALLENGER_COACH_PROMPT = """You are the CHALLENGER COACH. You optimize the Challenger Agent.

YOU OBSERVE:
- How long tasks take vs estimates
- Pass rate on first submission
- Are they bored (finishing too fast) or frustrated (stuck)?
- Task complexity vs their current skill

YOU ADVISE THE CHALLENGER AGENT ON:
- Harder or easier tasks?
- More scaffolding or less?
- Bigger chunks or smaller steps?
- Add stretch goals or focus on basics?

OUTPUT FORMAT:
{
    "difficulty_assessment": "too_easy" | "right" | "too_hard",
    "completion_rate": "fast" | "normal" | "slow",
    "frustration_signals": ["signs of frustration if any"],
    "recommendation": "specific advice for challenger agent",
    "adjust_difficulty": "increase" | "maintain" | "decrease"
}
"""

REVIEWER_COACH_PROMPT = """You are the REVIEWER COACH. You optimize the Reviewer Agent.

YOU OBSERVE:
- Are reviews consistent (same issues caught every time)?
- Is feedback actionable (do they know what to fix)?
- Are they improving on flagged issues?
- Is the reviewer too harsh or too lenient?

YOU ADVISE THE REVIEWER AGENT ON:
- Be stricter or more encouraging?
- Focus on different aspects?
- More specific feedback needed?
- Adjust pass threshold?

OUTPUT FORMAT:
{
    "review_consistency": "consistent" | "inconsistent",
    "feedback_actionable": true | false,
    "improvement_on_feedback": true | false,
    "harshness": "too_harsh" | "right" | "too_lenient",
    "recommendation": "specific advice for reviewer agent",
    "focus_areas": ["what reviewer should emphasize"]
}
"""


# =============================================================================
# LEARNER PROFILE
# =============================================================================

@dataclass
class BuilderProfile:
    name: str = "Builder"
    current_project: str = "01_cli_file_processor"
    projects_completed: List[str] = field(default_factory=list)
    
    # Current project state
    project_status: str = "not_started"  # not_started, in_progress, in_review, complete
    current_task: str = ""
    tasks_completed: List[str] = field(default_factory=list)
    
    # Code quality tracking
    review_history: List[dict] = field(default_factory=list)
    recurring_issues: List[str] = field(default_factory=list)
    
    # Time tracking
    days_on_current_project: int = 0
    total_days: int = 0
    
    # Learning preferences
    task_size: str = "medium"  # small, medium, large
    explanation_depth: str = "detailed"  # brief, detailed, deep-dive
    learning_style: str = "examples"  # examples, theory-first, trial-error
    pace: str = "normal"  # slow, normal, fast
    
    def get_preferences_context(self) -> str:
        """Return preferences as context for agents."""
        return f"""
LEARNER PREFERENCES (adapt your style to match):
- Task size: {self.task_size} ({"15-30 min tasks" if self.task_size == "small" else "30-60 min tasks" if self.task_size == "medium" else "1-2 hour tasks"})
- Explanation depth: {self.explanation_depth} ({"quick and minimal" if self.explanation_depth == "brief" else "thorough with examples" if self.explanation_depth == "detailed" else "comprehensive with theory"})
- Learning style: {self.learning_style} ({"show code first, explain after" if self.learning_style == "examples" else "explain concept, then show code" if self.learning_style == "theory-first" else "give task, let them struggle, then help"})
- Pace: {self.pace} ({"extra scaffolding and smaller steps" if self.pace == "slow" else "standard progression" if self.pace == "normal" else "minimal hand-holding, challenge them"})
"""
    
    def to_context(self) -> str:
        project_info = PROJECTS.get(self.current_project, {})
        return f"""
BUILDER: {self.name}

CURRENT PROJECT: {self.current_project}
  {project_info.get('name', 'Unknown')}
  Status: {self.project_status}
  Days on project: {self.days_on_current_project}

PROGRESS:
  Projects completed: {len(self.projects_completed)}/14
  Completed: {self.projects_completed}

PATTERNS TO WATCH:
  Recurring issues: {self.recurring_issues or 'None yet'}
{self.get_preferences_context()}
TOTAL TIME: {self.total_days} days
"""
    
    def save(self):
        """Save progress to file"""
        data = asdict(self)
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Progress saved to {SAVE_FILE}")
    
    @classmethod
    def load(cls) -> Optional['BuilderProfile']:
        """Load progress from file if it exists"""
        if not SAVE_FILE.exists():
            return None
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
            profile = cls(**data)
            print(f"📂 Loaded progress for {profile.name}")
            return profile
        except Exception as e:
            print(f"⚠️  Could not load save file: {e}")
            return None


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class BuildOrchestrator:
    def __init__(self, use_coaching: bool = True):
        # Primary agents
        # Curriculum uses Opus (strategic decisions), rest use Sonnet
        self.curriculum = Agent("Curriculum", CURRICULUM_PROMPT, use_opus=True)
        self.teacher = Agent("Teacher", LECTURE_PROMPT, use_opus=False)
        self.challenger = Agent("Challenger", CHALLENGE_PROMPT, use_opus=False)
        self.reviewer = Agent("Reviewer", REVIEW_PROMPT, use_opus=False)
        
        # Coaching layer (meta-agents that optimize the primary agents)
        self.use_coaching = use_coaching
        if use_coaching:
            # Curriculum Coach also uses Opus (meta-level strategic analysis)
            self.curriculum_coach = Agent("CurriculumCoach", CURRICULUM_COACH_PROMPT, use_opus=True)
            self.teacher_coach = Agent("TeacherCoach", TEACHER_COACH_PROMPT, use_opus=False)
            self.challenger_coach = Agent("ChallengerCoach", CHALLENGER_COACH_PROMPT, use_opus=False)
            self.reviewer_coach = Agent("ReviewerCoach", REVIEWER_COACH_PROMPT, use_opus=False)
        
        # Track agent outputs for coaching
        self.agent_history = {
            "curriculum": [],
            "teacher": [],
            "challenger": [],
            "reviewer": [],
        }
        
        # Auto-coaching: run every N reviews
        self.reviews_since_coaching = 0
        self.auto_coach_interval = 3  # Run coaching every 3 reviews
        
        self.learner = BuilderProfile()
        
        # Show model config on init
        print("\n⚙️  MODEL CONFIG:")
        print("   OPUS: Curriculum, Curriculum Coach")
        print("   SONNET: Teacher, Challenger, Reviewer + their coaches")
    
    def initialize(self, name: str, start_project: str = "01_cli_file_processor"):
        self.learner.name = name
        self.learner.current_project = start_project
    
    def _track_output(self, agent_name: str, output: str):
        """Track agent outputs for coaching"""
        self.agent_history[agent_name].append(output)
        # Keep last 5
        if len(self.agent_history[agent_name]) > 5:
            self.agent_history[agent_name] = self.agent_history[agent_name][-5:]
    
    def get_coaching_feedback(self) -> dict:
        """Get feedback from all coaches and APPLY it to agents."""
        if not self.use_coaching:
            return {"message": "Coaching not enabled"}
        
        feedback = {}
        
        # Curriculum Coach
        if self.agent_history["curriculum"]:
            prompt = f"""
Evaluate the Curriculum Agent's recent decisions:
{json.dumps(self.agent_history['curriculum'][-3:], indent=2)}

Learner progress:
- Projects completed: {self.learner.projects_completed}
- Days on current project: {self.learner.days_on_current_project}
- Recent review verdicts: {[r.get('verdict') for r in self.learner.review_history[-5:]]}

Output JSON with "recommendation" field containing a direct instruction for the Curriculum Agent.
"""
            feedback["curriculum"] = self.curriculum_coach.run(prompt, self.learner)
            self._apply_coaching("curriculum", feedback["curriculum"])
        
        # Teacher Coach
        if self.agent_history["teacher"]:
            prompt = f"""
Evaluate the Teacher Agent's recent lessons:
{self.agent_history['teacher'][-2:]}

Are lessons landing?
- Recurring issues in reviews: {self.learner.recurring_issues}
- Same mistakes repeating: {len(self.learner.recurring_issues) > 3}

Output JSON with "recommendation" field containing a direct instruction for the Teacher Agent.
"""
            feedback["teacher"] = self.teacher_coach.run(prompt, self.learner)
            self._apply_coaching("teacher", feedback["teacher"])
        
        # Challenger Coach  
        if self.agent_history["challenger"]:
            prompt = f"""
Evaluate the Challenger Agent's recent tasks:
{json.dumps(self.agent_history['challenger'][-3:], indent=2)}

Task performance:
- Tasks completed: {self.learner.tasks_completed}
- Review pass rate: {len([r for r in self.learner.review_history if r.get('verdict') == 'ship_it'])} / {len(self.learner.review_history)}

Output JSON with "recommendation" field containing a direct instruction for the Challenger Agent.
"""
            feedback["challenger"] = self.challenger_coach.run(prompt, self.learner)
            self._apply_coaching("challenger", feedback["challenger"])
        
        # Reviewer Coach
        if self.agent_history["reviewer"]:
            prompt = f"""
Evaluate the Reviewer Agent's recent reviews:
{json.dumps(self.agent_history['reviewer'][-3:], indent=2)}

Review effectiveness:
- Recurring issues (not being fixed): {self.learner.recurring_issues}
- Improvement trend: {self.learner.review_history[-3:] if len(self.learner.review_history) >= 3 else 'Not enough data'}

Output JSON with "recommendation" field containing a direct instruction for the Reviewer Agent.
"""
            feedback["reviewer"] = self.reviewer_coach.run(prompt, self.learner)
            self._apply_coaching("reviewer", feedback["reviewer"])
        
        return feedback
    
    def _apply_coaching(self, agent_name: str, coach_output: str):
        """Extract recommendation from coach output and apply to agent."""
        try:
            # Try to parse JSON from the coach output
            # Handle cases where JSON is wrapped in markdown
            clean = coach_output
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0]
            
            data = json.loads(clean)
            recommendation = data.get("recommendation", "")
            
            if recommendation:
                agent_map = {
                    "curriculum": self.curriculum,
                    "teacher": self.teacher,
                    "challenger": self.challenger,
                    "reviewer": self.reviewer,
                }
                if agent_name in agent_map:
                    agent_map[agent_name].set_coaching(recommendation)
                    print(f"   ✅ Applied coaching to {agent_name.upper()}")
        except (json.JSONDecodeError, KeyError, IndexError):
            # If we can't parse, try to extract recommendation manually
            if "recommendation" in coach_output.lower():
                # Just use the whole output as directive
                agent_map = {
                    "curriculum": self.curriculum,
                    "teacher": self.teacher,
                    "challenger": self.challenger,
                    "reviewer": self.reviewer,
                }
                if agent_name in agent_map:
                    agent_map[agent_name].set_coaching(f"Coach feedback: {coach_output[:500]}")
                    print(f"   ⚠️ Applied raw coaching to {agent_name.upper()}")
    
    def report_issue(self, issue: str):
        """Student reports an issue - coaches analyze and adjust agents."""
        if not self.use_coaching:
            print("Coaching not enabled.")
            return
        
        # Get recent context
        recent_lessons = self.agent_history.get('teacher', [])[-2:]
        recent_tasks = self.agent_history.get('challenger', [])[-2:]
        recent_reviews = self.agent_history.get('reviewer', [])[-2:]
        
        prompt = f"""
STUDENT REPORTED AN ISSUE:
"{issue}"

RECENT TEACHER OUTPUT:
{json.dumps(recent_lessons, indent=2) if recent_lessons else 'None'}

RECENT CHALLENGER TASKS:
{json.dumps(recent_tasks, indent=2) if recent_tasks else 'None'}

RECENT REVIEWS:
{json.dumps(recent_reviews, indent=2) if recent_reviews else 'None'}

ANALYZE:
1. Which agent is at fault? (Teacher, Challenger, Reviewer, or multiple)
2. What specifically went wrong?
3. What directive should each responsible agent receive?

OUTPUT JSON:
{{
    "fault": ["teacher", "challenger", "reviewer"],  // which agents are responsible
    "analysis": "What went wrong",
    "directives": {{
        "teacher": "Specific instruction for teacher (or null)",
        "challenger": "Specific instruction for challenger (or null)",
        "reviewer": "Specific instruction for reviewer (or null)"
    }}
}}
"""
        # Use curriculum coach to analyze (it has the broadest view)
        response = self.curriculum_coach.run(prompt, self.learner)
        
        try:
            # Parse and apply directives
            clean = response
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0]
            
            data = json.loads(clean)
            print(f"\n📋 Analysis: {data.get('analysis', 'No analysis')}")
            print(f"   Fault: {', '.join(data.get('fault', []))}")
            
            directives = data.get('directives', {})
            for agent_name, directive in directives.items():
                if directive:
                    agent_map = {
                        "teacher": self.teacher,
                        "challenger": self.challenger,
                        "reviewer": self.reviewer,
                    }
                    if agent_name in agent_map:
                        agent_map[agent_name].set_coaching(directive)
                        print(f"   ✅ Updated {agent_name.upper()}: {directive[:100]}...")
        except (json.JSONDecodeError, KeyError):
            print(f"   ⚠️ Could not parse coach response, applying general feedback")
            # Apply issue as general directive to all agents
            self.teacher.set_coaching(f"Student reported issue: {issue}")
            self.challenger.set_coaching(f"Student reported issue: {issue}")
    
    def get_project_brief(self) -> dict:
        """Get the current project details"""
        return PROJECTS.get(self.learner.current_project, {})
    
    def get_curriculum_check(self) -> dict:
        """Have curriculum agent evaluate progress and suggest adjustments"""
        prompt = f"""
Current project: {self.learner.current_project}
Projects completed: {self.learner.projects_completed}
Tasks completed in current project: {self.learner.tasks_completed}
Days on current project: {self.learner.days_on_current_project}

Recent review history:
{json.dumps([{'verdict': r.get('verdict'), 'must_fix': r.get('must_fix', [])} for r in self.learner.review_history[-5:] if isinstance(r, dict)], indent=2)}

Recurring issues: {self.learner.recurring_issues}

Assess their progress and recommend next steps. Output ONLY valid JSON.
"""
        response = self.curriculum.run(prompt, self.learner)
        self._track_output("curriculum", response)
        
        return self._parse_json_response(response)
    
    def get_next_task(self) -> dict:
        """Get the next task to work on - Challenger sees existing code"""
        proj = PROJECTS.get(self.learner.current_project, {})
        
        prompt = f"""
Current project: {proj.get('name')}
Skills to learn: {proj.get('skills')}

COMPLETED TASKS (do NOT repeat these):
{self.learner.tasks_completed if self.learner.tasks_completed else 'None yet'}

FILES THAT PASSED REVIEW (already ship_it):
{[r.get('task_reviewed', 'unknown') for r in self.learner.review_history if isinstance(r, dict) and r.get('verdict') == 'ship_it']}

RECURRING ISSUES to address:
{self.learner.recurring_issues if self.learner.recurring_issues else 'None yet'}

IMPORTANT: Look at the project code below. Do NOT assign tasks for things that are already built!
If cli.py already has a working CLI (Click, Typer, or argparse), move to the NEXT thing (tests, features, etc.)

Give the NEXT task that builds on what exists. Don't rebuild existing code.
Output ONLY valid JSON, no markdown, no explanation before or after.
"""
        # Pass include_code=True so Challenger can see what's already built
        response = self.challenger.run(prompt, self.learner, include_code=True)
        self._track_output("challenger", response)
        
        # Parse JSON - handle markdown wrapping
        task = self._parse_json_response(response)
        if task and "task" in task:
            self.learner.current_task = task.get("task", "")
        return task
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from response, handling markdown code blocks."""
        
        # FIRST: Try extracting from markdown code block (most common case)
        if "```json" in response:
            try:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass
        
        if "```" in response:
            try:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass
        
        # SECOND: Try direct parse (clean JSON)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # THIRD: Find the LAST complete JSON object (skip any { in preamble)
        # Look for the pattern that starts a JSON object with common keys
        for key in ['"task"', '"verdict"', '"pacing"']:
            if key in response:
                try:
                    # Find the { before this key
                    key_pos = response.find(key)
                    start = response.rfind("{", 0, key_pos)
                    if start != -1:
                        # Find matching closing brace
                        depth = 0
                        for i, char in enumerate(response[start:], start):
                            if char == "{":
                                depth += 1
                            elif char == "}":
                                depth -= 1
                                if depth == 0:
                                    return json.loads(response[start:i+1])
                except (json.JSONDecodeError, ValueError):
                    pass
        
        return {"raw": response}
    
    def get_lesson(self, topic: str) -> str:
        """Get a focused lesson on a specific topic"""
        project = PROJECTS.get(self.learner.current_project, {})
        
        prompt = f"""
They're building: {project.get('name')}
They need to learn: {topic}
Their current task: {self.learner.current_task}

Teach them {topic} with production code examples they can use RIGHT NOW.
Keep it under 500 words. They should be coding, not reading.
"""
        response = self.teacher.run(prompt, self.learner)
        self._track_output("teacher", response)
        return response
    
    def submit_code(self, code: str, description: str = "") -> dict:
        """Submit code for review (manual paste - legacy)"""
        proj = PROJECTS.get(self.learner.current_project, {})
        
        prompt = f"""
PROJECT: {proj.get('name')}
REQUIREMENTS: {proj.get('production_requirements')}

CURRENT TASK: {self.learner.current_task}

SUBMITTED CODE:
```python
{code}
```

DESCRIPTION: {description}

Review this code. Be direct. Output ONLY valid JSON.
"""
        response = self.reviewer.run(prompt, self.learner)
        self._track_output("reviewer", response)
        
        review = self._parse_json_response(response)
        
        if "verdict" in review:
            self.learner.review_history.append(review)
            
            # Track recurring issues
            for issue in review.get("must_fix", []):
                if issue not in self.learner.recurring_issues:
                    self.learner.recurring_issues.append(issue)
            
            # If shipped, mark task complete
            if review.get("verdict") == "ship_it":
                task_name = self.learner.current_task or description
                if task_name and task_name not in self.learner.tasks_completed:
                    self.learner.tasks_completed.append(task_name)
                    print(f"\n✅ TASK COMPLETE: {task_name}")
            
            # Auto-save after review
            self.learner.save()
        
        return review
    
    def review_project(self, target_file: str = None) -> dict:
        """Review code for current task only - specific file, not whole project."""
        proj = PROJECTS.get(self.learner.current_project, {})
        
        # Get the specific file content to review
        if target_file:
            file_content = project.read_file(target_file)
        else:
            file_content = "No specific file provided - reviewing based on task description only."
        
        prompt = f"""
PROJECT: {proj.get('name')}

CURRENT TASK: {self.learner.current_task}

REVIEW ONLY THIS FILE (ignore everything else):
{file_content}

Review ONLY the code shown above. Does it complete the current task?
Don't mention other files, tests, or things not related to this specific task.
"""
        response = self.reviewer.run(prompt, self.learner, include_code=False)  # Don't include all code
        self._track_output("reviewer", response)
        
        review = self._parse_json_response(response)
        
        if "verdict" in review:
            self.learner.review_history.append(review)
            
            for issue in review.get("must_fix", []):
                if issue not in self.learner.recurring_issues:
                    self.learner.recurring_issues.append(issue)
            
            if review.get("verdict") == "ship_it":
                # Mark task complete - use task description or file name
                task_name = self.learner.current_task or f"Review: {target_file}"
                if task_name and task_name not in self.learner.tasks_completed:
                    self.learner.tasks_completed.append(task_name)
                    print(f"\n✅ TASK COMPLETE: {task_name}")
            
            self.learner.save()
            
            # Auto-coaching: run every N reviews
            if self.use_coaching:
                self.reviews_since_coaching += 1
                if self.reviews_since_coaching >= self.auto_coach_interval:
                    print("\n🎓 AUTO-COACHING: Adapting agents based on your performance...")
                    self.get_coaching_feedback()
                    self.reviews_since_coaching = 0
                    print("   Agents updated.\n")
        
        return review
    
    def chat(self, message: str) -> str:
        """Chat about your code. Agent sees your files and teaches."""
        prompt = f"""
The learner asks: {message}

Look at their code and TEACH them:
- If they have a bug, show them EXACTLY where it is and explain WHY it's wrong
- If they ask "how do I do X", show complete working code with explanations
- Explain imports, type hints, syntax - don't assume they know production patterns
- Be specific to THEIR code and THEIR current task

You are a TEACHER. Actually teach. No "go read the docs" or placeholders.
"""
        return self.teacher.run(prompt, self.learner, include_code=True)
    
    def run_tests(self) -> str:
        """Run pytest on the project."""
        return project.run_pytest()
    
    def run_typecheck(self) -> str:
        """Run mypy on the project."""
        return project.run_mypy()
    
    def show_tree(self) -> str:
        """Show project file tree."""
        return project.get_tree()
    
    def read_file(self, path: str) -> str:
        """Read a specific file."""
        return project.read_file(path)
    
    def complete_project(self) -> str:
        """Mark current project as complete and move to next - ENFORCES QUALITY."""
        
        # Check if they have ANY reviews for this project
        if not self.learner.review_history:
            return "❌ Can't complete - you haven't submitted any code for review yet. Press 'r' to review your code."
        
        # Check the last review - must be "ship_it"
        last_review = self.learner.review_history[-1]
        last_verdict = last_review.get("verdict") if isinstance(last_review, dict) else None
        
        if last_verdict != "ship_it":
            if last_verdict == "major_issues":
                return f"❌ Can't complete - last review found MAJOR ISSUES. Fix them first.\n   Start here: {last_review.get('start_here', 'See review feedback')}"
            elif last_verdict == "needs_work":
                return f"❌ Can't complete - last review says NEEDS WORK. Address the feedback first.\n   Start here: {last_review.get('start_here', 'See review feedback')}"
            else:
                return "❌ Can't complete - need a passing review. Press 'r' to review your code."
        
        # Check they have at least one task completed
        if not self.learner.tasks_completed:
            return "❌ Can't complete - no tasks marked done. Complete at least one task."
        
        # PASSED - allow completion
        if self.learner.current_project not in self.learner.projects_completed:
            self.learner.projects_completed.append(self.learner.current_project)
        
        # Find next project
        project_ids = list(PROJECTS.keys())
        current_idx = project_ids.index(self.learner.current_project)
        
        if current_idx + 1 < len(project_ids):
            self.learner.current_project = project_ids[current_idx + 1]
            self.learner.project_status = "not_started"
            self.learner.tasks_completed = []
            self.learner.days_on_current_project = 0
            self.learner.review_history = []  # Reset for new project
            
            # Auto-save after completing project
            self.learner.save()
            
            return f"✅ PROJECT COMPLETE!\n\n🚀 Moving to: {PROJECTS[self.learner.current_project]['name']}"
        else:
            self.learner.save()
            return "🎉 ALL PROJECTS COMPLETE! You've built your portfolio!"



# =============================================================================
# INTERACTIVE CLI
# =============================================================================

def show_roadmap():
    print("\n" + "=" * 70)
    print("🗺️  THE BUILD PATH")
    print("=" * 70)
    
    for pid, project in PROJECTS.items():
        print(f"\n{pid}: {project['name']}")
        print(f"   └─ {project['what_you_build'][:60]}...")
        print(f"   └─ Ships as: {project['ships_as']}")
        print(f"   └─ Time: {project['time']}")


def show_project_details(project_id: str):
    project = PROJECTS.get(project_id, {})
    if not project:
        print("Project not found")
        return
    
    print(f"\n{'=' * 70}")
    print(f"📦 {project['name']}")
    print("=" * 70)
    print(f"\nWHAT YOU BUILD:\n  {project['what_you_build']}")
    print(f"\nWHY:\n  {project['why']}")
    print(f"\nSHIPS AS:\n  {project['ships_as']}")
    print(f"\nSKILLS YOU'LL LEARN:")
    for skill in project['skills']:
        print(f"  • {skill}")
    print(f"\nPRODUCTION REQUIREMENTS:")
    for req in project['production_requirements']:
        print(f"  ✓ {req}")
    print(f"\nESTIMATED TIME: {project['time']}")


def run_interactive():
    print("=" * 70)
    print("🐙 OCTO SODALES: Build-First Python Mastery")
    print("=" * 70)
    print("""
You will learn Python by BUILDING 14 real projects.
Each project ships as something real.
The capstone is YOUR adaptive learning platform.

Agents can see your code. No copy/paste needed.
    """)
    
    # Check for saved progress
    saved_profile = BuilderProfile.load()
    
    if saved_profile:
        print(f"\n📂 Found saved progress!")
        print(f"   Name: {saved_profile.name}")
        print(f"   Project: {saved_profile.current_project}")
        print(f"   Completed: {len(saved_profile.projects_completed)}/14 projects")
        resume = input("\nResume? (y/n): ").lower() == "y"
        
        if resume:
            use_coaching = input("Enable coaching layer? (y/n): ").lower() == "y"
            orchestrator = BuildOrchestrator(use_coaching=use_coaching)
            orchestrator.learner = saved_profile
            print(f"\n✅ Resumed as {saved_profile.name}")
        else:
            saved_profile = None
    
    if not saved_profile:
        name = input("Your name: ") or "Builder"
        use_coaching = input("Enable coaching layer? (y/n): ").lower() == "y"
        
        print("\nStarting points:")
        print("  1  = Start from project 1 (recommended)")
        print("  4  = Skip to LLM tooling (if you know Python basics)")
        print("  7  = Skip to Eval systems (if you've built LLM tools)")
        print("  10 = Skip to Web/Deployment (if you've built eval systems)")
        
        start = input("Start at project (1-14): ") or "1"
        project_id = list(PROJECTS.keys())[int(start) - 1]
        
        orchestrator = BuildOrchestrator(use_coaching=use_coaching)
        orchestrator.initialize(name, project_id)
        orchestrator.learner.save()
        
        print(f"\n✅ Starting with: {PROJECTS[project_id]['name']}")
    
    if use_coaching:
        print("✅ Coaching layer ENABLED")
    
    while True:
        print("\n" + "=" * 50)
        print("CURRICULUM:")
        print("  1. Project details     2. Next task")
        print("  3. Learn concept       4. Full roadmap")
        print("  5. My progress         6. Curriculum check")
        print("\nCODE (agents see your files):")
        print("  r. Review file         c. Chat about code")
        print("  t. Run tests           m. Run mypy")
        print("  f. Show file tree      v. View file")
        print("\nPROJECT:")
        print("  done. Mark project complete")
        if use_coaching:
            print("  coach. Get coaching feedback")
            print("  !. Report issue (feedback to coaches)")
        print("  p. Learning preferences")
        print("  s. Save    q. Quit")
        
        choice = input("\n> ").lower().strip()
        
        # Curriculum commands
        if choice == "1":
            show_project_details(orchestrator.learner.current_project)
            
        elif choice == "2":
            print("\n🎯 NEXT TASK:")
            task = orchestrator.get_next_task()
            print(json.dumps(task, indent=2))
            
        elif choice == "3":
            topic = input("What do you need to learn? ")
            print(f"\n📖 LESSON: {topic}")
            print("-" * 40)
            print(orchestrator.get_lesson(topic))
            
        elif choice == "4":
            show_roadmap()
            
        elif choice == "5":
            print(orchestrator.learner.to_context())
        
        elif choice == "6":
            print("\n📊 CURRICULUM CHECK:")
            print("-" * 40)
            check = orchestrator.get_curriculum_check()
            print(json.dumps(check, indent=2))
        
        # Code commands (agents see your files)
        elif choice == "r":
            print("\n📝 REVIEW CODE")
            print(f"Current task: {orchestrator.learner.current_task or 'None set - get a task first (press 2)'}")
            print("\nYour files:")
            print(orchestrator.show_tree())
            target = input("\nWhich file to review? (e.g. src/cli_file_processor/cli.py): ").strip()
            if target:
                print(f"\n📝 REVIEWING: {target}")
                print("-" * 40)
                review = orchestrator.review_project(target)
                print(json.dumps(review, indent=2) if isinstance(review, dict) else review)
            else:
                print("No file specified.")
        
        elif choice == "c":
            question = input("Ask about your code: ")
            print("\n💬 RESPONSE:")
            print("-" * 40)
            print(orchestrator.chat(question))
        
        elif choice == "t":
            print("\n🧪 RUNNING TESTS...")
            print("-" * 40)
            print(orchestrator.run_tests())
        
        elif choice == "m":
            print("\n🔍 RUNNING MYPY...")
            print("-" * 40)
            print(orchestrator.run_typecheck())
        
        elif choice == "f":
            print("\n📁 PROJECT STRUCTURE:")
            print("-" * 40)
            print(orchestrator.show_tree())
        
        elif choice == "v":
            filepath = input("File path (relative): ")
            print(f"\n📄 {filepath}:")
            print("-" * 40)
            print(orchestrator.read_file(filepath))
        
        # Project commands
        elif choice == "done":
            confirm = input("Mark project complete? (y/n): ")
            if confirm.lower() == "y":
                result = orchestrator.complete_project()
                print(f"\n{result}")
        
        elif choice == "coach" and use_coaching:
            print("\n🎓 COACHING FEEDBACK:")
            print("-" * 40)
            print("Analyzing agent performance...\n")
            feedback = orchestrator.get_coaching_feedback()
            for agent, coach_feedback in feedback.items():
                print(f"\n{agent.upper()} COACH:")
                print(coach_feedback)
        
        elif choice == "!" and use_coaching:
            print("\n⚠️  REPORT ISSUE TO COACHES")
            print("-" * 40)
            print("Describe what went wrong. Examples:")
            print("  - 'Teacher taught X but Challenger expected Y'")
            print("  - 'Lesson was too vague, didn't explain Z'")
            print("  - 'Task required refactoring instead of building new'")
            print()
            issue = input("Your issue: ").strip()
            if issue:
                print("\nRouting to coaches...")
                orchestrator.report_issue(issue)
                print("✅ Issue reported. Coaches will adjust agents.")
        
        elif choice == "p":
            print("\n⚙️  LEARNING PREFERENCES")
            print("=" * 40)
            print(f"Current settings:")
            print(f"  Task size: {orchestrator.learner.task_size}")
            print(f"  Explanation depth: {orchestrator.learner.explanation_depth}")
            print(f"  Learning style: {orchestrator.learner.learning_style}")
            print(f"  Pace: {orchestrator.learner.pace}")
            print()
            
            print("1. Task size (how big are assignments?)")
            print("   [s]mall (15-30 min)  [m]edium (30-60 min)  [l]arge (1-2 hours)")
            size = input("   > ").lower().strip()
            if size in ['s', 'small']:
                orchestrator.learner.task_size = "small"
            elif size in ['m', 'medium']:
                orchestrator.learner.task_size = "medium"
            elif size in ['l', 'large']:
                orchestrator.learner.task_size = "large"
            
            print("\n2. Explanation depth (how detailed are lessons?)")
            print("   [b]rief (quick, minimal)  [d]etailed (thorough)  [deep] (comprehensive)")
            depth = input("   > ").lower().strip()
            if depth in ['b', 'brief']:
                orchestrator.learner.explanation_depth = "brief"
            elif depth in ['d', 'detailed']:
                orchestrator.learner.explanation_depth = "detailed"
            elif depth in ['deep', 'deep-dive']:
                orchestrator.learner.explanation_depth = "deep-dive"
            
            print("\n3. Learning style (how do you learn best?)")
            print("   [e]xamples (code first, explain after)")
            print("   [t]heory (explain concept, then code)")
            print("   [trial] (struggle first, then help)")
            style = input("   > ").lower().strip()
            if style in ['e', 'examples']:
                orchestrator.learner.learning_style = "examples"
            elif style in ['t', 'theory', 'theory-first']:
                orchestrator.learner.learning_style = "theory-first"
            elif style in ['trial', 'trial-error']:
                orchestrator.learner.learning_style = "trial-error"
            
            print("\n4. Pace (how fast do we move?)")
            print("   [slow] (extra scaffolding)  [n]ormal  [f]ast (challenge me)")
            pace = input("   > ").lower().strip()
            if pace in ['slow', 's']:
                orchestrator.learner.pace = "slow"
            elif pace in ['n', 'normal']:
                orchestrator.learner.pace = "normal"
            elif pace in ['f', 'fast']:
                orchestrator.learner.pace = "fast"
            
            orchestrator.learner.save()
            print("\n✅ Preferences updated! Agents will adapt to your style.")
        
        elif choice == "s":
            orchestrator.learner.save()
            
        elif choice == "q":
            orchestrator.learner.save()
            print("\nProgress saved. Keep building! 🔨")
            break


if __name__ == "__main__":
    run_interactive()
