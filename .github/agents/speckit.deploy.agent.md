description: Provision infrastructure and deploy application components using mandatory user provided resource configuration, component driven inputs, and strict blocking deployment semantics
User Input

$ARGUMENTS

You MUST consider the user input before proceeding if it is not empty.

Supported arguments

environment=dev | staging | prod

component=<component-type>

dry-run

force

infra-only

deploy-only

Core principle (NON NEGOTIABLE)

The workflow MUST NOT:

infer critical infrastructure values

assume defaults for cost, capacity, or region

reuse resources without explicit user consent

The workflow MUST:

explicitly ask the user for required inputs

validate inputs

summarize inputs

get confirmation before proceeding

Global shell execution rules (MANDATORY)

All shell commands MUST execute synchronously

Commands MUST block until process exit

Exit codes MUST be captured

Non zero exit code MUST halt execution

No parallel execution unless explicitly allowed

Deployment success requires verified terminal state

Supported deployment components

The user MUST choose a component.

Supported values

azure-app-service

azure-container-app

azure-function-app

azure-aks

custom-container

If component is missing

STOP

Ask user to choose one

Tooling preflight (component aware)
Common checks

Shell command
az version

Shell command
az account show

Both MUST succeed before proceeding.

Component specific tooling

If component is Azure based

az bicep version

az bicep build --help

If component uses containers

docker version

Failure → STOP

Outline
1. Repository and task validation

Validate git repository

Validate tasks.md completion

Ask confirmation if incomplete

2. Load deployment context

REQUIRED

Read plan.md

Read tasks.md

IF EXISTS

Read deploy.md

NO shell execution here.

3. Mandatory resource input collection (BLOCKING)

This step is REQUIRED and CANNOT be skipped unless force is provided.

The workflow MUST ask the user all required inputs for the selected component.

Component input contracts
Component: azure-app-service

Ask the user explicitly for:

Azure basics

Azure subscription (confirm current one)

Resource group name

Region

App Service Plan

Plan name

SKU (B1, S1, P1v3, etc.)

OS type (Linux or Windows)

Instance count

App Service

App name

Deployment type

Code (zip deploy)

Container (Docker)

If Code deploy

Runtime stack (Node, Python, Java, .NET)

Runtime version

If Container deploy

Image name

Registry

Image tag

Networking

HTTPS only (yes/no)

Deployment slot required (yes/no)

If slot yes

Slot name

Observability

Enable Application Insights (yes/no)

Security

Enable system assigned managed identity (yes/no)

Component: azure-container-app

Ask the user explicitly for:

Resource group

Region

Container App name

Environment name

CPU

Memory

Min replicas

Max replicas

Container image

Ingress type (external/internal)

Exposed port

Component: azure-function-app

Ask the user explicitly for:

Resource group

Region

Function App name

Hosting plan (Consumption / Premium / Dedicated)

Runtime stack and version

Storage account name

OS type

Component: azure-aks

Ask the user explicitly for:

Resource group

Region

Cluster name

Node size

Node count

Kubernetes version

Network plugin

Container registry integration

Component: custom-container

Ask the user explicitly for:

Target platform

Service name

Container image

Registry

CPU

Memory

Port

Public exposure (yes/no)

4. Existing resource detection and decision (MANDATORY)

For each resource named by the user:

Query provider to check if resource exists

If exists

Display resource details

Ask user
Use existing resource or create new? (use/new)

Rules

use → reference resource only

new → generate creation logic

If force flag set

Default to use existing

5. Configuration summary and explicit confirmation

Print a complete configuration summary:

Component type

Environment

Resource group

Region

All resource names

SKUs and capacity

Deployment strategy

Reused vs new resources

Ask user:

Proceed with infrastructure generation and deployment? (yes/no)

If no → HALT
If yes → Continue

6. Infrastructure generation

Generate infra templates based on component

Parameterize ALL user provided inputs

Include creation logic only for new resources

Reference existing resources explicitly

NO deployment here.

7. Infrastructure deployment (STRICT BLOCKING)

Execute provider deployment command

Wait for process exit

Capture deployment identifier

Poll deployment state until terminal

Success state only

Succeeded

Failure states

Failed

Canceled

Timeout

Failure → STOP

If infra-only flag set

STOP

8. Build phase (if applicable)

Execute build commands sequentially

Block on each

Validate outputs

Failure → STOP

9. Application deployment (STRICT BLOCKING)

Execute component specific deployment

Wait for exit

Poll application state

Verify running or ready

Failure → STOP

10. Health verification

Poll health endpoint

Enforce timeout

Failure → STOP

11. Completion and reporting

Only after success:

Mark deployment SUCCESS

Update tasks.md

Print URLs and outputs

Failure handling rules

Any missing required input → STOP

Any command failure → STOP

Any non successful terminal state → STOP

Notes

This command enforces:

Mandatory user supplied infrastructure inputs

Explicit cost and capacity decisions

Safe reuse or creation of resources

Deterministic deployment completion

Nothing is assumed.
Everything is confirmed.