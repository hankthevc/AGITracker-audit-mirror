# Contributing to AGI Signpost Tracker

Thank you for your interest in contributing to the AGI Signpost Tracker! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [CI/CD Pipeline](#cicd-pipeline)

## Code of Conduct

This project follows a simple code of conduct:
- Be respectful and constructive
- Focus on evidence-based discussions
- Maintain neutrality in AGI timeline debates
- Cite sources for technical claims

## Getting Started

### Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **Docker** & Docker Compose
- **Git**
- **PostgreSQL** 15+ (or use Docker)
- **Redis** (or use Docker)

### Initial Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/AGITracker.git
cd "AI Doomsday Tracker"
```

2. **Install dependencies**

```bash
# Install all dependencies (npm + pip)
make bootstrap
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required variables:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agi_signpost_tracker
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-proj-your-key-here
LLM_BUDGET_DAILY_USD=20
```

4. **Start development environment**

```bash
make dev
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI (port 8000)
- Celery Worker
- Celery Beat
- Next.js (port 3000)

5. **Run migrations and seed data**

```bash
make migrate
make seed
```

6. **Verify setup**

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Development Workflow

### Creating a Feature Branch

```bash
# Create a new branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Dependency updates, config changes

### Making Changes

1. Make your changes in the appropriate directory:
   - Frontend: `apps/web/`
   - Backend API: `services/etl/`
   - Shared code: `packages/`
   - Database: `infra/migrations/`

2. Follow the code style guidelines (see below)

3. Add tests for new functionality

4. Run linters and tests locally:

```bash
# Lint everything
make lint

# Type check
make typecheck

# Run unit tests
make test

# Run E2E tests
make e2e
```

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality before commits.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### What the hooks check

- **Python**: Ruff formatting and linting
- **TypeScript/JavaScript**: Prettier formatting, ESLint
- **Git**: No direct commits to main
- **General**: Trailing whitespace, YAML/JSON syntax, large files
- **Security**: No hardcoded API keys or secrets

### Running hooks manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff-format --all-files

# Skip hooks (only if absolutely necessary)
git commit --no-verify -m "message"
```

### Troubleshooting hooks

If hooks fail:
1. Read the error message carefully
2. Fix the issues (many hooks auto-fix)
3. Stage the fixes: `git add .`
4. Try committing again

## Testing

### Unit Tests

**Python**:
```bash
cd services/etl
pytest
pytest --cov=app  # With coverage
```

**TypeScript**:
```bash
cd packages/scoring/typescript
npm test
```

### E2E Tests

```bash
cd apps/web
npm run e2e

# Run in UI mode
npm run e2e:ui

# Debug mode
npm run e2e:debug
```

### Test Coverage Goals

- **Python**: 70%+ coverage
- **Critical paths**: 100% coverage (scoring, migrations, API endpoints)

## Code Style

### TypeScript

- **Linter**: ESLint with Next.js config
- **Formatter**: Prettier
- **Style**:
  - Use functional components with hooks
  - Prefer `async/await` over `.then()`
  - Use TypeScript strict mode
  - Import shadcn/ui components for consistency

```typescript
// Good
export async function fetchData(id: string): Promise<Data> {
  const response = await fetch(`/api/data/${id}`);
  return await response.json();
}

// Avoid
export function fetchData(id: string): Promise<Data> {
  return fetch(`/api/data/${id}`).then(res => res.json());
}
```

### Python

- **Linter**: Ruff
- **Formatter**: Ruff format
- **Type checker**: mypy
- **Style**:
  - Type hints required (PEP 484)
  - Docstrings for all public functions (Google style)
  - Line length: 100 characters

```python
# Good
def calculate_progress(
    observed: float,
    baseline: float,
    target: float
) -> float:
    """
    Calculate signpost progress as a normalized value.

    Args:
        observed: Current observed value
        baseline: Historical baseline value
        target: Target value for 100% progress

    Returns:
        Progress value clamped to [0, 1]
    """
    if target == baseline:
        return 0.0
    return max(0.0, min(1.0, (observed - baseline) / (target - baseline)))
```

### Database Migrations

**ALWAYS use Alembic for schema changes**:

```bash
# Create a new migration
cd infra/migrations
alembic revision -m "add_new_column_to_events"

# Edit the generated file
# Apply migration
alembic upgrade head
```

**Never**:
- Use raw SQL DDL in application code
- Skip migrations
- Modify existing migrations after they're merged

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process, dependency updates
- `perf`: Performance improvements

### Examples

```bash
feat(api): Add endpoint for event filtering

Added /v1/events endpoint with category and tier filtering.
Includes pagination and caching (5 min TTL).

Closes #123

---

fix(frontend): Resolve gauge rendering on mobile

Fixed overflow issue causing gauge to clip on small screens.
Added responsive breakpoints.

---

docs(readme): Update deployment instructions

Added Railway CLI steps and environment variable reference.
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
```bash
make test
make e2e
```

2. **Run linters**:
```bash
make lint
```

3. **Update documentation** if needed

4. **Rebase on main** (if needed):
```bash
git fetch origin
git rebase origin/main
```

### Creating a PR

1. Push your branch to your fork:
```bash
git push origin feature/your-feature-name
```

2. Go to GitHub and create a Pull Request

3. Fill out the PR template:
   - **Description**: What does this PR do?
   - **Changes**: List key changes
   - **Testing**: How was this tested?
   - **Screenshots**: For UI changes
   - **Checklist**: Complete the checklist

### PR Review Process

- PRs require at least 1 approval
- CI/CD pipeline must pass
- No merge conflicts with main
- Code follows style guidelines

### After Merge

- Delete your feature branch
- Pull latest main:
```bash
git checkout main
git pull origin main
```

## CI/CD Pipeline

### Workflows

Our GitHub Actions CI/CD pipeline includes:

#### 1. **CI** (on every push/PR)
- Lint & typecheck (TypeScript + Python)
- Unit tests (with matrix: Python 3.11/3.12, Node 20)
- E2E tests (Playwright)
- Build check

#### 2. **Deploy** (on merge to main)
- Deploy frontend to Vercel
- Deploy backend to Railway
- Run database migrations
- Deploy Celery workers
- Smoke tests
- Rollback on failure

#### 3. **Nightly E2E** (daily at 3 AM UTC)
- Full E2E test suite
- Creates GitHub issue on failure

#### 4. **Dependency Updates** (weekly on Monday)
- npm audit and updates
- pip-audit and updates
- Creates PRs for updates
- Posts summary to GitHub issue

### Required Secrets

Set these in GitHub Settings → Secrets:

**Vercel**:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

**Railway**:
- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`

**OpenAI**:
- `OPENAI_API_KEY` (for tests that need LLM)

### Viewing CI Results

- Go to GitHub Actions tab
- Click on your PR's workflow run
- Review logs for any failures
- Fix issues and push again (CI re-runs automatically)

## Development Commands Reference

```bash
# Bootstrap (install all dependencies)
make bootstrap

# Start development environment
make dev

# Run migrations
make migrate

# Create new migration
make migrate-create

# Seed database
make seed

# Run linters
make lint

# Run type checkers
make typecheck

# Run tests
make test

# Run E2E tests
make e2e

# Build for production
make build

# Clean build artifacts
make clean
```

## Project Structure

```
/Users/HenryAppel/AI Doomsday Tracker/
├── .github/
│   └── workflows/       # GitHub Actions CI/CD
├── apps/
│   └── web/            # Next.js frontend
│       ├── app/        # App Router pages
│       ├── components/ # React components
│       └── lib/        # Utilities
├── services/
│   └── etl/            # FastAPI + Celery backend
│       ├── app/
│       │   ├── main.py      # FastAPI app
│       │   ├── models.py    # SQLAlchemy models
│       │   └── tasks/       # Celery tasks
│       └── tests/           # Python tests
├── packages/
│   ├── shared/         # Cross-language schemas
│   └── scoring/        # Dual TS/Py scoring
├── infra/
│   ├── migrations/     # Alembic migrations
│   └── docker/         # Dockerfiles
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

## Getting Help

- **Documentation**: See README.md and docs/
- **Issues**: [GitHub Issues](https://github.com/hankthevc/AGITracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hankthevc/AGITracker/discussions)

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License (code) and CC BY 4.0 (public API data).

---

**Thank you for contributing to AGI Signpost Tracker!** 🚀
