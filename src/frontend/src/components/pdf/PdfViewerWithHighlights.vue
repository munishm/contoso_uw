<template>
  <div class="pdf-viewer-container" ref="containerRef">
    <div v-if="isLoading && loadedPages.size === 0" class="pdf-loading">
      <v-progress-circular indeterminate color="primary" />
      <span class="ml-3">Loading pages...</span>
    </div>
    
    <div v-else-if="error" class="pdf-error">
      <v-icon size="48" color="warning">mdi-file-alert-outline</v-icon>
      <p class="text-body-1 mt-3">{{ error }}</p>
      <v-btn variant="tonal" color="primary" class="mt-3" @click="retry">
        <v-icon start>mdi-refresh</v-icon>
        Retry
      </v-btn>
    </div>
    
    <div v-else class="pdf-pages">
      <div 
        v-for="pageNum in numPages" 
        :key="pageNum"
        class="pdf-page-wrapper"
        :data-page="pageNum"
      >
        <!-- Page image from backend -->
        <img 
          :src="getPageImageUrl(pageNum)"
          class="pdf-page-image"
          :alt="`Page ${pageNum}`"
          @load="onImageLoad(pageNum, $event)"
          @error="onImageError(pageNum, $event)"
        />
        
        <!-- SVG overlay for interactive bounding boxes -->
        <svg 
          v-if="pageDimensions[pageNum]"
          class="highlight-overlay"
          :viewBox="`0 0 ${pageDimensions[pageNum].width} ${pageDimensions[pageNum].height}`"
          preserveAspectRatio="xMidYMid meet"
        >
          <!-- Annotation rectangles -->
          <g v-for="(annotation, idx) in getAnnotationsForPage(pageNum)" :key="`${pageNum}-${idx}`">
            <!-- Glow background (when selected) -->
            <rect
              v-if="selectedField === annotation.fieldName"
              :x="annotation.x - 6"
              :y="annotation.y - 6"
              :width="annotation.width + 12"
              :height="annotation.height + 12"
              :fill="annotation.color"
              fill-opacity="0.3"
              :stroke="annotation.color"
              stroke-width="4"
              stroke-opacity="0.7"
              rx="4"
              class="glow-rect"
            />
            <!-- Main bounding box -->
            <rect
              :x="annotation.x"
              :y="annotation.y"
              :width="annotation.width"
              :height="annotation.height"
              :fill="selectedField === annotation.fieldName ? `${annotation.color}30` : 'transparent'"
              :stroke="annotation.color"
              :stroke-width="selectedField === annotation.fieldName ? 3 : 2"
              :stroke-dasharray="selectedField === annotation.fieldName ? 'none' : '4,2'"
              class="annotation-rect"
              :class="{ 'selected': selectedField === annotation.fieldName }"
              @click="handleAnnotationClick(annotation.fieldName)"
            />
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { ExtractedFieldResult, FieldColorInfo } from '@/types/document'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Props {
  caseId: string
  documentId: string
  fields: ExtractedFieldResult[]
  fieldColors: Record<string, FieldColorInfo>
  selectedField: string | null  // Currently selected field (from click)
  numPages: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'select-field', fieldName: string | null): void
  (e: 'loaded'): void
  (e: 'error', error: string): void
}>()

// State
const isLoading = ref(false)  // Start as false so images render immediately
const error = ref<string | null>(null)
const containerRef = ref<HTMLElement | null>(null)
const pageDimensions = ref<Record<number, { width: number; height: number }>>({})
const loadedPages = ref<Set<number>>(new Set())

// Get page image URL (using backend's page rendering endpoint)
function getPageImageUrl(pageNum: number): string {
  return `${API_BASE_URL}/cases/${props.caseId}/documents/${props.documentId}/page/${pageNum}`
}

// Handle image load to get natural dimensions
function onImageLoad(pageNum: number, event: Event) {
  const img = event.target as HTMLImageElement
  pageDimensions.value[pageNum] = {
    width: img.naturalWidth,
    height: img.naturalHeight
  }
  loadedPages.value.add(pageNum)
  console.log(`[PdfViewer] Page ${pageNum} loaded (${loadedPages.value.size}/${props.numPages})`)
  
  // Check if all pages are loaded
  if (loadedPages.value.size >= props.numPages) {
    isLoading.value = false
    emit('loaded')
  }
}

// Handle image error
function onImageError(pageNum: number, event: Event) {
  console.error(`[PdfViewer] Failed to load page ${pageNum}`)
  error.value = `Failed to load page ${pageNum}. Check if the backend is running.`
  isLoading.value = false
  emit('error', error.value)
}

// Retry loading
function retry() {
  error.value = null
  isLoading.value = true
  loadedPages.value.clear()
  pageDimensions.value = {}
}

// Convert normalized bbox coordinates to pixel coordinates
interface Annotation {
  fieldName: string
  page: number
  x: number
  y: number
  width: number
  height: number
  color: string
}

const annotations = computed<Annotation[]>(() => {
  const result: Annotation[] = []
  
  for (const field of props.fields) {
    if (!field.citations?.length) continue
    
    for (const citation of field.citations) {
      if (!citation.bbox) continue
      
      const dims = pageDimensions.value[citation.page]
      if (!dims) continue
      
      // Convert normalized coordinates (0-1) to pixel coordinates
      const bbox = citation.bbox
      result.push({
        fieldName: field.field_name,
        page: citation.page,
        x: bbox.x * dims.width,
        y: bbox.y * dims.height,
        width: bbox.width * dims.width,
        height: bbox.height * dims.height,
        color: props.fieldColors[field.field_name]?.hex || '#1976d2'
      })
    }
  }
  
  return result
})

function getAnnotationsForPage(pageNum: number): Annotation[] {
  return annotations.value.filter(a => a.page === pageNum)
}

// Handle click on annotation in PDF
function handleAnnotationClick(fieldName: string) {
  // Toggle selection - click again to deselect
  if (props.selectedField === fieldName) {
    emit('select-field', null)
  } else {
    emit('select-field', fieldName)
  }
}

// Scroll to field and highlight it
function scrollToField(fieldName: string) {
  const annotation = annotations.value.find(a => a.fieldName === fieldName)
  if (!annotation || !containerRef.value) return
  
  const pageEl = containerRef.value.querySelector(`[data-page="${annotation.page}"]`)
  if (pageEl) {
    pageEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// Watch for selected field changes to scroll
watch(() => props.selectedField, (fieldName) => {
  if (fieldName) scrollToField(fieldName)
})

function loadPages() {
  isLoading.value = true
  error.value = null
  loadedPages.value.clear()
  pageDimensions.value = {}
}

onMounted(() => {
  // Images will load automatically via src binding
  // isLoading will be set to false when all images load
})
</script>

<style scoped>
.pdf-viewer-container {
  height: 100%;
  overflow-y: auto;
  background: #525659;
}

.pdf-loading,
.pdf-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: white;
  background: #f5f5f5;
}

.pdf-error {
  color: #333;
}

.pdf-pages {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  gap: 20px;
}

.pdf-page-wrapper {
  position: relative;
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  line-height: 0;
}

.pdf-page-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.highlight-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.annotation-rect {
  pointer-events: all;
  cursor: pointer;
  transition: all 0.2s ease;
}

.annotation-rect:hover {
  stroke-width: 3;
  stroke-dasharray: none;
}

.annotation-rect.selected {
  stroke-dasharray: none;
}

.glow-rect {
  animation: glowPulse 1.2s ease-in-out infinite;
  filter: drop-shadow(0 0 8px currentColor);
}

@keyframes glowPulse {
  0%, 100% { 
    opacity: 0.4;
    transform: scale(1);
  }
  50% { 
    opacity: 0.8;
    transform: scale(1.01);
  }
}
</style>
