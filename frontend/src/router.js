import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Products from './views/Products.vue'
import Inventory from './views/Inventory.vue'
import Sales from './views/Sales.vue'
import ImportView from './views/ImportView.vue'
import ExportView from './views/ExportView.vue'
import Settings from './views/Settings.vue'
import Styles from './views/Styles.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard, meta: { title: '仪表盘' } },
    { path: '/products', component: Products, meta: { title: '商品档案' } },
    { path: '/inventory', component: Inventory, meta: { title: '库存' } },
    { path: '/sales', component: Sales, meta: { title: '销量' } },
    { path: '/styles', component: Styles, meta: { title: '款详情' } },
    { path: '/import', component: ImportView, meta: { title: '数据导入' } },
    { path: '/export', component: ExportView, meta: { title: '数据导出' } },
    { path: '/settings', component: Settings, meta: { title: '设置' } }
  ]
})

export default router
