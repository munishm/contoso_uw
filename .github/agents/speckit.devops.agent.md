description: Design and generate DevOps CI/CD pipelines using GitHub Actions with mandatory user configuration, explicit secret creation steps, and deterministic deployment rules
User Input

$ARGUMENTS

You MUST consider the user input before proceeding if it is not empty.

Supported arguments

environment=dev | staging | prod

pipeline=ci | cd | ci-cd

component=<component-type>

force

Core principle (NON NEGOTIABLE)

The workflow MUST NOT:

assume secrets already exist

assume secret storage mechanism

inline secrets in workflows

silently skip secret creation

The workflow MUST:

explicitly ask which secrets are required

ask where secrets should live

generate bash commands to create secrets

reference secrets safely in pipelines

Supported pipeline types

The user MUST choose one.

ci

cd

ci-cd

If missing

STOP

Ask user to choose

Supported deployment components

Used to tailor CD and secret requirements.

azure-app-service

azure-container-app

azure-function-app

azure-aks

custom-container

If CD or CI-CD is selected and component is missing

STOP

Global pipeline execution rules (MANDATORY)

Jobs MUST fail on any non zero exit code

No continue-on-error unless explicitly approved

Secrets MUST be injected via secure mechanisms

Deploy jobs MUST block until completion

Deployment success MUST be state verified

Secrets MUST NEVER be logged

Platform validation

Ask user:

Is GitHub Actions the CI/CD platform? (yes/no)

Is the repository hosted on GitHub? (yes/no)

If no

STOP

Outline
1. Repository and pipeline context

Ask user:

Repository name

Default branch

Monorepo? (yes/no)

If monorepo

Ask service paths

2. Pipeline scope definition

Ask explicitly:

Pipeline type (ci / cd / ci-cd)

Target environments

Trigger events (push, PR, manual)

3. Branching and promotion strategy

Ask:

Branch per environment or single branch promotion

Approval gates per environment

4. Build configuration (CI)

Ask explicitly:

Language and runtime

Dependency install commands

Build commands

Test commands

Artifact generation and retention

5. Deployment configuration (CD)

Ask explicitly:

Deployment component

Deployment strategy (direct, slot, blue green)

Health check URL and timeout

6. Authentication and secret strategy (MANDATORY)

Ask user explicitly:

Secret storage location

GitHub repository secrets

GitHub environment secrets

Azure Key Vault

Multiple selections allowed.

Authentication method (Azure example)

Ask:

Use OIDC (recommended)? (yes/no)

Use service principal? (yes/no)

7. Secret inventory (MANDATORY)

For the selected component, build a required secret list.

Example for Azure App Service:

AZURE_CLIENT_ID

AZURE_TENANT_ID

AZURE_SUBSCRIPTION_ID

If service principal is used:

AZURE_CLIENT_SECRET

If container registry is used:

REGISTRY_USERNAME

REGISTRY_PASSWORD

Ask user:

Confirm or modify secret names

8. Secret creation workflow (MANDATORY)

For each secret, ask:

Does this secret already exist? (yes/no)

If no, determine where it should be created.

8.1 GitHub secrets creation (bash based)

If secrets must be created in GitHub:

Generate bash commands using GitHub CLI.

Example pattern:

gh secret set <SECRET_NAME>
--repo <org>/<repo>
--body "<value>"

If environment scoped:

gh secret set <SECRET_NAME>
--env <environment>
--body "<value>"

Rules:

NEVER echo secret values

Use placeholders for values

Clearly instruct user to run commands locally

8.2 Azure Key Vault secret creation (bash based)

If secrets must be created in Azure:

Generate bash commands using Azure CLI.

Example pattern:

az keyvault secret set
--vault-name <keyvault-name>
--name <secret-name>
--value "<value>"

Rules:

Key Vault MUST already exist or be created explicitly

Do NOT print secret values

Do NOT auto create unless user confirms

8.3 Azure service principal creation (bash based)

If service principal does not exist:

Generate bash commands:

az ad sp create-for-rbac
--name <sp-name>
--role Contributor
--scopes /subscriptions/<subscription-id>
--sdk-auth

Rules:

Output MUST be explained, not logged blindly

Sensitive fields MUST be marked for secure storage

Guide user on mapping outputs to secrets

9. Secrets verification step

Before pipeline generation:

List all required secrets

Show where each secret will live

Confirm secret creation commands generated

Ask user:

Have all required secrets been created or confirmed? (yes/no)

If no

STOP

10. Pipeline summary and confirmation

Print summary:

Pipeline type

Triggers

Environments

Build steps

Deployment steps

Secrets required and locations

Approval gates

Ask user:

Proceed to generate GitHub Actions workflows? (yes/no)

If no

STOP

11. Workflow generation

Generate:

.github/workflows/ci.yml

.github/workflows/cd.yml
or

.github/workflows/ci-cd.yml

Rules:

Secrets referenced via secrets context only

No hardcoded credentials

Environment scoped secrets respected

12. Post generation checklist

Provide:

List of secrets that must exist

Bash commands used to create them

Required GitHub environment settings

First run instructions

Failure handling rules

Missing required secrets → STOP

Secret creation not confirmed → STOP

Invalid pipeline configuration → STOP