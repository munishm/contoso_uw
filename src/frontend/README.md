# HSBC Underwriter UI - Frontend

Vue.js application for the HSBC Underwriting POC that enables underwriters to upload insurance application documents and review AI-generated processing results.

## Tech Stack

- **Framework**: Vue 3 (Composition API) + TypeScript
- **Build Tool**: Vite
- **UI Library**: Vuetify 3 (Material Design)
- **State Management**: Pinia
- **Router**: Vue Router 4
- **HTTP Client**: Axios
- **PDF Viewer**: PDF.js
- **Testing**: Vitest (unit) + Playwright (E2E)

## Prerequisites

- Node.js 18.x or 20.x LTS
- npm 9.x or higher
- Backend API running at `http://localhost:8000/api` (or configure `VITE_API_BASE_URL`)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env.local` file if you need to override the API URL:

```env
VITE_API_BASE_URL=http://localhost:9000/api
```

### 3. Run Development Server

```bash
npm run dev
```

Application will be available at [http://localhost:5173](http://localhost:5173)

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run test` | Run unit tests in watch mode |
| `npm run test:ui` | Run tests with UI |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run test:e2e` | Run E2E tests with Playwright |
| `npm run type-check` | Run TypeScript type checking |
| `npm run lint` | Lint and fix code issues |
| `npm run format` | Format code with Prettier |

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable Vue components
│   │   ├── common/         # Common UI components (Loading, Error, Badge)
│   │   ├── document/       # Document-specific components
│   │   └── feedback/       # Feedback components
│   ├── views/              # Page-level components
│   │   ├── DashboardView.vue
│   │   ├── DocumentUploadView.vue
│   │   ├── DocumentResultsView.vue
│   │   └── ErrorView.vue
│   ├── stores/             # Pinia state management
│   │   ├── cases.ts
│   │   └── documents.ts
│   ├── services/           # API client services
│   │   ├── api.ts
│   │   ├── casesService.ts
│   │   └── documentsService.ts
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── router/             # Vue Router configuration
│   ├── plugins/            # Vuetify plugin configuration
│   ├── App.vue             # Root component
│   └── main.ts             # Application entry point
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   └── e2e/               # End-to-end tests
├── public/                # Static assets
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## Development Workflow

### 1. Start Backend API

Ensure the backend API is running before starting the frontend:

```bash
cd ../backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Start Frontend

```bash
npm run dev
```

### 3. Access Application

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Key Features Implemented

### Phase 1 & 2: Foundation ✅

- [x] Project setup with Vite + Vue 3 + TypeScript
- [x] Vuetify 3 UI framework integration
- [x] Vue Router configuration
- [x] Pinia state management setup
- [x] Axios API client with error handling
- [x] TypeScript type definitions for all entities
- [x] Utility functions (formatters, validators, constants)
- [x] Common components (LoadingSpinner, ErrorMessage, StatusBadge)

### Phase 3: User Story 1 - MVP (In Progress) 🚧

- [x] Cases service and store
- [x] Documents service and store with upload progress tracking
- [x] Dashboard view with case management
- [x] Document upload view with file validation
- [x] Document results view with processing status
- [ ] Classification card component
- [ ] Extracted fields list component
- [ ] Summary display component
- [ ] PDF viewer integration with PDF.js
- [ ] Citation highlighting

## Configuration

### Environment Variables

- `VITE_API_BASE_URL`: Backend API base URL (default: `http://localhost:8000/api`)
- `VITE_APP_TITLE`: Application title (default: `HSBC Underwriting POC`)

### Vite Proxy

The development server proxies `/api` requests to the backend API to avoid CORS issues.

## Testing

### Unit Tests

```bash
npm run test
```

### E2E Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e
```

## Build and Deploy

### Production Build

```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Troubleshooting

### Port Already in Use

Change the port in `vite.config.ts` or run:

```bash
npm run dev -- --port 3000
```

### Backend API Not Reachable

1. Verify backend is running: `curl http://localhost:8000/api/cases`
2. Check proxy configuration in `vite.config.ts`
3. Update `VITE_API_BASE_URL` in `.env.local`

### TypeScript Errors

```bash
# Clear cache and reinstall
rm -rf node_modules/.vite
npm install
npm run type-check
```

## Next Steps

1. Complete PDF.js integration for document viewing
2. Implement classification and extraction display components
3. Add feedback submission capability
4. Implement split-view layout
5. Add comprehensive test coverage
6. Performance optimization

## Documentation

- [Feature Specification](../specs/001-underwriter-and-workflow/spec.md)
- [Implementation Plan](../specs/001-underwriter-and-workflow/plan.md)
- [Data Model](../specs/001-underwriter-and-workflow/data-model.md)
- [API Contracts](../specs/001-underwriter-and-workflow/contracts/)
- [Tasks](../specs/001-underwriter-and-workflow/tasks.md)

## License

Internal HSBC project - All rights reserved
