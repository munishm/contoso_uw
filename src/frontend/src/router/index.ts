import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue')
  },
  {
    path: '/onboarding',
    name: 'DocumentTypeOnboarding',
    component: () => import('@/views/DocumentTypeOnboardingView.vue')
  },
  {
    path: '/cases/:caseId',
    name: 'CaseDetail',
    component: () => import('@/views/CaseDetailView.vue'),
    props: true
  },
  {
    path: '/cases/:caseId/upload',
    name: 'DocumentUpload',
    component: () => import('@/views/DocumentUploadView.vue'),
    props: true
  },
  {
    path: '/cases/:caseId/documents/:documentId',
    name: 'DocumentDetail',
    component: () => import('@/views/DocumentResultsView.vue'),
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
