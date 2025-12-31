# Tasks: Underwriter UI and Workflow for Document Processing

**Feature**: 001-underwriter-and-workflow  
**Generated**: 2025-12-18  
**Input**: Design documents from `/specs/001-underwriter-and-workflow/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are omitted per mode instructions. Focus is on functional implementation for POC validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Vue.js application structure

- [X] T001 Create frontend project directory structure per implementation plan
- [X] T002 Initialize Vite + Vue 3 + TypeScript project with dependencies from quickstart.md
- [X] T003 [P] Install and configure Vuetify 3 UI framework in frontend/src/plugins/vuetify.ts
- [X] T004 [P] Install and configure Vue Router in frontend/src/router/index.ts
- [X] T005 [P] Install and configure Pinia state management in frontend/src/main.ts
- [X] T006 [P] Install Axios and PDF.js dependencies per research.md
- [X] T007 [P] Configure TypeScript compiler options in frontend/tsconfig.json
- [X] T008 [P] Setup Vite configuration with API proxy in frontend/vite.config.ts
- [X] T009 [P] Create environment files (.env.development, .env.production) per quickstart.md
- [X] T010 [P] Configure ESLint and Prettier for code quality

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Create base API client with Axios interceptors and error handling in frontend/src/services/api.ts
- [ ] T012 [P] Generate TypeScript types from OpenAPI specs into frontend/src/types/generated/
- [X] T013 [P] Define core TypeScript interfaces (Case, Document, ProcessingStatus) in frontend/src/types/
- [X] T014 [P] Define classification and extraction TypeScript interfaces in frontend/src/types/
- [X] T015 [P] Define summary and feedback TypeScript interfaces in frontend/src/types/
- [X] T016 [P] Create utility functions for formatting (dates, confidence scores) in frontend/src/utils/formatters.ts
- [X] T017 [P] Create client-side validation functions in frontend/src/utils/validators.ts
- [X] T018 [P] Define constants (file size limits, poll intervals) in frontend/src/utils/constants.ts
- [X] T019 Update App.vue root component with Vuetify app shell and navigation bar in frontend/src/App.vue
- [X] T020 Create router configuration with routes for all views in frontend/src/router/index.ts
- [X] T021 [P] Create common LoadingSpinner component in frontend/src/components/common/LoadingSpinner.vue
- [X] T022 [P] Create common ErrorMessage component in frontend/src/components/common/ErrorMessage.vue
- [X] T023 [P] Create common StatusBadge component in frontend/src/components/common/StatusBadge.vue

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Review Document Processing Results (Priority: P1) 🎯 MVP

**Goal**: Enable underwriters to upload an insurance application document and view AI-generated classification, extracted fields, and summary to understand the application without reading the entire document manually

**Independent Test**: Upload a sample document (sample-form-a.pdf), wait for processing completion, view results page showing classification type (Form A), all extracted fields (applicant name, DOB, policy amount, etc.) with confidence scores, and document summary with citations - verify all elements are visible and accurate compared to manual review

### Implementation for User Story 1

**US1 - Core Services (API Integration)**

- [X] T024 [P] [US1] Implement cases service with create/list/get methods in frontend/src/services/casesService.ts
- [X] T025 [P] [US1] Implement documents service with upload/get/status methods in frontend/src/services/documentsService.ts
- [X] T026 [US1] Create cases Pinia store with state management and polling logic in frontend/src/stores/cases.ts
- [X] T027 [US1] Create documents Pinia store with upload progress and status polling in frontend/src/stores/documents.ts

**US1 - Document Upload Components**

- [ ] T028 [US1] Create DocumentUpload component with file validation (PDF, 20MB limit) in frontend/src/components/document/DocumentUpload.vue
- [X] T029 [US1] Create DocumentUploadView page with case selection and upload UI in frontend/src/views/DocumentUploadView.vue

**US1 - Document Results Display Components**

- [ ] T030 [P] [US1] Create ClassificationCard component displaying document type and confidence in frontend/src/components/document/ClassificationCard.vue
- [ ] T031 [P] [US1] Create ExtractedFieldsList component showing fields with confidence scores in frontend/src/components/document/ExtractedFieldsList.vue
- [ ] T032 [P] [US1] Create SummaryDisplay component with citation links in frontend/src/components/document/SummaryDisplay.vue
- [X] T033 [US1] Create DocumentResultsView page integrating all result components in frontend/src/views/DocumentResultsView.vue

**US1 - PDF Viewer Integration**

- [ ] T034 [US1] Create DocumentViewer component with PDF.js integration for rendering in frontend/src/components/document/DocumentViewer.vue
- [ ] T035 [US1] Implement PDF page navigation and zoom controls in DocumentViewer component
- [ ] T036 [US1] Implement text highlighting functionality for citations in DocumentViewer component
- [ ] T037 [US1] Add scroll-to-page and highlight-on-click for citation links in DocumentViewer component

**US1 - Dashboard for Document Queue**

- [X] T038 [US1] Create DashboardView with case and document list display in frontend/src/views/DashboardView.vue
- [X] T039 [US1] Add case creation dialog to DashboardView
- [X] T040 [US1] Add document status indicators (Pending, Processing, Completed, Failed) in DashboardView
- [X] T041 [US1] Add navigation from dashboard to document results page

**US1 - Error Handling and Loading States**

- [ ] T042 [US1] Add upload error handling with user-friendly messages in DocumentUpload component
- [ ] T043 [US1] Add processing status polling with progress indicators in DocumentResultsView
- [ ] T044 [US1] Create ErrorView page for API failures and 404s in frontend/src/views/ErrorView.vue
- [ ] T045 [US1] Add loading spinners to all async operations (upload, polling, fetch)

**Checkpoint**: At this point, User Story 1 should be fully functional - underwriters can upload documents and view complete results

---

## Phase 4: User Story 2 - Provide Feedback on AI Outputs (Priority: P2)

**Goal**: Enable underwriters to mark AI-generated outputs as correct or incorrect to help the data science team improve model accuracy and build a feedback dataset for future training

**Independent Test**: View any processed document result, click "Mark as Incorrect" on an extracted field, provide corrected value ("John Smith"), click "Rate Summary" with 4 stars and comment, submit feedback - verify feedback is saved and can be retrieved via backend API

### Implementation for User Story 2

**US2 - Feedback Services**

- [ ] T046 [US2] Implement feedback service with submit methods in frontend/src/services/feedbackService.ts
- [ ] T047 [US2] Create feedback Pinia store for managing feedback state in frontend/src/stores/feedback.ts

**US2 - Feedback Components**

- [ ] T048 [P] [US2] Create FieldFeedback component for marking fields correct/incorrect in frontend/src/components/feedback/FieldFeedback.vue
- [ ] T049 [P] [US2] Create SummaryRating component with star rating and comments in frontend/src/components/feedback/SummaryRating.vue
- [ ] T050 [US2] Integrate FieldFeedback into ExtractedFieldsList component from US1
- [ ] T051 [US2] Integrate SummaryRating into SummaryDisplay component from US1

**US2 - Feedback Submission Flow**

- [ ] T052 [US2] Add feedback submission handlers in DocumentResultsView
- [ ] T053 [US2] Add confirmation messages after successful feedback submission
- [ ] T054 [US2] Add error handling for feedback submission failures

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - underwriters can review results and provide feedback

---

## Phase 5: User Story 3 - Navigate and Compare Source Documents (Priority: P2)

**Goal**: Enable underwriters to view the original source document alongside AI outputs to verify extraction accuracy and understand context for citations and summaries

**Independent Test**: Display a processed document result with split view - PDF viewer on left side showing original document, AI outputs on right side - click on an extracted field value, verify corresponding location in PDF is highlighted - click citation [1] in summary, verify PDF scrolls to cited page and highlights text

### Implementation for User Story 3

**US3 - Split View Layout**

- [ ] T055 [US3] Refactor DocumentResultsView to support split-view layout in frontend/src/views/DocumentResultsView.vue
- [ ] T056 [US3] Add view toggle (split-view vs single-view) in DocumentResultsView
- [ ] T057 [US3] Implement responsive layout for split view with resizable panels

**US3 - Citation Integration**

- [ ] T058 [US3] Create CitationLink component for clickable citations in frontend/src/components/document/CitationLink.vue
- [ ] T059 [US3] Update SummaryDisplay to use CitationLink component for inline citations
- [ ] T060 [US3] Implement citation click handler to emit events to DocumentViewer

**US3 - Field Highlighting Integration**

- [ ] T061 [US3] Add clickable field values in ExtractedFieldsList component
- [ ] T062 [US3] Implement field click handler to emit source location to DocumentViewer
- [ ] T063 [US3] Test highlighting accuracy for fields across different pages

**US3 - Enhanced PDF Viewer Features**

- [ ] T064 [US3] Add support for multiple concurrent highlights in DocumentViewer
- [ ] T065 [US3] Implement highlight color coding (yellow for citations, blue for fields)
- [ ] T066 [US3] Add smooth scrolling animation for navigation between pages

**Checkpoint**: All three priority-2 user stories (US1, US2, US3) should now be independently functional

---

## Phase 6: User Story 4 - Manage Document Queue and Status (Priority: P3)

**Goal**: Enable underwriters to view all uploaded documents in a queue, track their processing status, and prioritize which documents to review next

**Independent Test**: Upload 3 different documents (Form A, Form B, one that fails), view dashboard showing all 3 with distinct statuses (Completed, Completed, Failed), filter by status showing only "Completed" (2 documents), sort by upload time (newest first), click a document row to navigate to its results page

### Implementation for User Story 4

**US4 - Enhanced Dashboard Features**

- [ ] T067 [US4] Add filtering controls (status, document type) to DashboardView in frontend/src/views/DashboardView.vue
- [ ] T068 [US4] Add sorting controls (date, status, type, confidence) to DashboardView
- [ ] T069 [US4] Implement filter and sort logic in cases store in frontend/src/stores/cases.ts
- [ ] T070 [US4] Add search functionality for case/document names in DashboardView

**US4 - Processing Status Details**

- [ ] T071 [US4] Create ProcessingStatusDetail component showing step breakdown in frontend/src/components/document/ProcessingStatusDetail.vue
- [ ] T072 [US4] Add progress bar with percentage to ProcessingStatusDetail component
- [ ] T073 [US4] Add stepper component showing current processing step (OCR → Classification → Extraction → Summarization)
- [ ] T074 [US4] Display estimated completion time for in-progress documents

**US4 - Error State Handling**

- [ ] T075 [US4] Add detailed error messages for failed documents in DashboardView
- [ ] T076 [US4] Add manual retry button for failed documents in DashboardView
- [ ] T077 [US4] Implement retry logic in documents store to reset status to Pending

**US4 - Performance and Pagination**

- [ ] T078 [US4] Implement pagination for document list (50 items per page)
- [ ] T079 [US4] Add virtual scrolling for large document lists (100+ items)
- [ ] T080 [US4] Optimize dashboard loading performance with lazy loading

**Checkpoint**: All four user stories should now be independently functional with complete workflow coverage

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and overall application quality

**Documentation and Refinement**

- [ ] T081 [P] Update frontend/README.md with setup instructions from quickstart.md
- [ ] T082 [P] Add JSDoc comments to complex service and store functions
- [ ] T083 [P] Add component prop documentation with TypeScript types
- [ ] T084 Validate quickstart.md instructions work on clean environment

**User Experience Improvements**

- [ ] T085 [P] Add keyboard shortcuts for common actions (upload, submit feedback)
- [ ] T086 [P] Add tooltips to confidence score badges explaining thresholds
- [ ] T087 Implement success notifications (toast/snackbar) for all user actions
- [ ] T088 Add loading skeleton screens for document results page

**Code Quality and Optimization**

- [ ] T089 Remove unused dependencies and code from package.json
- [ ] T090 Run ESLint and fix any linting warnings across all files
- [ ] T091 Run Prettier to format all code consistently
- [ ] T092 Optimize bundle size by analyzing with vite-plugin-visualizer

**Performance Optimization**

- [ ] T093 Implement lazy loading for PDF.js worker and large components
- [ ] T094 Add caching strategy for document results in Pinia stores
- [ ] T095 Optimize image assets and PDF thumbnails
- [ ] T096 Add performance monitoring for critical user flows (upload, results display)

**Security and Validation**

- [ ] T097 Review and strengthen client-side validation for all form inputs
- [ ] T098 Sanitize user-provided text before displaying (XSS prevention)
- [ ] T099 Add Content Security Policy headers to Vite config
- [ ] T100 Review error messages to ensure no sensitive data leakage

**Browser Compatibility**

- [ ] T101 Test application in Chrome, Firefox, Edge, Safari (last 2 versions)
- [ ] T102 Fix any browser-specific CSS or JavaScript issues
- [ ] T103 Add polyfills if needed for target browsers

**Final Validation**

- [ ] T104 End-to-end walkthrough of all user stories with sample data
- [ ] T105 Verify all success criteria from spec.md are met
- [ ] T106 Prepare demo script and sample documents for stakeholder presentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP target
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Can start in parallel with US1 if staffed, but integrates with US1 components
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) AND User Story 1 Phase 3 - Enhances US1 with split view
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) - Can start in parallel, enhances dashboard from US1
- **Polish (Phase 7)**: Depends on completion of desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Integrates with US1 components (ExtractedFieldsList, SummaryDisplay) but feedback features are independently testable
- **User Story 3 (P2)**: Depends on US1 DocumentViewer and results components - Enhances existing views
- **User Story 4 (P3)**: Enhances dashboard from US1 but filtering/sorting features are independently testable

### Within Each User Story

**US1 Flow**:
1. Services and stores (T024-T027) before components
2. Upload components (T028-T029) can be parallel with results components
3. Results display components (T030-T033) in parallel
4. PDF viewer (T034-T037) after DocumentViewer component exists
5. Dashboard (T038-T041) after stores exist
6. Error handling (T042-T045) last

**US2 Flow**:
1. Feedback service and store (T046-T047) before components
2. Feedback components (T048-T049) in parallel
3. Integration (T050-T051) after both components and US1 components exist
4. Submission flow (T052-T054) last

**US3 Flow**:
1. Split-view layout (T055-T057) first
2. Citation and field components (T058-T062) in parallel
3. Enhanced PDF features (T064-T066) after basic viewer works

**US4 Flow**:
1. Dashboard filters/sort (T067-T070) first
2. Status detail components (T071-T074) in parallel
3. Error handling (T075-T077) after status components
4. Performance (T078-T080) last

### Parallel Opportunities

**Setup Phase (Phase 1)**: All tasks T003-T010 marked [P] can run in parallel

**Foundational Phase (Phase 2)**: Tasks T012-T018 (type definitions and utils) can run in parallel, T021-T023 (common components) can run in parallel

**User Story 1**:
- Services: T024 and T025 in parallel
- Result components: T030, T031, T032 in parallel
- PDF viewer development can overlap with other component work

**User Story 2**:
- Feedback components: T048 and T049 in parallel

**User Story 3**:
- Citation and field integration can proceed in parallel

**Cross-Story Parallelism** (with multiple developers):
- After Foundational phase, US1 + US2 + US4 can start in parallel
- US3 must wait for US1 components to exist

**Polish Phase (Phase 7)**: Documentation tasks (T081-T083), UX improvements (T085-T087), code quality tasks (T089-T092) can run in parallel

---

## Parallel Example: User Story 1

```bash
# After services are ready, launch multiple component implementations:
Task: "Create ClassificationCard component in frontend/src/components/document/ClassificationCard.vue"
Task: "Create ExtractedFieldsList component in frontend/src/components/document/ExtractedFieldsList.vue"
Task: "Create SummaryDisplay component in frontend/src/components/document/SummaryDisplay.vue"

# These components work on different files with no shared dependencies
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - Recommended for POC

1. ✅ Complete Phase 1: Setup (T001-T010)
2. ✅ Complete Phase 2: Foundational (T011-T023) - CRITICAL checkpoint
3. ✅ Complete Phase 3: User Story 1 (T024-T045)
4. **STOP and VALIDATE**: Test end-to-end upload and results viewing
5. Demo to stakeholders - MVP is ready!

**Estimated Timeline**: 8-12 days for MVP

### Incremental Delivery (Add Features Progressively)

1. Complete Setup + Foundational → Foundation ready (2-3 days)
2. Add User Story 1 → Test independently → Deploy/Demo (6-8 days) 🎯 **MVP HERE**
3. Add User Story 2 → Test independently → Deploy/Demo (3-4 days)
4. Add User Story 3 → Test independently → Deploy/Demo (3-4 days)
5. Add User Story 4 → Test independently → Deploy/Demo (3-4 days)
6. Polish phase → Final refinements (2-3 days)

**Total Estimated Timeline**: 19-26 days (4-5 weeks) for complete implementation

### Parallel Team Strategy (3+ Developers)

1. **All Team**: Complete Setup + Foundational together (2-3 days)
2. **After Foundational checkpoint**:
   - **Developer A**: User Story 1 (P1) - Core functionality (6-8 days)
   - **Developer B**: User Story 2 (P2) - Feedback features (3-4 days)
   - **Developer C**: User Story 4 (P3) - Dashboard enhancements (3-4 days)
3. **Developer A continues**: User Story 3 (P2) - Split view (3-4 days) - Depends on US1 completion
4. **All Team**: Polish phase together (2-3 days)

**Parallel Timeline**: 13-18 days (2.5-3.5 weeks) with 3 developers

---

## Task Count Summary

- **Total Tasks**: 106 tasks
- **Phase 1 - Setup**: 10 tasks
- **Phase 2 - Foundational**: 13 tasks (BLOCKING)
- **Phase 3 - User Story 1 (MVP)**: 22 tasks
- **Phase 4 - User Story 2**: 9 tasks
- **Phase 5 - User Story 3**: 12 tasks
- **Phase 6 - User Story 4**: 14 tasks
- **Phase 7 - Polish**: 26 tasks

**Parallel Task Opportunities**: 35 tasks marked [P] across all phases

**MVP Scope (Phases 1-3 only)**: 45 tasks for complete User Story 1 implementation

---

## Success Criteria Mapping

Each task contributes to specific success criteria from spec.md:

| Success Criterion | Related Tasks |
|-------------------|---------------|
| **SC-001**: Upload + view results < 5 min | T024-T045 (US1 - entire upload and results flow) |
| **SC-002**: 90% locate fields in < 30s | T030-T031 (ExtractedFieldsList component design) |
| **SC-003**: Citation navigation < 2s delay | T034-T037, T058-T060 (PDF viewer and citation integration) |
| **SC-004**: 100% feedback saved | T046-T054 (US2 - feedback service and submission) |
| **SC-005**: All mandatory fields displayed | T031 (ExtractedFieldsList completeness validation) |
| **SC-007**: Zero data loss | T011, T024-T025 (API client error handling) |
| **SC-008**: Actionable error messages | T022, T042-T044 (ErrorMessage component and error handling) |
| **SC-009**: Dashboard loads < 3s | T038-T041, T078-T080 (Dashboard optimization) |
| **SC-010**: Split-view 50% faster | T055-T057 (Split-view layout implementation) |

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe for parallel execution
- **[Story] labels**: Map each task to specific user story (US1, US2, US3, US4) for traceability
- **Independent stories**: Each user story can be tested without others (after Foundational phase)
- **POC focus**: No authentication, no comprehensive tests - rapid prototyping prioritized
- **Commit strategy**: Commit after each task or logical group of related tasks
- **Validation checkpoints**: Stop after each phase completion to verify functionality
- **Avoid**: Vague descriptions, working on same files simultaneously, creating cross-story dependencies

---

## Next Actions

1. **Review** this task breakdown with team and stakeholders
2. **Choose strategy**: MVP-only, Incremental, or Parallel team approach
3. **Start with Phase 1**: Project setup and configuration
4. **Complete Phase 2**: CRITICAL - blocks all feature work
5. **Implement Phase 3**: User Story 1 for MVP demonstration
6. **Iterate**: Add remaining user stories based on POC feedback

---

**Tasks Status**: ✅ COMPLETE - Ready for Phase 1 implementation  
**Branch**: `001-underwriter-and-workflow`  
**Last Updated**: 2025-12-18
