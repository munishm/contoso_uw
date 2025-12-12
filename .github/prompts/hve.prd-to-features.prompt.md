---
agent: hve.ado-prd-to-wit
description: 'Stage 1: Analyze PRD and create Epic + Features only'
---

# Stage 1: Epic & Feature Planning Only

## Workflow Constraints

**Execute Phases 1-3 only with the following modifications:**

### Phase 1: Analyze PRD Artifacts
- Proceed normally - extract all Epic and Feature-level information
- **Skip User Story details** - note them for future but don't elaborate
- Focus on high-level capabilities and Feature boundaries

### Phase 2: Discover Related Codebase Information
- Proceed normally - identify relevant code areas per Feature
- Document which code areas map to which Features

### Phase 3: Discover Related Work Items
- Search for related Epics and Features only
- Document relationships but **do not search for User Stories**

### Phase 4 & 5: SKIP ENTIRELY
- **Do not create User Stories**
- **Do not proceed to refinement phase**

## Output Requirements

### Planning Files
- `planning-log.md` - Mark as "Stage 1 Complete - Features Ready"
- `artifact-analysis.md` - Full PRD analysis
- `work-items.md` - Epic + Features only (User Stories section empty or minimal placeholders)
- `features-handoff.md` - Stage 1 completion artifact

### Handoff Criteria
Before completing Stage 1, ensure:
- All Features clearly scoped with acceptance criteria
- Features linked to Epic (if applicable)
- Each Feature has estimated complexity/size noted
- Related ADO work items documented
- Codebase areas mapped to Features

## Completion Signal

After Phase 3, present summary:
```
✅ Stage 1 Complete: Epic + Features Defined

**Epic**: [Epic title and ID]
**Features**: [List with IDs and brief descriptions]

📋 Next Step: Review and approve Features, then use `hve.ado-features-to-stories.prompt.md` to decompose selected Features into User Stories for upcoming sprints.
```

**STOP execution after this summary.**
