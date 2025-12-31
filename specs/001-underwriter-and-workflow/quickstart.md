# Quickstart: Underwriter UI and Workflow

**Feature**: 001-underwriter-and-workflow  
**Date**: 2025-12-17  
**Phase**: 1 - Design and Contracts

---

## Overview

This guide provides step-by-step instructions to set up and run the Vue.js underwriter UI application locally. The frontend communicates with a backend API (assumed to be running separately).

---

## Prerequisites

### Required Software

- **Node.js**: v18.x or v20.x LTS ([download](https://nodejs.org/))
- **npm**: v9.x or v10.x (comes with Node.js)
- **Git**: Latest version
- **VS Code** (recommended) with extensions:
  - Volar (Vue Language Features)
  - TypeScript Vue Plugin
  - ESLint
  - Prettier

### Backend Requirement

The backend API must be running and accessible at `http://localhost:8000/api` (or update `VITE_API_BASE_URL` in `.env.local`).

**Backend endpoints required**:
- POST `/api/cases`
- GET `/api/cases`
- POST `/api/documents/upload`
- GET `/api/documents/{id}`
- GET `/api/documents/{id}/status`
- POST `/api/feedback`

See [contracts/README.md](contracts/README.md) for full API specification.

---

## Initial Setup

### 1. Create Project

```bash
# Navigate to repository root
cd /Users/munishmalhotra/Documents/code/HSBC_IWPB_UW

# Create frontend directory
mkdir frontend
cd frontend

# Initialize Vite + Vue + TypeScript project
npm create vite@latest . -- --template vue-ts

# Install dependencies
npm install
```

### 2. Install Core Dependencies

```bash
# UI Framework
npm install vuetify@^3.4.0
npm install @mdi/font

# Routing and State Management
npm install vue-router@^4.2.0
npm install pinia@^2.1.0

# HTTP Client
npm install axios@^1.6.0

# PDF Viewer
npm install pdfjs-dist@^3.11.174

# Date/Time Utilities
npm install date-fns@^3.0.0
```

### 3. Install Dev Dependencies

```bash
# Testing
npm install --save-dev vitest@^1.0.0
npm install --save-dev @vue/test-utils@^2.4.0
npm install --save-dev @testing-library/vue@^8.0.0
npm install --save-dev @playwright/test@^1.40.0
npm install --save-dev jsdom@^23.0.0

# Type Generation
npm install --save-dev openapi-typescript@^6.7.0

# Code Quality
npm install --save-dev eslint@^8.55.0
npm install --save-dev @typescript-eslint/eslint-plugin@^6.15.0
npm install --save-dev @typescript-eslint/parser@^6.15.0
npm install --save-dev prettier@^3.1.0
npm install --save-dev eslint-config-prettier@^9.1.0
```

---

## Project Configuration

### 1. Update `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts']
  }
})
```

### 2. Update `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    
    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3. Create Environment Files

**`.env.development`** (local development):
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=HSBC Underwriting POC
```

**`.env.production`** (production build):
```env
VITE_API_BASE_URL=https://api.hsbc-underwriting.internal/api
VITE_APP_TITLE=HSBC Underwriting
```

**`.env.local`** (local overrides - gitignored):
```env
# Override API URL if backend runs on different port
VITE_API_BASE_URL=http://localhost:9000/api
```

### 4. Update `package.json` Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "format": "prettier --write src/"
  }
}
```

---

## Project Structure Setup

### 1. Create Directory Structure

```bash
# From frontend/ directory
mkdir -p src/{components/{document,feedback,common},views,stores,services,types,utils,router,plugins}
mkdir -p tests/{unit,e2e,fixtures}
mkdir -p public
```

### 2. Create Vuetify Plugin

**`src/plugins/vuetify.ts`**:
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
          primary: '#1976D2',
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

### 3. Create Router

**`src/router/index.ts`**:
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue')
  },
  {
    path: '/cases/:caseId/upload',
    name: 'DocumentUpload',
    component: () => import('@/views/DocumentUploadView.vue'),
    props: true
  },
  {
    path: '/documents/:documentId',
    name: 'DocumentResults',
    component: () => import('@/views/DocumentResultsView.vue'),
    props: true
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/ErrorView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
```

### 4. Create Base API Client

**`src/services/api.ts`**:
```typescript
import axios, { type AxiosInstance, type AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
```

### 5. Update `src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

app.mount('#app')
```

### 6. Update `src/App.vue`

```vue
<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>{{ appTitle }}</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || 'Underwriter UI')
</script>
```

---

## Generate TypeScript Types from API Contracts

```bash
# Generate types from OpenAPI specs
npx openapi-typescript ../specs/001-underwriter-and-workflow/contracts/cases-api.yaml \
  -o src/types/generated/cases-api.ts

npx openapi-typescript ../specs/001-underwriter-and-workflow/contracts/documents-api.yaml \
  -o src/types/generated/documents-api.ts

npx openapi-typescript ../specs/001-underwriter-and-workflow/contracts/feedback-api.yaml \
  -o src/types/generated/feedback-api.ts
```

---

## Running the Application

### Development Mode

```bash
# Start development server with hot reload
npm run dev

# Application will be available at http://localhost:5173
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Type Checking

```bash
# Run TypeScript type checker
npm run type-check
```

---

## Running Tests

### Unit Tests

```bash
# Run unit tests in watch mode
npm run test

# Run unit tests once with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui
```

### E2E Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode (with browser UI)
npx playwright test --headed

# Run E2E tests in debug mode
npx playwright test --debug
```

---

## Development Workflow

### 1. Start Backend API

Ensure the backend API is running before starting the frontend:

```bash
# In separate terminal, navigate to backend directory
cd backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
python -m uvicorn main:app --reload --port 8000
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

### 3. Access Application

Open browser and navigate to `http://localhost:5173`

### 4. Hot Reload

Any changes to `.vue`, `.ts`, or `.css` files will automatically trigger hot reload.

---

## Troubleshooting

### Port Already in Use

If port 5173 is occupied:

```bash
# Use different port
npm run dev -- --port 3000
```

Or update `vite.config.ts`:
```typescript
server: {
  port: 3000
}
```

### Backend API Not Reachable

1. Verify backend is running: `curl http://localhost:8000/api/cases`
2. Check proxy configuration in `vite.config.ts`
3. Update `VITE_API_BASE_URL` in `.env.local`

### TypeScript Errors

```bash
# Clear TypeScript cache
rm -rf node_modules/.vite

# Reinstall dependencies
npm install

# Run type check
npm run type-check
```

### Vuetify Components Not Styled

Ensure imports in `main.ts`:
```typescript
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
```

---

## VS Code Configuration

**`.vscode/extensions.json`**:
```json
{
  "recommendations": [
    "vue.volar",
    "vue.vscode-typescript-vue-plugin",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ]
}
```

**`.vscode/settings.json`**:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

---

## Next Steps

After setup is complete:

1. **Implement Core Components** (from `data-model.md` and project structure)
   - `DocumentUpload.vue`
   - `DocumentViewer.vue`
   - `ClassificationCard.vue`
   - `ExtractedFieldsList.vue`
   - `SummaryDisplay.vue`

2. **Implement Services** (API integration layer)
   - `casesService.ts`
   - `documentsService.ts`
   - `feedbackService.ts`

3. **Implement Stores** (Pinia state management)
   - `cases.ts`
   - `documents.ts`
   - `feedback.ts`

4. **Implement Views** (page-level components)
   - `DashboardView.vue`
   - `DocumentUploadView.vue`
   - `DocumentResultsView.vue`

5. **Write Tests** as components are implemented

6. **Iterate** based on POC feedback

---

## Useful Commands Reference

```bash
# Development
npm run dev                  # Start dev server
npm run build                # Production build
npm run preview              # Preview production build

# Testing
npm run test                 # Unit tests (watch mode)
npm run test:coverage        # Unit tests with coverage
npm run test:e2e             # E2E tests

# Code Quality
npm run type-check           # TypeScript type checking
npm run lint                 # ESLint
npm run format               # Prettier formatting

# Dependencies
npm install                  # Install all dependencies
npm update                   # Update dependencies
npm outdated                 # Check for outdated packages
```

---

## Additional Resources

- [Vue 3 Documentation](https://vuejs.org/guide/introduction.html)
- [Vuetify 3 Documentation](https://vuetifyjs.com/en/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vite Documentation](https://vitejs.dev/guide/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
