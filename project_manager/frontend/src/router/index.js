import { createRouter, createWebHistory } from 'vue-router'

import Layout from '../components/Layout.vue'
import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import MyTasks from '../views/MyTasks.vue'
import Projects from '../views/Projects.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Stats from '../views/Stats.vue'
import Report from '../views/Report.vue'
import Users from '../views/Users.vue'
import ArchivedProjects from '../views/ArchivedProjects.vue'

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', name: 'home', component: Home, meta: { title: '工作台' } },
      { path: 'tasks', name: 'tasks', component: MyTasks, meta: { title: '我的任务' } },
      { path: 'projects', name: 'projects', component: Projects, meta: { title: '项目' } },
      { path: 'projects/:id', name: 'project-detail', component: ProjectDetail, props: true, meta: { title: '项目详情' } },
      { path: 'stats/:id', name: 'stats', component: Stats, props: true, meta: { title: '任务统计' } },
      { path: 'report', name: 'report', component: Report, meta: { title: '日报导出' } },
      { path: 'archived', name: 'archived-projects', component: ArchivedProjects, meta: { title: '归档项目', manager: true } },
      { path: 'users', name: 'users', component: Users, meta: { title: '用户管理', admin: true } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录不允许访问任何页面
router.beforeEach((to) => {
  const token = localStorage.getItem('token')

  if (to.meta.public) {
    return token ? '/' : true
  }
  if (!token) {
    return { path: '/login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }

  const role = localStorage.getItem('role')
  if (to.meta.admin && role !== 'admin') {
    return '/'
  }
  if (to.meta.manager && role !== 'admin' && role !== 'pm') {
    return '/'
  }
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title
    ? `${to.meta.title} - 运维项目管理工作平台`
    : '运维项目管理工作平台'
})

export default router