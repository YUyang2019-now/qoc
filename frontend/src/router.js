import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: '仪表盘' } },
    { path: '/products', component: () => import('./views/Products.vue'), meta: { title: '商品档案' } },
    { path: '/inventory', component: () => import('./views/Inventory.vue'), meta: { title: '库存' } },
    { path: '/sales', component: () => import('./views/Sales.vue'), meta: { title: '销量' } },
    { path: '/styles', component: () => import('./views/Styles.vue'), meta: { title: '款详情' } },
    { path: '/import', component: () => import('./views/ImportView.vue'), meta: { title: '数据导入' } },
    { path: '/export', component: () => import('./views/ExportView.vue'), meta: { title: '数据导出' } },
    { path: '/settings', component: () => import('./views/Settings.vue'), meta: { title: '设置' } }
  ]
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · QOC 商品管理` : 'QOC 商品管理'
})

export default router
