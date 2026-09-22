import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true, hideLayout: true } },
  { path: '/', name: 'home', component: () => import('../views/Home.vue') },
  { path: '/tasks', name: 'tasks', component: () => import('../views/Tasks.vue') },
  { path: '/projects', name: 'projects', component: () => import('../views/Projects.vue') },
  { path: '/projects/:id', name: 'projectDetail', component: () => import('../views/ProjectDetail.vue') },
  { path: '/stats', name: 'stats', component: () => import('../views/Stats.vue'), meta: { requirePM: true } },
  { path: '/archived', name: 'archived', component: () => import('../views/Archived.vue'), meta: { requirePM: true } },
  { path: '/report', name: 'report', component: () => import('../views/Report.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.public) return true
  if (!userStore.token) return { path: '/login', query: { redirect: to.fullPath } }
  // 仅项目经理/管理员可访问任务统计
  if (to.meta.requirePM && !userStore.isPM) {
    return { path: '/' }
  }
  return true
})

export default router