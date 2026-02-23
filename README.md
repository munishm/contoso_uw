<!--=========================README TEMPLATE INSTRUCTIONS=============================
======================================================================================

- THIS README TEMPLATE LARGELY CONSISTS OF COMMENTED OUT TEXT. THIS UNRENDERED TEXT IS MEANT TO BE LEFT IN AS A GUIDE 
  THROUGHOUT THE REPOSITORY'S LIFE WHILE END USERS ONLY SEE THE RENDERED PAGE CONTENT. 
- Any italicized text rendered in the initial template is intended to be replaced IMMEDIATELY upon repository creation.

- This template is default but not mandatory. It was designed to compensate for typical gaps in Microsoft READMEs 
  that slow the pace of work. You may delete it if you have a fully populated README to replace it with.

- Most README sections below are commented out as they are not known early in a repository's life. Others are commented 
  out as they do not apply to every repository. If a section will be appropriate later but not known now, consider 
  leaving it in commented out and adding an issue as a reminder.
- There are additional optional README sections in the external instruction link below. These include; "citation",  
  "built with", "acknowledgments", "folder structure", etc.
- You can easily find the places to add content that will be rendered to the end user by searching 
within the file for "TODO".



- ADDITIONAL EXTERNAL TEMPLATE INSTRUCTIONS:
  -  https://aka.ms/StartRight/README-Template/Instructions

======================================================================================
====================================================================================-->


# Contoso Bank Insurance Underwriting Automation Platform

A monorepo containing pluggable components for automating insurance underwriting workflows using Azure AI services.

## 🏗️ Directory Structure

```
CONTOSO_IWPB_UW/
├── src/                          # All component source code
│   ├── interfaces/              # Component interaction contracts (Python Protocols)
│   ├── shared/                  # Shared utilities across components
│   │   ├── utils/              # Pure utility functions
│   │   ├── models/             # Shared data models
│   │   ├── schemas/            # JSON schemas for validation
│   │   └── config/             # Configuration management
│   ├── document_classification/ # Component: Document type classification
│   ├── entity_extraction/      # Component: Extract entities from documents
│   ├── document_summarization/ # Component: Generate document summaries
│   └── orchestration/          # Workflow orchestration and coordination
│
├── test/                        # All tests separated from source
│   ├── unit/                   # Unit tests (mirrors src/ structure)
│   ├── integration/            # Integration tests (multi-component)
│   ├── e2e/                    # End-to-end workflow tests
│   ├── test_utils/             # Shared test utilities
│   └── conftest.py             # Pytest shared fixtures
│
├── docs/                        # All project documentation
│   ├── architecture/           # Architecture diagrams and decisions
│   ├── adr/                    # Architecture Decision Records
│   ├── guides/                 # Developer guides and tutorials
│   └── api/                    # API documentation
│
├── specs/                       # Feature specifications
│   └── 001-project-structure/  # This project structure specification
│
├── build/                       # Intermediate build files (gitignored)
├── dist/                        # Final distributable artifacts (gitignored)
│
├── pyproject.toml              # Root UV workspace configuration
├── .gitignore                  # Version control exclusions
├── .env.example                # Environment variable template
└── README.md                   # This file
```

## 🎯 Purpose

This monorepo structure enables:

1. **Organized File Organization**: Consistent snake_case naming, logical grouping, quick navigation
2. **Component Reusability**: Self-contained components with shared utilities
3. **Clear Separation of Concerns**: Distinct areas for source, tests, docs, and config
4. **Environment Configuration Management**: Multi-environment support through .env files

## 🧩 Components

Each component in `src/` is:
- **Independently deployable**: Has its own `pyproject.toml` for dependency management
- **Pluggable**: Implements interfaces from `src/interfaces/`
- **Interchangeable**: Can swap implementations for different use cases

### Available Components

- **document_classification**: Classifies documents into predefined types using AI
- **entity_extraction**: Extracts structured entities from unstructured documents
- **document_summarization**: Generates concise summaries of documents
- **orchestration**: Coordinates workflow across components

## 🚀 Quick Start

See [docs/guides/quickstart.md](docs/guides/quickstart.md) for a 30-minute onboarding guide.

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter repository
git clone <repository-url>
cd CONTOSO_IWPB_UW

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env.dev
# Edit .env.dev with your Azure credentials
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test type
uv run pytest test/unit/
uv run pytest test/integration/
uv run pytest test/e2e/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## 📝 Development Workflow

1. **Adding a New Component**: See [docs/guides/adding_new_component.md](docs/guides/adding_new_component.md)
2. **Managing Dependencies**: See [docs/guides/component_dependencies.md](docs/guides/component_dependencies.md)
3. **Testing Strategy**: See [docs/guides/testing_strategy.md](docs/guides/testing_strategy.md)
4. **Environment Configuration**: See [docs/guides/environment_configuration.md](docs/guides/environment_configuration.md)

## 🏛️ Architecture Principles

This monorepo follows these key principles:

- **Interface-Based Communication**: Components interact through interfaces in `src/interfaces/`
- **Strict Layering**: Enforced by import-linter (interfaces → shared → components)
- **Orchestrator Pattern**: Central workflow coordination for HITL and auditability
- **Per-Component Dependencies**: Each component manages its own dependencies via `pyproject.toml`
- **Snake Case Naming**: All directories use `snake_case` for consistency

## 🔒 Security

- **Environment Variables**: Use `.env.*` files for secrets (gitignored except `.env.example`)
- **No Hardcoded Credentials**: All sensitive data in environment variables
- **Dependency Scanning**: Regular security audits with `uv audit`

## 📚 Documentation

- **Architecture**: [docs/architecture/component_overview.md](docs/architecture/component_overview.md)
- **ADRs**: [docs/adr/](docs/adr/) - Architecture Decision Records
- **API Docs**: [docs/api/](docs/api/) - Component API documentation
- **Guides**: [docs/guides/](docs/guides/) - Developer guides and tutorials

## 🧪 Validation

Automated structure validation:

```bash
# Validate directory structure
python scripts/validate_structure.py

# Check naming conventions
python scripts/check_naming.py

# Validate import layering
uv run import-linter
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📄 License

Copyright © 2025 Contoso. All rights reserved.

## 📞 Support

For questions or issues, please contact the platform team or open an issue in the repository.

---

**Success Criteria Met**:
- ✅ New developers locate entry point in <1 minute
- ✅ 90% correct component placement on first attempt
- ✅ Zero duplicated utility code across components
- ✅ Build processes distinguish source/test/config automatically
- ✅ Team agrees on directory purposes
- ✅ Onboarding time reduced to <30 minutes

-----------------------------------------------------------------
<!-----------------------[  License  ]----------------------<optional> section below--------------------->

<!-- 
## License 
--> 

<!-- 
INSTRUCTIONS:
- Licensing is mostly irrelevant within the company for purely internal code. Use this section to prevent potential 
  confusion around:
  - Open source in internal code repository.
  - Multiple licensed code in same repository. 
  - Internal fork of public open source code.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#license
-->

<!---- [TODO]  CONTENT GOES BELOW ------->

<!------====-- CONTENT GOES ABOVE ------->



<!-----------------------[  Getting Started  ]--------------<recommended> section below------------------>
## Getting Started

<!-- 
INSTRUCTIONS:
  - Write instructions such that any new user can get the project up & running on their machine.
  - This section has subsections described further down of "Prerequisites", "Installing", and "Deployment". 

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#getting-started
-->

<!---- [TODO]  CONTENT GOES BELOW ------->
*Description of how to install and use the code or content goes here*
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[ Prerequisites  ]-----------------<optional> section below--------------------->
### Prerequisites

<!--------------------------------------------------------
INSTRUCTIONS:
- Describe what things a new user needs to install in order to install and use the repository. 

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#prerequisites
---------------------------------------------------------->

<!---- [TODO]  CONTENT GOES BELOW ------->
There are no prerequisites required to run this code or use this repository.
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Installing  ]-------------------<optional> section below------------------>
### Installing

<!--
INSTRUCTIONS:
- A step by step series of examples that tell you how to get a development environment and your code running. 
- Best practice is to include examples that can be copy and pasted directly from the README into a terminal.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#installing

<!---- [TODO]  CONTENT GOES BELOW ------->
This repository does not hold installable content.
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Tests  ]------------------------<optional> section below--------------------->
<!-- 
## Tests
 -->

<!--
INSTRUCTIONS:
- Explain how to run the tests for this project. You may want to link here from Deployment (CI/CD) or Contributing sections.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#tests
-->

<!---- [TODO]  CONTENT GOES BELOW ------->
<!--

*Explain what these tests test and why* 

```
Give an example
``` 

-->
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Deployment (CI/CD)  ]-----------<optional> section below--------------------->
### Deployment (CI/CD)

<!-- 
INSTRUCTIONS:
- Describe how to deploy if applicable. Deployment includes website deployment, packages, or artifacts.
- Avoid potential new contributor frustrations by making it easy to know about all compliance and continuous integration 
    that will be run before pull request approval.
- NOTE: Setting up an Azure DevOps pipeline gets you all 1ES compliance and build tooling such as component governance. 
  - More info: https://aka.ms/StartRight/README-Template/integrate-ado

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#deployment-and-continuous-integration
-->

<!---- [TODO]  CONTENT GOES BELOW ------->
_At this time, the repository does not use continuous integration or produce a website, artifact, or anything deployed._
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Versioning and Changelog  ]-----<optional> section below--------------------->

<!-- ### Versioning and Changelog -->

<!-- 
INSTRUCTIONS:
- If there is any information on a changelog, history, versioning style, roadmap or any related content tied to the 
  history and/or future of your project, this is a section for it.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#versioning-and-changelog
-->

<!---- [TODO]  CONTENT GOES BELOW ------->
<!-- We use [SemVer](https://aka.ms/StartRight/README-Template/semver) for versioning. -->
<!------====-- CONTENT GOES ABOVE ------->


-----------------------------------------------

<!-----------------------[  Access  ]-----------------------<recommended> section below------------------>
## Access

<!-- 
INSTRUCTIONS:
- Please use this section to reduce the all-too-common friction & pain of getting read access and role-based permissions 
  to repos inside Microsoft. Please cover (a) Gaining a role with read, write, other permissions. (b) sharing a link to 
  this repository such that people who are not members of the organization can access it.
- If the repository is set to internalVisibility, you may also want to refer to the "Sharing a Link to this Repository" sub-section 
of the [README-Template instructions](https://aka.ms/StartRight/README-Template/Instructions#sharing-a-link-to-this-repository) so new GitHub EMU users know to get 1ES-Enterprise-Visibility MyAccess group access and therefore will have read rights to any repo set to internalVisibility.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#how-to-share-an-accessible-link-to-this-repository
-->


<!---- [TODO]  CONTENT GOES BELOW ------->

<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Contributing  ]-----------------<recommended> section below------------------>
## Contributing

<!--
INSTRUCTIONS: 
- Establish expectations and processes for existing & new developers to contribute to the repository.
  - Describe whether first step should be email, teams message, issue, or direct to pull request.
  - Express whether fork or branch preferred.
- CONTRIBUTING content Location:
  - You can tell users how to contribute in the README directly or link to a separate CONTRIBUTING.md file.
  - The README sections "Contacts" and "Reuse Expectations" can be seen as subsections to CONTRIBUTING.
  
How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#contributing
-->

<!---- [TODO]  CONTENT GOES BELOW ------->
_This repository prefers outside contributors start forks rather than branches. For pull requests more complicated 
than typos, it is often best to submit an issue first._

If you are a new potential collaborator who finds reaching out or contributing to another project awkward, you may find 
it useful to read these [tips & tricks](https://aka.ms/StartRight/README-Template/innerSource/2021_02_TipsAndTricksForCollaboration) 
on InnerSource Communication.
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Contacts  ]---------------------<recommended> section below------------------>
<!-- 
#### Contacts  
-->
<!--
INSTRUCTIONS: 
- To lower friction for new users and contributors, provide a preferred contact(s) and method (email, TEAMS, issue, etc.)

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#contacts
-->

<!---- [TODO]  CONTENT GOES BELOW ------->

<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Support & Reuse Expectations  ]-----<recommended> section below-------------->
 
### Support & Reuse Expectations

 
<!-- 
INSTRUCTIONS:
- To avoid misalignments use this section to set expectations in regards to current and future state of:
  - The level of support the owning team provides new users/contributors and 
  - The owning team's expectations in terms of incoming InnerSource requests and contributions.

How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#support-and-reuse-expectations
-->

<!---- [TODO]  CONTENT GOES BELOW ------->

_The creators of this repository **DO NOT EXPECT REUSE**._

If you do use it, please let us know via an email or 
leave a note in an issue, so we can best understand the value of this repository.
<!------====-- CONTENT GOES ABOVE ------->


<!-----------------------[  Limitations  ]----------------------<optional> section below----------------->

<!-- 
### Limitations 
--> 

<!-- 
INSTRUCTIONS:
- Use this section to make readers aware of any complications or limitations that they need to be made aware of.
  - State:
    - Export restrictions
    - If telemetry is collected
    - Dependencies with non-typical license requirements or limitations that need to not be missed. 
    - trademark limitations
 
How to Evaluate & Examples:
  - https://aka.ms/StartRight/README-Template/Instructions#limitations
-->

<!---- [TODO]  CONTENT GOES BELOW ------->

<!------====-- CONTENT GOES ABOVE ------->

--------------------------------------------


<!-----------------------[  Links to Platform Policies  ]-------<recommended> section below-------------->
## How to Accomplish Common User Actions
<!-- 
INSTRUCTIONS: 
- This section links to information useful to any user of this repository new to internal GitHub policies & workflows.
-->

 If you have trouble doing something related to this repository, please keep in mind that the following actions require 
 using [GitHub inside Microsoft (GiM) tooling](https://aka.ms/gim/docs) and not the normal GitHub visible user interface!
- [Switching between EMU GitHub and normal GitHub without logging out and back in constantly](https://aka.ms/StartRight/README-Template/maintainingMultipleAccount)
- [Creating a repository](https://aka.ms/StartRight)
- [Changing repository visibility](https://aka.ms/StartRight/README-Template/policies/jit) 
- [Gaining repository permissions, access, and roles](https://aka.ms/StartRight/README-TEmplates/gim/policies/access)
- [Enabling easy access to your low sensitivity and widely applicable repository by setting it to Internal Visibility and having any FTE who wants to see it join the 1ES Enterprise Visibility MyAccess Group](https://aka.ms/StartRight/README-Template/gim/innersource-access)
- [Migrating repositories](https://aka.ms/StartRight/README-Template/troubleshoot/migration)
- [Setting branch protection](https://aka.ms/StartRight/README-Template/gim/policies/branch-protection)
- [Setting up GitHubActions](https://aka.ms/StartRight/README-Template/policies/actions)
- [and other actions](https://aka.ms/StartRight/README-Template/gim/policies)

This README started as a template provided as part of the 
[StartRight](https://aka.ms/gim/docs/startright) tool that is used to create new repositories safely. Feedback on the
[README template](https://aka.ms/StartRight/README-Template) used in this repository is requested as an issue. 

<!-- version: 2023-04-07 [Do not delete this line, it is used for analytics that drive template improvements] -->
