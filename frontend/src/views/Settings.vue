<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">设置</div>
        <div class="page-desc">预警阈值和登录密码</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">低库存预警</div>
      <div class="setting-row">
        <span>库存低于该数值时提醒（按 SKU）</span>
        <el-input-number v-model="threshold" :min="0" :step="1" />
        <el-button type="primary" :loading="saving" @click="saveThreshold">保存</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">快照保留</div>
      <div class="setting-row">
        <span>保留最近多少天的快照</span>
        <el-input-number v-model="retentionDays" :min="1" :max="3650" :step="30" />
        <el-button type="primary" :loading="savingRetention" @click="saveRetention">保存</el-button>
        <el-button type="danger" plain :loading="cleaning" @click="cleanNow">立即清理</el-button>
      </div>
      <div class="cleanup-hint">系统每天会自动清理更早的数据</div>
    </div>

    <div class="panel">
      <div class="panel-title">修改密码</div>
      <el-form :model="passwordForm" label-width="90px" style="max-width: 420px">
        <el-form-item label="原密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="changing" @click="changePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const threshold = ref(10)
const retentionDays = ref(60)
const saving = ref(false)
const savingRetention = ref(false)
const cleaning = ref(false)
const changing = ref(false)
const passwordForm = reactive({ old_password: '', new_password: '' })

async function load() {
  const { data } = await api.get('/api/settings')
  threshold.value = data.low_stock_threshold
  retentionDays.value = data.snapshot_retention_days
}

async function saveThreshold() {
  saving.value = true
  try {
    await api.put('/api/settings', { low_stock_threshold: threshold.value })
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function saveRetention() {
  savingRetention.value = true
  try {
    await api.put('/api/settings', { snapshot_retention_days: retentionDays.value })
    ElMessage.success('已保存')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    savingRetention.value = false
  }
}

async function cleanNow() {
  await ElMessageBox.confirm(
    `将删除保留期以外的快照，删除后无法恢复。确定立即清理？`,
    '清理旧数据',
    { type: 'warning', confirmButtonText: '清理', cancelButtonText: '取消' }
  )
  cleaning.value = true
  try {
    const { data } = await api.post('/api/settings/cleanup-snapshots')
    ElMessage.success(`已清理 ${data.deleted} 条旧快照`)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '清理失败')
  } finally {
    cleaning.value = false
  }
}

async function changePassword() {
  if (!passwordForm.old_password || !passwordForm.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  changing.value = true
  try {
    await api.post('/api/auth/change-password', passwordForm)
    ElMessage.success('密码已修改')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally {
    changing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.setting-row {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #4a5560;
}

.cleanup-hint {
  color: #8a95a1;
  font-size: 12px;
  margin-top: 10px;
}
</style>
