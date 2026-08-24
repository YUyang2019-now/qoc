<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">数据导入</div>
        <div class="page-desc">上传运营更新的 Excel，预览后确认入库</div>
      </div>
    </div>

    <div class="panel">
      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xlsm,.xls"
        :on-change="onFileChange"
        :on-remove="() => (selectedFile = null)"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖入运营文件，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 xlsx / xlsm / xls，大文件请耐心等待解析</div>
        </template>
      </el-upload>

      <div class="filter-row upload-actions">
        <el-checkbox v-model="includeMaster">首次迁移（同时导入商品档案）</el-checkbox>
        <el-date-picker
          v-model="importDate"
          type="date"
          placeholder="快照日期（留空自动识别）"
          value-format="YYYY-MM-DD"
          style="width: 240px"
        />
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="upload">
          上传并预览
        </el-button>
      </div>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        :closable="false"
        class="import-alert"
      />

      <template v-if="preview">
        <el-divider />
        <div class="preview-head">
          <div>
            <strong>{{ preview.filename }}</strong>
            <span class="preview-meta">日期 {{ preview.date }} · 共 {{ preview.total_rows }} 行</span>
          </div>
          <div>
            <el-button @click="discard">放弃</el-button>
            <el-button type="primary" :loading="confirming" @click="confirm">确认导入</el-button>
          </div>
        </div>
        <el-table :data="preview.sheets" size="small">
          <el-table-column prop="sheet_name" label="Sheet" min-width="180" />
          <el-table-column prop="kind" label="类型" width="100" />
          <el-table-column prop="row_count" label="行数" width="120" align="right" />
        </el-table>
      </template>
    </div>

    <div class="panel">
      <div class="panel-title">导入记录</div>
      <el-table v-loading="historyLoading" :data="history" size="small">
        <el-table-column prop="filename" label="文件" min-width="220" show-overflow-tooltip />
        <el-table-column prop="import_date" label="日期" width="110" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'done' ? 'success' : 'info'" size="small">
              {{ row.status === 'done' ? '已导入' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="导入时间" min-width="160">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!history.length" description="暂无导入记录" :image-size="70" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const selectedFile = ref(null)
const includeMaster = ref(false)
const importDate = ref('')
const uploading = ref(false)
const confirming = ref(false)
const preview = ref(null)
const error = ref('')
const history = ref([])
const historyLoading = ref(false)

function onFileChange(file) {
  selectedFile.value = file.raw
  preview.value = null
  error.value = ''
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const { data } = await api.post('/api/imports/upload', form, {
      params: { include_master: includeMaster.value, date: importDate.value || undefined }
    })
    preview.value = data
    ElMessage.success('解析完成，请确认导入')
    loadHistory()
  } catch (err) {
    error.value = err.response?.data?.detail || '上传失败'
  } finally {
    uploading.value = false
  }
}

async function confirm() {
  confirming.value = true
  try {
    await api.post(`/api/imports/${preview.value.token}/confirm`)
    ElMessage.success('导入成功')
    preview.value = null
    selectedFile.value = null
    loadHistory()
  } finally {
    confirming.value = false
  }
}

async function discard() {
  await ElMessageBox.confirm('放弃本次导入？', '提示', { type: 'warning' })
  await api.delete(`/api/imports/${preview.value.token}`)
  preview.value = null
  selectedFile.value = null
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const { data } = await api.get('/api/imports')
    history.value = data.items.filter((item) => item.status === 'done' || item.status === 'preview')
  } finally {
    historyLoading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.upload-actions {
  margin-top: 14px;
}

.import-alert {
  margin-top: 12px;
}

.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.preview-meta {
  color: #8a95a1;
  font-size: 13px;
  margin-left: 10px;
}
</style>
