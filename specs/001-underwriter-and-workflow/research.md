# Research: Underwriter UI and Workflow

**Feature**: 001-underwriter-and-workflow  
**Date**: 2025-12-17  
**Phase**: 0 - Technical Research and Decision Making

---

## Overview

This document captures all technical research decisions for building a Vue.js frontend that enables underwriters to upload documents, review AI processing results, and provide feedback. All decisions are made with POC constraints in mind: no authentication, fail-fast error handling, and best-effort performance.

---

## 1. Vue 3 + TypeScript + Vuetify Setup

### Decision
Use **Vite + Vue 3 (Composition API) + TypeScript + Vuetify 3** for frontend development.

### Rationale
- **Vite**: Modern build tool with fast HMR (Hot Module Replacement), optimized for Vue 3, smaller bundle sizes compared to Webpack
- **Vue 3 Composition API**: Better TypeScript support, improved code organization and reusability, recommended approach for new projects
- **TypeScript**: Type safety reduces runtime errors, better IDE support, enforces API contract adherence
- **Vuetify 3**: Material Design component library with comprehensive UI components (tables, cards, dialogs, forms), reduces custom CSS development time by 60-70%

### Implementation Details
```bash
# Project initialization
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install vuetify@^3.4.0
npm install @mdi/font  # Material Design Icons
```

**tsconfig.json configuration**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**Vuetify plugin setup** (`src/plugins/vuetify.ts`):
```typescript
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976D2',  // Contoso red alternative for POC
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107'
        }
      }
    }
  }
})
```

### Alternatives Considered
- **Nuxt 3**: Adds SSR complexity unnecessary for POC; overkill for internal tool
- **Quasar**: Another component library, but Vuetify has better TypeScript support and documentation
- **Vue 2 Options API**: Legacy approach, poor TypeScript integration, not recommended for new projects

### References
- [Vite Vue TypeScript Starter](https://vitejs.dev/guide/#trying-vite-online)
- [Vue 3 Composition API Guide](https://vuejs.org/guide/typescript/composition-api.html)
- [Vuetify 3 Documentation](https://vuetifyjs.com/en/getting-started/installation/)

---

## 2. PDF Viewer Integration

### Decision
Use **PDF.js** with custom Vue 3 wrapper component for rendering and highlighting.

### Rationale
- **PDF.js**: Mozilla's battle-tested PDF rendering library, used by Firefox, most mature JS PDF solution
- **Highlighting Support**: PDF.js provides text layer that enables search, selection, and custom highlighting
- **Performance**: Lazy loading pages, canvas-based rendering handles large documents efficiently
- **No Server Dependencies**: Client-side rendering, no need for backend PDF processing

### Implementation Details

**Installation**:
```bash
npm install pdfjs-dist@^3.11.174
```

**DocumentViewer Component** (`src/components/document/DocumentViewer.vue`):
```typescript
import * as pdfjsLib from 'pdfjs-dist'
import 'pdfjs-dist/web/pdf_viewer.css'

// Configure worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

const loadPDF = async (url: string) => {
  const loadingTask = pdfjsLib.getDocument(url)
  const pdf = await loadingTask.promise
  // Render pages to canvas elements
}

const highlightText = (pageNum: number, bbox: { x: number, y: number, width: number, height: number }) => {
  // Overlay SVG highlight on canvas
  // Use absolute positioning with computed coordinates
}

const scrollToPage = (pageNum: number) => {
  // Smooth scroll to target page
  const pageElement = document.getElementById(`page-${pageNum}`)
  pageElement?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
```

**Citation Click Flow**:
1. User clicks citation in summary → emits `citation-clicked` event with page number and bounding box
2. Parent component calls `DocumentViewer.scrollToPage(pageNum)`
3. `DocumentViewer` scrolls to page and calls `highlightText(pageNum, bbox)`
4. Highlight overlay rendered as SVG rect with yellow background, 30% opacity

### Performance Considerations
- **Lazy Page Rendering**: Only render pages visible in viewport + 1 page buffer
- **Canvas Pooling**: Reuse canvas elements for off-screen pages
- **Text Layer Optimization**: Render text layer only when user interacts (search, highlight)
- **Large File Warning**: Show warning for PDFs > 50 pages, disable thumbnail preview

### Alternatives Considered
- **vue-pdf-embed**: Third-party Vue wrapper, but lacks fine-grained control over highlighting and performance
- **iframe with browser PDF viewer**: No programmatic control over highlighting or scrolling
- **Server-side PDF-to-image conversion**: Adds backend complexity, slower, requires backend changes

### References
- [PDF.js Documentation](https://mozilla.github.io/pdf.js/)
- [PDF.js Text Layer Example](https://github.com/mozilla/pdf.js/blob/master/examples/components/pageviewer.js)

---

## 3. API Integration Patterns

### Decision
Use **Axios** with TypeScript types generated from OpenAPI specifications.

### Rationale
- **Axios over Fetch**: Built-in interceptors for global error handling, automatic JSON parsing, request/response transformation, better timeout handling
- **Fail-Fast Error Handling**: Axios interceptors enable centralized error handling aligned with spec requirement (no retries)
- **Type Safety**: OpenAPI TypeScript generator (openapi-typescript) creates types from backend API specs
- **File Upload**: Axios provides upload progress tracking via `onUploadProgress` callback

### Implementation Details

**Installation**:
```bash
npm install axios@^1.6.0
npm install --save-dev openapi-typescript
```

**Base API Client** (`src/services/api.ts`):
```typescript
import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for document processing
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling (FAIL IMMEDIATELY - no retries)
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Log error for debugging
    console.error('API Error:', error.response?.data || error.message)
    
    // Return error immediately without retry
    return Promise.reject(error)
  }
)

export default apiClient
```

**Document Service** (`src/services/documentsService.ts`):
```typescript
import apiClient from './api'
import type { components } from './generated/api-types' // Generated from OpenAPI

type Document = components['schemas']['Document']
type ProcessingStatus = components['schemas']['ProcessingStatus']

export const documentsService = {
  async uploadDocument(caseId: string, file: File, onProgress?: (progress: number) => void): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('case_id', caseId)
    
    const response = await apiClient.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress?.(progress)
        }
      }
    })
    
    return response.data
  },
  
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/documents/${documentId}`)
    return response.data
  },
  
  async getProcessingStatus(documentId: string): Promise<ProcessingStatus> {
    const response = await apiClient.get<ProcessingStatus>(`/documents/${documentId}/status`)
    return response.data
  }
}
```

**Error Handling in Components**:
```typescript
// In Vue component
try {
  await documentsService.uploadDocument(caseId, file)
} catch (error) {
  if (axios.isAxiosError(error)) {
    // Display user-friendly error message
    if (error.response?.status === 400) {
      showError('Invalid file format. Please upload a PDF file under 20MB.')
    } else if (error.response?.status === 500) {
      showError('Azure OpenAI service is unavailable. Please try again later.')
    } else {
      showError('Document upload failed. Please try again.')
    }
  }
}
```

### OpenAPI Type Generation
```bash
# Generate TypeScript types from OpenAPI spec
npx openapi-typescript http://localhost:8000/api/openapi.json -o src/services/generated/api-types.ts
```

### Alternatives Considered
- **Fetch API**: Requires manual error handling, no interceptors, verbose timeout logic
- **Vue Query / TanStack Query**: Adds caching complexity unnecessary for POC; fail-fast requirement conflicts with automatic retries
- **Manual TypeScript types**: Error-prone, out of sync with backend, maintenance burden

### References
- [Axios Documentation](https://axios-http.com/docs/intro)
- [openapi-typescript](https://github.com/drwpow/openapi-typescript)

---

## 4. State Management Strategy

### Decision
Use **Pinia** with domain-specific stores (cases, documents, feedback).

### Rationale
- **Pinia**: Official Vue 3 state management, simpler API than Vuex, better TypeScript support, composition API integration
- **Domain Stores**: Separate stores for cases, documents, feedback align with entity boundaries, prevent god object anti-pattern
- **Server-Driven State**: POC uses polling for status updates (no WebSockets); store fetches latest state from API
- **No Optimistic Updates**: Fail-fast requirement means UI waits for server confirmation before updating state

### Implementation Details

**Documents Store** (`src/stores/documents.ts`):
```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { documentsService } from '@/services/documentsService'
import type { Document, ProcessingStatus } from '@/types/document'

export const useDocumentsStore = defineStore('documents', () => {
  // State
  const documents = ref<Map<string, Document>>(new Map())
  const currentDocument = ref<Document | null>(null)
  const uploadProgress = ref<number>(0)
  const isUploading = ref<boolean>(false)
  const error = ref<string | null>(null)
  
  // Getters
  const getDocumentById = computed(() => (id: string) => documents.value.get(id))
  
  // Actions
  async function uploadDocument(caseId: string, file: File) {
    isUploading.value = true
    error.value = null
    uploadProgress.value = 0
    
    try {
      const document = await documentsService.uploadDocument(
        caseId, 
        file, 
        (progress) => { uploadProgress.value = progress }
      )
      documents.value.set(document.id, document)
      currentDocument.value = document
      
      // Start polling for processing status
      pollProcessingStatus(document.id)
      
      return document
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Upload failed'
      throw err
    } finally {
      isUploading.value = false
    }
  }
  
  async function pollProcessingStatus(documentId: string) {
    const maxAttempts = 60 // 5 minutes with 5-second intervals
    let attempts = 0
    
    const poll = async () => {
      if (attempts >= maxAttempts) {
        error.value = 'Processing timeout - please refresh'
        return
      }
      
      try {
        const status = await documentsService.getProcessingStatus(documentId)
        const doc = documents.value.get(documentId)
        if (doc) {
          doc.processing_status = status.status
          doc.progress_percentage = status.progress_percentage
        }
        
        if (status.status === 'completed' || status.status === 'failed') {
          // Fetch full document with results
          await fetchDocument(documentId)
          return
        }
        
        // Continue polling
        attempts++
        setTimeout(poll, 5000)
      } catch (err) {
        error.value = 'Failed to fetch processing status'
      }
    }
    
    poll()
  }
  
  async function fetchDocument(documentId: string) {
    try {
      const document = await documentsService.getDocument(documentId)
      documents.value.set(document.id, document)
      if (currentDocument.value?.id === documentId) {
        currentDocument.value = document
      }
      return document
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Fetch failed'
      throw err
    }
  }
  
  return {
    documents,
    currentDocument,
    uploadProgress,
    isUploading,
    error,
    getDocumentById,
    uploadDocument,
    fetchDocument
  }
})
```

**Store Usage in Components**:
```typescript
<script setup lang="ts">
import { useDocumentsStore } from '@/stores/documents'

const documentsStore = useDocumentsStore()

const handleUpload = async (file: File) => {
  try {
    await documentsStore.uploadDocument(currentCaseId, file)
    router.push(`/documents/${documentsStore.currentDocument?.id}`)
  } catch (error) {
    // Error already captured in store
  }
}
</script>
```

### Polling vs WebSockets Decision
**Decision**: Use polling for POC.

**Rationale**:
- Simpler implementation, no WebSocket server setup required
- Adequate for POC with small user base
- 5-second poll interval acceptable for 5-minute processing time
- Production can upgrade to WebSockets without frontend architecture changes

### Alternatives Considered
- **Vuex**: Legacy option, verbose compared to Pinia, poor TypeScript support
- **Composition API with provide/inject**: No built-in dev tools, harder to debug, no persistence plugins
- **Context API pattern**: Requires manual reactive state management, boilerplate-heavy

### References
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue 3 State Management Guide](https://vuejs.org/guide/scaling-up/state-management.html)

---

## 5. Testing Approach

### Decision
Use **Vitest** for unit/component testing and **Playwright** for E2E testing.

### Rationale
- **Vitest**: Vite-native test runner, fast, same config as Vite, Jest-compatible API, excellent TypeScript support
- **Playwright**: Multi-browser support (Chromium, Firefox, WebKit), auto-waiting reduces flaky tests, better debugging tools than Cypress
- **Testing Library**: Vue Testing Library for component tests, promotes user-centric testing

### Implementation Details

**Installation**:
```bash
npm install --save-dev vitest @vue/test-utils @testing-library/vue
npm install --save-dev @playwright/test
```

**Vitest Configuration** (`vite.config.ts`):
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html']
    }
  }
})
```

**Component Test Example** (`tests/unit/components/DocumentUpload.spec.ts`):
```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import DocumentUpload from '@/components/document/DocumentUpload.vue'
import { useDocumentsStore } from '@/stores/documents'

describe('DocumentUpload', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should validate file type and size', async () => {
    const wrapper = mount(DocumentUpload, {
      props: { caseId: 'case-123' }
    })
    
    // Create mock file (non-PDF)
    const file = new File(['content'], 'test.txt', { type: 'text/plain' })
    const input = wrapper.find('input[type="file"]')
    
    // Simulate file selection
    await input.trigger('change', { target: { files: [file] } })
    
    // Should show error message
    expect(wrapper.text()).toContain('PDF files only')
  })
  
  it('should upload valid file', async () => {
    const documentsStore = useDocumentsStore()
    vi.spyOn(documentsStore, 'uploadDocument').mockResolvedValue({ id: 'doc-123' })
    
    const wrapper = mount(DocumentUpload, {
      props: { caseId: 'case-123' }
    })
    
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const input = wrapper.find('input[type="file"]')
    await input.trigger('change', { target: { files: [file] } })
    
    const uploadButton = wrapper.find('button[type="submit"]')
    await uploadButton.trigger('click')
    
    expect(documentsStore.uploadDocument).toHaveBeenCalledWith('case-123', file)
  })
})
```

**E2E Test Example** (`tests/e2e/document-workflow.spec.ts`):
```typescript
import { test, expect } from '@playwright/test'

test('complete document review workflow', async ({ page }) => {
  // Navigate to dashboard
  await page.goto('http://localhost:5173')
  
  // Create new case
  await page.click('button:has-text("New Case")')
  await page.fill('input[name="case-name"]', 'Test Application')
  await page.click('button:has-text("Create")')
  
  // Upload document
  await page.setInputFiles('input[type="file"]', './tests/fixtures/sample-form-a.pdf')
  await page.click('button:has-text("Upload")')
  
  // Wait for processing (mock or use test backend)
  await expect(page.locator('text=Processing...')).toBeVisible()
  await expect(page.locator('text=Completed')).toBeVisible({ timeout: 10000 })
  
  // Verify results displayed
  await expect(page.locator('text=Form A')).toBeVisible()
  await expect(page.locator('text=Confidence: 98%')).toBeVisible()
  
  // Test citation click
  await page.click('a.citation-link')
  await expect(page.locator('.pdf-highlight')).toBeVisible()
})
```

**Testing Strategy for POC**:
- **Unit Tests**: Critical utility functions (formatters, validators), store actions
- **Component Tests**: User interaction flows (upload, feedback submission), error states
- **E2E Tests**: One happy path per user story, critical error scenarios
- **Coverage Target**: 60%+ for POC (not 80%+ given time constraints)

### Mocking API Calls
```typescript
// tests/setup.ts
import { vi } from 'vitest'
import * as documentsService from '@/services/documentsService'

vi.mock('@/services/documentsService', () => ({
  documentsService: {
    uploadDocument: vi.fn(),
    getDocument: vi.fn(),
    getProcessingStatus: vi.fn()
  }
}))
```

### Alternatives Considered
- **Jest**: Requires additional Babel config for ESM, slower than Vitest
- **Cypress**: Good E2E tool but heavier than Playwright, slower test execution, less reliable auto-waiting

### References
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Vue Testing Library](https://testing-library.com/docs/vue-testing-library/intro/)

---

## Summary of Key Decisions

| Topic | Decision | Key Reasoning |
|-------|----------|---------------|
| **Build Tool** | Vite | Fast HMR, optimized for Vue 3, smaller bundles |
| **Framework** | Vue 3 Composition API + TypeScript | Better TypeScript support, code reusability, modern patterns |
| **UI Library** | Vuetify 3 | Comprehensive components, 60-70% faster UI development |
| **PDF Rendering** | PDF.js with custom wrapper | Mature, client-side, supports highlighting |
| **HTTP Client** | Axios + OpenAPI-generated types | Interceptors for error handling, type safety, upload progress |
| **State Management** | Pinia with domain stores | Simple API, TypeScript support, composition API integration |
| **Status Updates** | Polling (5-second interval) | Simpler than WebSockets for POC, adequate for 5-min processing |
| **Unit Testing** | Vitest + Vue Testing Library | Fast, Vite-native, Jest-compatible |
| **E2E Testing** | Playwright | Multi-browser, reliable auto-waiting, better debugging |

---

## Next Steps (Phase 1)

With all technical unknowns resolved, proceed to Phase 1:
1. Generate `data-model.md` - Define TypeScript types for all entities
2. Generate `contracts/` - Define OpenAPI specs for backend API endpoints
3. Generate `quickstart.md` - Project setup and run instructions

All NEEDS CLARIFICATION items from Technical Context have been resolved.
