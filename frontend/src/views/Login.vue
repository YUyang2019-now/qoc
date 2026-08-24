<template>
  <div class="login-wrap">
    <div class="login-panel">
      <div class="login-brand">
        <div class="brand-mark">Q</div>
        <div>
          <div class="login-title">QOC 商品管理</div>
          <div class="login-sub">库存 · 销量 · 数据导入</div>
        </div>
      </div>
      <el-form @submit.prevent="submit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="账号" size="large" aria-label="账号">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            aria-label="密码"
            @keyup.enter="submit"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-button"
          :loading="loading"
          @click="submit"
        >
          登录
        </el-button>
      </el-form>
      <el-alert v-if="error" :title="error" type="error" :closable="false" class="login-error" />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const emit = defineEmits(['logged-in'])
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
  if (!form.username || !form.password) {
    error.value = '请输入账号和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/api/auth/login', form)
    ElMessage.success('登录成功')
    emit('logged-in', data.username)
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-button {
  width: 100%;
}

.login-error {
  margin-top: 16px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.login-title {
  margin-bottom: 2px;
}

.login-sub {
  margin-bottom: 0;
}
</style>
