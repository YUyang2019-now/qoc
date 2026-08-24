<template>
  <Login v-if="!user" @logged-in="loadMe" />
  <el-container v-else class="app-shell">
    <el-aside width="220px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">Q</div>
        <div>
          <div class="brand-name">QOC 商品管理</div>
          <div class="brand-sub">库存 · 销量 · 导入</div>
        </div>
      </div>
      <el-menu :default-active="activePath" router class="side-menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <span>商品档案</span>
        </el-menu-item>
        <el-menu-item index="/inventory">
          <el-icon><Box /></el-icon>
          <span>库存</span>
        </el-menu-item>
        <el-menu-item index="/sales">
          <el-icon><TrendCharts /></el-icon>
          <span>销量</span>
        </el-menu-item>
        <el-menu-item index="/import">
          <el-icon><UploadFilled /></el-icon>
          <span>数据导入</span>
        </el-menu-item>
        <el-menu-item index="/export">
          <el-icon><Download /></el-icon>
          <span>数据导出</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-line">
          <el-icon><User /></el-icon>
          <span>{{ user }}</span>
        </div>
        <el-button size="small" text type="danger" @click="logout">退出登录</el-button>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Box,
  DataBoard,
  Download,
  Goods,
  Setting,
  TrendCharts,
  UploadFilled,
  User
} from '@element-plus/icons-vue'
import api from './api'
import Login from './views/Login.vue'

const user = ref(null)
const route = useRoute()
const router = useRouter()
const activePath = computed(() => route.path)

async function loadMe() {
  try {
    const { data } = await api.get('/api/auth/me')
    user.value = data.username
  } catch (error) {
    user.value = null
  }
}

async function logout() {
  await api.post('/api/auth/logout')
  user.value = null
  router.push('/dashboard')
}

onMounted(loadMe)
</script>
