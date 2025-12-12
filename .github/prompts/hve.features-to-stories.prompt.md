---
agent: hve.ado-prd-to-wit
description: 'Stage 2: Decompose specific Features into User Stories for sprint planning'
---

# Stage 2: User Story Decomposition (Sprint-Focused)

## Context & Prerequisites

**Before starting:**
- Stage 1 must be complete (`features-handoff.md` exists)
- **Always ask user** which Feature(s) to decompose (don't assume)
- This prompt is **reusable** - run it once per sprint or Feature batch

## User Input Protocol

**On every invocation, ask user:**

1. **Feature Selection:**
   - "Which Feature(s) should I decompose?" (e.g., "Feature 1", "Features 2, 5, 7")
   - "All remaining Features"
   - "Only Feature X"

2. **Story Scope (if Feature already has Stories):**
   - "Create all Stories for this Feature"
   - "Create Stories for specific areas" (user describes: "Stories for login flow only", "Stories for API integration")
   - "Add N more Stories to existing set"

3. **Refinement Level:**
   - "Standard sprint-sized Stories" (default)
   - "Break down into smaller tasks" (more granular)
   - "High-level Stories only" (coarser)

**Examples of valid user requests:**
- "Decompose Feature 3"
- "Create Stories for Features 1, 4, and 6"
- "Add Stories for the authentication part of Feature 2"
- "Feature 5 already has Stories - add 3 more for the reporting module"
- "Refine existing Stories in Feature 7 to be smaller"

## Workflow Constraints

**Skip Phases 1-3, Execute Modified Phases 4-5:**

### Phase 1-3: SKIP
- **Do not re-analyze PRD** - read existing `artifact-analysis.md`
- **Do not re-discover codebase** - reference existing findings
- **Do not re-search ADO** - use cached related work items

### Phase 4: Targeted Story Creation (Modified)

**Scope limitation based on user input:**
- **Feature-level**: "Decompose Feature X" → Create all Stories for Feature X
- **Multi-feature**: "Decompose Features X, Y, Z" → Create Stories for selected Features
- **Partial-feature**: "Add Stories for login in Feature 2" → Create subset of Stories within Feature
- **Incremental**: "Feature 5 needs 3 more Stories for reporting" → Add to existing Stories

**Check existing Stories first:**
- Read `work-items.md` to see what Stories already exist for requested Feature(s)
- If Stories exist: Ask "Should I add more Stories or refine existing ones?"
- If no Stories: Proceed with full decomposition

**Story criteria:**
- Each Story is sprint-sized (completable in one sprint)
- Clear acceptance criteria per Story
- Dependencies between Stories documented
- Technical implementation notes from codebase analysis
- Sequential Story IDs within each Feature (US-001, US-002, etc.)

**Handle partial Feature decomposition:**
When user requests specific areas within a Feature:
1. Identify the functional area within the Feature scope
2. Create Stories only for that area
3. Mark Feature as "Partially decomposed" in planning-log.md
4. Note which areas still need Stories

**Iterative refinement:**
- Present Stories for selected Feature(s) or areas
- User reviews and provides feedback
- Refine based on feedback (add, modify, split, merge Stories)
- Repeat for next Feature/area when user requests

### Phase 5: Incremental Handoff (Modified)

**Output per iteration:**
- Update `work-items.md` with new Stories under respective Features
- Append to `stories-handoff.md` (cumulative across sprints)
- Update `planning-log.md` with progress: "Feature X decomposed - Y Stories created"

**Do not finalize** until user explicitly says all Features are complete

## Multi-Sprint Usage Pattern

This prompt will be invoked multiple times with various user requests:

**Sprint 1 - Full Feature decomposition:**
```
Agent: Which Feature(s) should I decompose?
User: Decompose Feature 1 and Feature 2
Agent: [Creates all Stories for F1, F2]
Agent: ✅ 8 Stories created for Features 1-2
```

**Sprint 2 - Partial Feature decomposition:**
```
Agent: Which Feature(s) should I decompose?
User: Only create Stories for the authentication part of Feature 3
Agent: [Creates Stories for auth module only within F3]
Agent: ✅ 3 Stories created for Feature 3 (authentication) | Feature 3: Partially decomposed
```

**Sprint 3 - Complete remaining Stories:**
```
Agent: Which Feature(s) should I decompose?
User: Complete the rest of Feature 3
Agent: [Reads existing Stories, creates remaining Stories for F3]
Agent: ✅ 4 additional Stories created for Feature 3 | Total for F3: 7 Stories
```

**Sprint 4 - Add specific Stories:**
```
Agent: Which Feature(s) should I decompose?
User: Feature 2 needs 2 more Stories for error handling
Agent: [Adds Stories to existing Feature 2 Stories]
Agent: ✅ 2 Stories added to Feature 2 (Total: 10 Stories across Features 1-3)
```

**Sprint N - Bulk remaining:**
```
Agent: Which Feature(s) should I decompose?
User: All remaining Features
Agent: [Creates Stories for all Features without Stories]
Agent: ✅ Features 4-7 decomposed | All Features complete - Ready for final handoff
```

## Session Continuity

**On each invocation:**
1. Read `planning-log.md` to understand decomposition status per Feature
2. Read `work-items.md` to see existing Stories and their IDs
3. Present Feature status summary:
   ```
   📋 Feature Decomposition Status:
   - Feature 1: ✅ Complete (5 Stories)
   - Feature 2: ✅ Complete (3 Stories)  
   - Feature 3: 🔄 Partial (2 Stories - auth only)
   - Feature 4: ⏳ Not started
   - Feature 5: ⏳ Not started
   ```
4. **Ask user**: "Which Feature(s) should I work on? (You can specify full Features, partial areas, or additions)"
5. Based on user response:
   - New Feature → Create all Stories
   - Partial Feature → Create Stories for specified area only
   - Existing Feature → Add/refine Stories
6. Update planning files incrementally
7. Preserve all previous work and Story IDs

## Output Requirements

### Per Invocation
- Clear summary of Stories created in this session
- Updated `work-items.md` with new Stories
- Updated `planning-log.md` with progress
- Cumulative Story count across all sessions

### Final Handoff (when all Features done)
Present complete summary:
```
✅ Stage 2 Complete: All Features Decomposed

**Total Stories**: [Count across all sprints]
**Features Covered**: [List of all Features]
**Ready for**: ADO work item creation

📋 Review `stories-handoff.md` for complete work item hierarchy
```

## Key Principle

**Incremental & Reusable**: This prompt is designed to be run multiple times, each time adding User Stories for specific Features without disrupting previous work.
