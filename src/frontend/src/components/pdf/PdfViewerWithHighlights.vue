<template>
  <div 
    class="pdf-viewer-container" 
    ref="containerRef"
    @scroll="handleScroll"
  >
    <div v-if="isLoading" class="pdf-loading">
      <v-progress-circular indeterminate color="primary" />
      <span class="ml-3">Loading PDF...</span>
    </div>
    
    <div v-else-if="error" class="pdf-error">
      <v-icon size="48" color="warning">mdi-file-alert-outline</v-icon>
      <p class="text-body-1 mt-3">{{ error }}</p>
      <p class="text-body-2 text-grey mt-1">
        This may be due to browser security restrictions (CORS).
      </p>
      <div class="d-flex gap-2 mt-3">
        <v-btn variant="tonal" color="primary" @click="loadPdf">
          <v-icon start>mdi-refresh</v-icon>
          Retry
        </v-btn>
        <v-btn variant="outlined" color="secondary" @click="$emit('fallback-to-annotated')">
          <v-icon start>mdi-pencil-box-outline</v-icon>
          Use Annotated View
        </v-btn>
      </div>
    </div>
    
    <div v-else class="pdf-pages" ref="pagesContainerRef">
      <div 
        v-for="pageNum in numPages" 
        :key="pageNum"
        class="pdf-page-wrapper"
        :data-page="pageNum"
      >
        <canvas 
          :ref="(el) => setCanvasRef(pageNum, el as HTMLCanvasElement)"
          class="pdf-canvas"
        />
        <!-- SVG overlay for interactive highlights -->
        <svg 
          class="highlight-overlay"
          :viewBox="`0 0 ${pageWidths[pageNum] || 612} ${pageHeights[pageNum] || 792}`"
          preserveAspectRatio="none"
        >
          <defs>
            <!-- Strong glow filter for hover effect -->
            <filter id="glowHover" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="8" result="blur1"/>
              <feFlood flood-color="currentColor" flood-opacity="0.8" result="color"/>
              <feComposite in="color" in2="blur1" operator="in" result="shadow"/>
              <feMerge>
                <feMergeNode in="shadow"/>
                <feMergeNode in="shadow"/>
                <feMergeNode in="shadow"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <!-- Pulsing animation filter -->
            <filter id="glowPulse" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="10" result="blur"/>
              <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          <!-- Annotation rectangles -->
          <g v-for="(annotation, idx) in getAnnotationsForPage(pageNum)" :key="`${pageNum}-${idx}`">
            <!-- Glow background layer (only visible when hovered) -->
            <rect
              v-if="hoveredField === annotation.fieldName"
              :x="annotation.x - 4"
              :y="annotation.y - 4"
              :width="annotation.width + 8"
              :height="annotation.height + 8"
              :fill="annotation.color"
              fill-opacity="0.3"
              :stroke="annotation.color"
              stroke-width="4"
              stroke-opacity="0.6"
              rx="4"
              class="glow-background"
            />
            <!-- Main annotation rectangle -->
            <rect
              :x="annotation.x"
              :y="annotation.y"
              :width="annotation.width"
              :height="annotation.height"
              :fill="hoveredField === annotation.fieldName ? `${annotation.color}40` : `${annotation.color}15`"
              :stroke="annotation.color"
              :stroke-width="hoveredField === annotation.fieldName ? 4 : 2"
              class="annotation-rect"
              :class="{ 
                'hovered': hoveredField === annotation.fieldName,
                'highlighted': highlightedField === annotation.fieldName
              }"
              @mouseenter="$emit('hover-field', annotation.fieldName)"
              @mouseleave="$emit('hover-field', null)"
              @click="$emit('click-field', annotation.fieldName)"
            />
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { ExtractedFieldResult, FieldColorInfo } from '@/types/document'

// Set worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

interface Props {
  pdfUrl: string | null
  fields: ExtractedFieldResult[]
  fieldColors: Record<string, FieldColorInfo>
  highlightedField: string | null
  hoveredField: string | null
  scale?: number
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1.5
})

const emit = defineEmits<{
  (e: 'hover-field', fieldName: string | null): void
  (e: 'click-field', fieldName: string): void
  (e: 'loaded'): void
  (e: 'error', error: string): void
  (e: 'fallback-to-annotated'): void
}>()

// State
const isLoading = ref(false)
const error = ref<string | null>(null)
const numPages = ref(0)
const pdfDoc = ref<any>(null)
const containerRef = ref<HTMLElement | null>(null)
const pagesContainerRef = ref<HTMLElement | null>(null)
const canvasRefs = ref<Map<number, HTMLCanvasElement>>(new Map())
const pageWidths = ref<Record<number, number>>({})
const pageHeights = ref<Record<number, number>>({})
const renderedPages = ref<Set<number>>(new Set())

// Computed: Convert fields to annotations with pixel coordinates
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
      
      const pageWidth = pageWidths.value[citation.page] || 612
      const pageHeight = pageHeights.value[citation.page] || 792
      
      // Convert normalized coordinates (0-1) to page coordinates
      const bbox = citation.bbox
      result.push({
        fieldName: field.field_name,
        page: citation.page,
        x: bbox.x * pageWidth,
        y: bbox.y * pageHeight,
        width: bbox.width * pageWidth,
        height: bbox.height * pageHeight,
        color: props.fieldColors[field.field_name]?.hex || '#1976d2'
      })
    }
  }
  
  return result
})

function getAnnotationsForPage(pageNum: number): Annotation[] {
  return annotations.value.filter(a => a.page === pageNum)
}

function setCanvasRef(pageNum: number, el: HTMLCanvasElement | null) {
  if (el) {
    canvasRefs.value.set(pageNum, el)
  } else {
    canvasRefs.value.delete(pageNum)
  }
}

async function loadPdf() {
  if (!props.pdfUrl) return
  
  try {
    isLoading.value = true
    error.value = null
    renderedPages.value.clear()
    
    // Load the PDF document
    const loadingTask = pdfjsLib.getDocument(props.pdfUrl)
    pdfDoc.value = await loadingTask.promise
    numPages.value = pdfDoc.value.numPages
    
    // Get page dimensions for all pages
    for (let i = 1; i <= numPages.value; i++) {
      const page = await pdfDoc.value.getPage(i)
      const viewport = page.getViewport({ scale: props.scale })
      pageWidths.value[i] = viewport.width
      pageHeights.value[i] = viewport.height
    }
    
    // Wait for DOM to update with pages
    await nextTick()
    
    // Render visible pages
    renderVisiblePages()
    
    emit('loaded')
  } catch (err) {
    console.error('Failed to load PDF:', err)
    error.value = 'Failed to load PDF document'
    emit('error', error.value)
  } finally {
    isLoading.value = false
  }
}

async function renderPage(pageNum: number) {
  if (renderedPages.value.has(pageNum)) return
  if (!pdfDoc.value) return
  
  const canvas = canvasRefs.value.get(pageNum)
  if (!canvas) return
  
  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const viewport = page.getViewport({ scale: props.scale })
    
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    const context = canvas.getContext('2d')
    if (!context) return
    
    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise
    
    renderedPages.value.add(pageNum)
  } catch (err) {
    console.error(`Failed to render page ${pageNum}:`, err)
  }
}

function renderVisiblePages() {
  if (!containerRef.value || !pagesContainerRef.value) return
  
  const container = containerRef.value
  const containerRect = container.getBoundingClientRect()
  
  // Find visible pages and render them
  const pageElements = pagesContainerRef.value.querySelectorAll('.pdf-page-wrapper')
  pageElements.forEach((el) => {
    const rect = el.getBoundingClientRect()
    const pageNum = parseInt(el.getAttribute('data-page') || '0')
    
    // Check if page is visible (with some buffer)
    if (rect.bottom > containerRect.top - 200 && rect.top < containerRect.bottom + 200) {
      renderPage(pageNum)
    }
  })
}

let scrollTimeout: number | null = null
function handleScroll() {
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
  scrollTimeout = window.setTimeout(() => {
    renderVisiblePages()
  }, 100)
}

// Scroll to highlighted field
function scrollToField(fieldName: string) {
  const annotation = annotations.value.find(a => a.fieldName === fieldName)
  if (!annotation || !containerRef.value || !pagesContainerRef.value) return
  
  const pageEl = pagesContainerRef.value.querySelector(`[data-page="${annotation.page}"]`)
  if (!pageEl) return
  
  pageEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

// Watch for URL changes
watch(() => props.pdfUrl, () => {
  loadPdf()
})

// Watch for highlighted field changes to scroll
watch(() => props.highlightedField, (fieldName) => {
  if (fieldName) {
    scrollToField(fieldName)
  }
})

onMounted(() => {
  if (props.pdfUrl) {
    loadPdf()
  }
})

onUnmounted(() => {
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
})

// Expose methods for parent
defineExpose({
  scrollToField,
  refresh: loadPdf
})
</script>

<style scoped>
.pdf-viewer-container {
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 600px;
  overflow: auto;
  background: #525659;
  position: relative;
}

.pdf-loading,
.pdf-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f5f5f5;
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
}

.pdf-canvas {
  display: block;
}

.highlight-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.glow-background {
  animation: glowPulse 1.5s ease-in-out infinite;
}

.annotation-rect {
  pointer-events: all;
  cursor: pointer;
  transition: all 0.15s ease;
}

.annotation-rect.hovered {
  animation: rectPulse 1s ease-in-out infinite;
}

.annotation-rect.highlighted {
  stroke-width: 4;
  stroke-dasharray: none;
}

@keyframes glowPulse {
  0% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
  100% {
    opacity: 0.4;
    transform: scale(1);
  }
}

@keyframes rectPulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    opacity: 1;
  }
}
</style>
