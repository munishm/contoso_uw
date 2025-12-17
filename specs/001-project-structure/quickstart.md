# Quickstart: HSBC Monorepo Structure

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)  
**Created**: 15 December 2025  
**Audience**: Developers new to this project

## Welcome

This guide helps you understand and navigate the HSBC Insurance Underwriting monorepo structure in under 30 minutes (Success Criterion SC-006). By the end, you'll know where everything lives and how to add new code correctly.

---

## 🗺️ Quick Reference Map

**Finding Things in Under 1 Minute** (SC-001):

```text
Need to find...                 Look in...
────────────────────────────────────────────────────────────────
Component source code           src/[component_name]/
Shared utilities                src/shared/
Component interfaces            src/interfaces/
Unit tests                      test/unit/[component_name]/
E2E tests                       test/e2e/
Documentation                   docs/
Architecture decisions          docs/adr/
Component dependencies          src/[component_name]/pyproject.toml
Environment config              .env.dev, .env.staging, .env.prod
Build outputs                   build/ or dist/ (gitignored)
```

---

## 📐 Structure Overview

### Top-Level Layout

```text
/
├── src/                    # All component source code (FR-001)
├── test/                   # All tests, separated by type (FR-002)
├── docs/                   # All documentation (FR-003)
├── specs/                  # Feature specifications
├── .env.*                  # Environment configs (FR-004)
├── build/                  # Build artifacts (gitignored)
├── package.json            # Workspace root config
└── README.md               # You are here!
```

### Components in src/

Each directory under `src/` (except `shared/` and `interfaces/`) is a **pluggable component**:

```text
src/
├── document_classification/    # Component: Classifies document types
│   ├── __init__.py
│   ├── classifier.py           # Main logic
│   ├── models/                 # Component-specific models
│   └── pyproject.toml          # Component dependencies (FR-013)
│
├── entity_extraction/          # Component: Extracts entities
│   ├── __init__.py
│   ├── extractor.py
│   └── pyproject.toml
│
├── interfaces/                 # Component contracts (NOT a component)
│   ├── classifier.py           # IDocumentClassifier interface
│   └── processor.py            # IDocumentProcessor interface
│
└── shared/                     # Shared utilities (NOT a component)
    ├── utils/                  # General utilities
    ├── models/                 # Shared data models
    └── config/                 # Configuration helpers
```

**Key Principle**: Components are **plug-and-play** with **interchangeable implementations** (Clarification 2025-12-15).

---

## 🚀 Quick Start Tasks

### Task 1: Navigate to a Component

**Goal**: Find where document classification logic lives.

**Steps**:
1. All components are in `src/`
2. Look for `src/document_classification/` (snake_case naming)
3. Entry point is typically `__init__.py` or `[component_name].py`

**Expected Time**: Under 30 seconds ✅ (SC-001)

### Task 2: Add a New Component

**Goal**: Create a new "risk_assessment" component correctly.

**Steps**:

1. **Create directory** (snake_case naming, FR-008):
   ```bash
   mkdir -p src/risk_assessment
   ```

2. **Create component structure**:
   ```bash
   cd src/risk_assessment
   touch __init__.py
   touch risk_assessor.py
   ```

3. **Add package manifest** (FR-013 requirement):
   ```bash
   uv init --name hsbc-risk-assessment
   ```
   
   Or create `pyproject.toml` manually:
   ```toml
   [project]
   name = "hsbc-risk-assessment"
   version = "0.1.0"
   description = "Risk assessment component"
   requires-python = ">=3.11"
   dependencies = []
   ```

4. **Implement interface** (FR-015):
   ```python
   # risk_assessor.py
   from src.interfaces.processor import IDocumentProcessor
   
   class RiskAssessor(IDocumentProcessor):
       def process(self, document):
           # Implementation here
           pass
   ```

5. **Create tests** (FR-016):
   ```bash
   mkdir -p test/unit/risk_assessment
   touch test/unit/risk_assessment/test_risk_assessor.py
   ```

**Expected Outcome**: 90% of developers place files correctly on first attempt ✅ (SC-002)

### Task 3: Find and Run Tests

**Goal**: Run tests for a specific component.

**Where Tests Live** (FR-002):
```text
test/
├── unit/                    # Fast, isolated unit tests
│   ├── document_classification/
│   │   └── test_classifier.py
│   └── risk_assessment/
│
├── integration/             # Multi-component tests
│   └── test_workflow.py
│
└── e2e/                     # Full end-to-end tests
    └── test_document_pipeline.py
```

**Run specific component tests**:
```bash
# Unit tests for one component
pytest test/unit/document_classification/

# All unit tests
pytest test/unit/

# E2E tests
pytest test/e2e/
```

**Expected Time**: Locate test directory in under 1 minute ✅

### Task 4: Use Shared Utilities

**Goal**: Import and use a shared utility function.

**Available in** `src/shared/`:
```python
# In your component
from src.shared.utils.validators import validate_document
from src.shared.models.document import Document

def process(self, doc):
    validate_document(doc)
    # Your logic here
```

**Rule**: Shared code is for utilities used by **2+ components**. If only one component needs it, keep it component-specific.

**Layering Rule** (from research.md):
- ✅ Components CAN import from `shared/` and `interfaces/`
- ❌ `shared/` CANNOT import from components (prevents circular dependencies)

### Task 5: Configure Environment

**Goal**: Set up environment-specific configurations.

**Environment Files** (FR-004):
```text
.env.example     # Template (committed to git)
.env.dev         # Development (gitignored)
.env.staging     # Staging (gitignored)
.env.prod        # Production (gitignored)
```

**Setup**:
1. Copy template:
   ```bash
   cp .env.example .env.dev
   ```

2. Fill in your values:
   ```bash
   # .env.dev
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-key-here
   DATABASE_URL=postgresql://localhost/hsbc_dev
   ```

3. Load in code:
   ```python
   from src.shared.config import load_env
   
   config = load_env("dev")  # Loads .env.dev
   ```

**Security**: Never commit actual `.env.*` files (except `.env.example`) ⚠️ (FR-012)

---

## 🧭 Navigation Guide

### "Where do I put this file?"

Use this decision tree (helps achieve SC-002: 90% correct placement):

```
Is it a new major feature/capability?
├─ YES → Create new component in src/
│         e.g., src/fraud_detection/
│
└─ NO → Is it used by 2+ components?
        ├─ YES → Add to src/shared/
        │         e.g., src/shared/utils/
        │
        └─ NO → Add to existing component
                  e.g., src/document_classification/helpers.py

Is it a test file?
├─ Unit test → test/unit/[component_name]/
├─ Integration → test/integration/
└─ E2E → test/e2e/

Is it documentation?
├─ Architecture → docs/architecture/
├─ ADR → docs/adr/
├─ User guide → docs/guides/
└─ API docs → docs/api/
```

### "How do components communicate?"

**Architecture**: **Orchestrator Pattern** (from research.md)

```python
# Components don't call each other directly
# ❌ WRONG:
from src.entity_extraction import Extractor
result = Extractor().extract(doc)  # Tight coupling!

# ✅ CORRECT: Use orchestrator
from src.orchestration.workflow import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
orchestrator.register(classifier, extractor, summarizer)
result = orchestrator.run(document)
```

**Why**: Keeps components pluggable and independently testable.

---

## 📋 Checklists

### Before Creating a Pull Request

- [ ] All directory names use snake_case (FR-008)
- [ ] New components have `pyproject.toml` (FR-013)
- [ ] Tests exist in `test/unit/[component]/` (FR-016)
- [ ] No `.env.*` files committed (except `.env.example`) (FR-012)
- [ ] Component implements interface from `src/interfaces/` (FR-015)
- [ ] No circular dependencies (run `import-linter`)
- [ ] README updated if structure changed (FR-009)

### New Component Checklist

1. [ ] Directory created under `src/` with snake_case name
2. [ ] `__init__.py` created
3. [ ] `pyproject.toml` created with dependencies
4. [ ] Interface implementation added
5. [ ] Unit tests created in `test/unit/[component]/`
6. [ ] Component documented in `docs/architecture/component_overview.md`

---

## 🔧 Common Commands

### Workspace Setup

```bash
# Install all component dependencies
uv sync

# Add dependency to specific component
cd src/document_classification
uv add azure-ai-documentintelligence

# Run all tests
uv run pytest

# Check structure compliance
uv run python scripts/validate_structure.py
```

### Linting & Validation

```bash
# Check import layering (prevent circular deps)
import-linter

# Format code
black src/ test/

# Type checking
mypy src/

# Run pre-commit hooks
pre-commit run --all-files
```

---

## 🎓 Key Principles to Remember

1. **Snake_case Everything**: All directory names use snake_case (FR-008)

2. **Components Are Independent**: Each has own `pyproject.toml` (FR-013)

3. **Plug-and-Play**: Components can be swapped for different implementations (Clarification 2025-12-15)

4. **Tests Mirror Structure**: `test/unit/` structure matches `src/` (FR-016)

5. **No Secrets in Git**: Only `.env.example` is committed (FR-012)

6. **Layered Imports**: interfaces ← shared ← components (no circular deps)

---

## 🆘 Troubleshooting

### "Where's the main entry point?"

**Answer**: Depends on component. Look in `src/[component]/__init__.py` or `src/orchestration/` for workflows.

**Expected Time**: Under 1 minute ✅ (SC-001)

### "I can't import from another component"

**Problem**: Direct component imports create tight coupling.

**Solution**: Use interfaces:
```python
# ❌ Don't do this
from src.entity_extraction.extractor import Extractor

# ✅ Do this instead
from src.interfaces.extractor import IExtractor
# Get implementation via orchestrator or DI
```

### "My directory shows up in version control but shouldn't"

**Problem**: Not in `.gitignore`.

**Solution**: Check if it's `build/`, `dist/`, `.env.*`, or `__pycache__/`. These should all be gitignored. If missing, update `.gitignore`.

### "Where do I add integration tests?"

**Answer**: `test/integration/` for multi-component tests, `test/e2e/` for full workflow tests.

---

## 📚 Further Reading

- **Architecture Decisions**: See [docs/adr/](../../docs/adr/)
- **Component Overview**: [docs/architecture/component_overview.md](../../docs/architecture/component_overview.md)
- **Full Specification**: [spec.md](spec.md)
- **Research & Decisions**: [research.md](research.md)
- **Data Model**: [data-model.md](data-model.md)

---

## ✅ Completion Checklist

After reading this guide, you should be able to:

- [ ] Navigate to any component in under 30 seconds
- [ ] Understand where to place a new file (90% accuracy)
- [ ] Create a new component with correct structure
- [ ] Know where tests go for any component
- [ ] Set up environment configuration
- [ ] Understand component communication patterns
- [ ] Avoid common pitfalls (secrets in git, circular deps)

**Onboarding Time Target**: Under 30 minutes ✅ (SC-006)

---

**Questions?** See [docs/guides/faq.md](../../docs/guides/faq.md) or ask the team in #dev-infrastructure channel.
