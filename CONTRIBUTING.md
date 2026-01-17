# Contributing to SVA-Chatbot

Thank you for your interest in contributing to SVA-Chatbot! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Process](#development-process)
4. [Pull Request Process](#pull-request-process)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation](#documentation)
8. [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

**Positive behavior includes:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**

- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Docker & Docker Compose
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/sva-chatbot.git
cd sva-chatbot
```

3. Add upstream remote:

```bash
git remote add upstream https://github.com/your-org/sva-chatbot.git
```

### Development Setup

1. **Backend Setup:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

2. **Frontend Setup:**

```bash
cd frontend
npm install
cp .env.example .env
```

3. **Start Development Environment:**

```bash
# From project root
docker-compose up -d
```

## Development Process

### Branching Strategy

We use Git Flow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Creating a Feature Branch

```bash
# Update your local repository
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/my-feature

# Make your changes
# ...

# Commit your changes
git add .
git commit -m "feat(scope): description"

# Push to your fork
git push origin feature/my-feature
```

### Commit Message Format

We follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**

```
feat(agents): add new validation agent

Implement validation agent that checks assertion quality
and detects vacuity issues using heuristics.

Closes #123
```

```
fix(api): correct authentication token expiration

The JWT tokens were expiring too quickly. Updated the
expiration time from 30 minutes to 60 minutes.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. **Update your branch:**

```bash
git checkout develop
git pull upstream develop
git checkout feature/my-feature
git rebase develop
```

2. **Run tests:**

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

3. **Check code style:**

```bash
# Backend
black app/
flake8 app/

# Frontend
npm run lint
```

4. **Update documentation** if needed

### Submitting a Pull Request

1. Push your branch to your fork
2. Go to the original repository on GitHub
3. Click "New Pull Request"
4. Select your branch
5. Fill out the PR template:

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests passing
```

6. Request review from maintainers

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainers will merge

### After Merge

1. Delete your feature branch:

```bash
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

2. Update your local repository:

```bash
git checkout develop
git pull upstream develop
```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these additions:

**Imports:**

```python
# Standard library
import os
import sys
from typing import List, Dict, Optional

# Third-party
from fastapi import FastAPI, HTTPException
import numpy as np

# Local
from app.agents import Agent
from app.utils import helper
```

**Type Hints:**

```python
def process_data(
    data: List[Dict[str, Any]],
    options: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Process data and return result."""
    pass
```

**Docstrings:**

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> my_function("test", 5)
        True
    """
    pass
```

**Code Formatting:**

```bash
# Format code
black app/

# Sort imports
isort app/

# Check style
flake8 app/

# Type checking
mypy app/
```

### TypeScript Style Guide

Follow Airbnb style guide:

**Interfaces:**

```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  createdAt: Date;
}
```

**Components:**

```typescript
interface ProjectCardProps {
  project: Project;
  onUpdate: (project: Project) => void;
  className?: string;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onUpdate,
  className
}) => {
  // Component implementation
  return (
    <div className={className}>
      {/* JSX */}
    </div>
  );
};
```

**Hooks:**

```typescript
export const useProject = (projectId: string) => {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Effect implementation
  }, [projectId]);

  return { project, loading, error };
};
```

**Code Formatting:**

```bash
# Check style
npm run lint

# Fix issues
npm run lint -- --fix

# Format code
npm run format
```

## Testing Guidelines

### Backend Testing

**Unit Tests:**

```python
def test_create_project():
    """Test project creation"""
    project = create_project("Test Project", "Description")
    assert project.name == "Test Project"
    assert project.description == "Description"
```

**Property Tests:**

```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1, max_size=100),
    description=st.text(max_size=500)
)
def test_project_round_trip(name, description):
    """
    Feature: sva-chatbot, Property 30: Project Metadata Persistence

    For any created project, storing it and then retrieving it
    should produce a project record with the same name and description.
    """
    project_id = create_project(name, description)
    retrieved = get_project(project_id)

    assert retrieved.name == name
    assert retrieved.description == description
```

**Integration Tests:**

```python
async def test_complete_pipeline():
    """Test the entire generation pipeline"""
    project_id = await create_project("Test")
    await upload_specification(project_id, "spec.pdf")
    await upload_rtl(project_id, "design.sv")

    result = await generate_assertions(project_id)

    assert result.success
    assert len(result.assertions) > 0
```

### Frontend Testing

**Component Tests:**

```typescript
describe('ProjectCard', () => {
  it('renders project information', () => {
    const project = {
      id: '1',
      name: 'Test Project',
      description: 'Test Description',
      status: 'draft'
    };

    render(<ProjectCard project={project} onUpdate={() => {}} />);

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('calls onUpdate when edited', () => {
    const onUpdate = vi.fn();
    const project = { /* ... */ };

    render(<ProjectCard project={project} onUpdate={onUpdate} />);

    fireEvent.click(screen.getByText('Edit'));
    // ... edit actions

    expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({
      id: project.id
    }));
  });
});
```

### Test Coverage

Aim for:

- **Unit tests**: 80%+ coverage
- **Integration tests**: All major workflows
- **Property tests**: All correctness properties

## Documentation

### Code Documentation

**Do:**

- ✅ Document all public APIs
- ✅ Explain complex algorithms
- ✅ Include examples in docstrings
- ✅ Keep comments up-to-date
- ✅ Use clear, concise language

**Don't:**

- ❌ State the obvious
- ❌ Leave outdated comments
- ❌ Write novels in comments
- ❌ Use unclear abbreviations

### User Documentation

When adding features:

1. Update [USER_GUIDE.md](docs/USER_GUIDE.md)
2. Add screenshots if applicable
3. Include examples
4. Update FAQ if needed

### API Documentation

When adding endpoints:

1. Update [API.md](docs/API.md)
2. Include request/response examples
3. Document all parameters
4. Specify authentication requirements

### Developer Documentation

When changing architecture:

1. Update [DEVELOPER.md](docs/DEVELOPER.md)
2. Update architecture diagrams
3. Document design decisions
4. Add migration guides if needed

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code review and collaboration
- **Email**: dev@your-domain.com

### Getting Help

**Before asking:**

1. Check existing documentation
2. Search GitHub issues
3. Review closed PRs

**When asking:**

1. Provide context
2. Include error messages
3. Share relevant code
4. Describe what you've tried

### Reporting Bugs

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:

1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**

- OS: [e.g., macOS 12.0]
- Browser: [e.g., Chrome 96]
- Version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

### Requesting Features

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots.
```

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to SVA-Chatbot! 🎉

---

**Questions?** Contact us at dev@your-domain.com
