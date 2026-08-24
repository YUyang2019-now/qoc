<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">数据导入</div>
        <div class="page-desc">上传运营更新的 Excel，预览后确认入库</div>
      </div>
    </div>

    <div
      class="panel"
      :aria-busy="uploading"
    >
      <el-upload
        ref="uploadRef"
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
        <span class="control-label">快照日期</span>
        <el-date-picker
          v-model="importDate"
          type="date"
          placeholder="快照日期（留空自动识别）"
          value-format="YYYY-MM-DD"
          style="width: 240px"
        />
      </div>

      <div v-if="uploading" class="parse-overlay">
        <div class="parse-box" role="status" aria-live="polite">
          <div class="parse-stage">{{ parseStage }}</div>
          <el-progress
            :percentage="parseProgress"
            :status="parseProgress >= 100 ? 'success' : undefined"
            :stroke-width="14"
          />
          <div class="parse-tip">正在后台解析，请勿关闭页面或刷新</div>
        </div>
      </div>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        :closable="false"
        role="alert"
        class="import-alert"
      />

      <template v-if="preview && preview.format !== 'channel'">
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

    <el-dialog v-model="channelDialogVisible" title="确认渠道数据" width="760px">
      <div class="dialog-summary">
        <div class="dialog-field">
          <span class="dialog-label">渠道</span>
          <el-select v-model="channelForm.channel" filterable style="width: 240px">
            <el-option v-for="name in sheets" :key="name" :label="name" :value="name" />
          </el-select>
        </div>
        <div class="dialog-field">
          <span class="dialog-label">数据日期</span>
          <el-date-picker
            v-model="channelForm.date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 180px"
          />
        </div>
      </div>

      <el-descriptions :column="3" border size="small" class="dialog-stats">
        <el-descriptions-item label="SKU 数">{{ channelStats.total }}</el-descriptions-item>
        <el-descriptions-item label="有库存">{{ channelStats.with_inventory }}</el-descriptions-item>
        <el-descriptions-item label="有在途">{{ channelStats.with_in_transit }}</el-descriptions-item>
        <el-descriptions-item label="有销量">{{ channelStats.with_sales }}</el-descriptions-item>
        <el-descriptions-item label="匹配不到商品档案" :span="2">{{ channelStats.unmatched }}</el-descriptions-item>
      </el-descriptions>

      <div class="sample-title">数据样例（前 5 条）</div>
      <el-table :data="channelSamples" size="small" max-height="260">
        <el-table-column prop="sku" label="条码" min-width="160" />
        <el-table-column label="库存" width="90" align="right">
          <template #default="{ row }">{{ row.inventory ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="在途" width="90" align="right">
          <template #default="{ row }">{{ row.in_transit ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="昨日" width="80" align="right">
          <template #default="{ row }">{{ row.yesterday_sales ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="7 天" width="80" align="right">
          <template #default="{ row }">{{ row.seven_sales ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="30 天" width="80" align="right">
          <template #default="{ row }">{{ row.thirty_sales ?? '-' }}</template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="discardChannel">取消</el-button>
        <el-button type="primary" :loading="confirming" @click="confirmChannel">确认导入</el-button>
      </template>
    </el-dialog>

    <div class="panel">
      <div class="panel-title">导入记录</div>
      <el-table v-loading="historyLoading" :data="history" size="small">
        <el-table-column prop="filename" label="文件" min-width="220" show-overflow-tooltip />
        <el-table-column prop="import_date" label="日期" width="110" />
        <el-table-column prop="channel" label="渠道" width="120">
          <template #default="{ row }">{{ row.channel || '-' }}</template>
        </el-table-column>
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
import { onMounted, reactive, ref } from 'vue'
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
const uploadRef = ref(null)
const sheets = ref([])
const channelDialogVisible = ref(false)
const channelForm = reactive({ channel: '', date: '' })
const channelStats = reactive({ total: 0, with_inventory: 0, with_in_transit: 0, with_sales: 0, unmatched: 0 })
const channelSamples = ref([])
const parseProgress = ref(0)
const parseStage = ref('')

function onFileChange(file) {
  if (uploading.value) return
  selectedFile.value = file.raw
  preview.value = null
  error.value = ''
  upload()
}

function resetUpload() {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
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
    parseProgress.value = 0
    parseStage.value = '等待解析'
    pollParse(data.task_id)
  } catch (err) {
    uploading.value = false
    resetUpload()
    error.value = `${err.response?.data?.detail || '上传失败'}，可重新上传文件`
  }
}

async function pollParse(taskId) {
  try {
    const { data } = await api.get(`/api/imports/parse-progress/${taskId}`)
    parseProgress.value = data.progress || 0
    parseStage.value = data.stage || ''
    if (data.status === 'done') {
      uploading.value = false
      preview.value = data.result
      if (data.result.format === 'channel') {
        channelForm.channel = data.result.channel
        channelForm.date = data.result.date
        channelStats.total = data.result.total_rows
        channelStats.with_inventory = data.result.stats?.with_inventory || 0
        channelStats.with_in_transit = data.result.stats?.with_in_transit || 0
        channelStats.with_sales = data.result.stats?.with_sales || 0
        channelStats.unmatched = data.result.stats?.unmatched || 0
        channelSamples.value = data.result.samples || []
        channelDialogVisible.value = true
      } else {
        ElMessage.success('解析完成，请确认导入')
      }
      loadHistory()
      return
    }
    if (data.status === 'error') {
      uploading.value = false
      resetUpload()
      error.value = `${data.error || '解析失败'}，可重新上传文件`
      return
    }
    setTimeout(() => pollParse(taskId), 1000)
  } catch (err) {
    uploading.value = false
    resetUpload()
    error.value = `${err.response?.data?.detail || '解析状态获取失败'}，可重新上传文件`
  }
}

async function confirmChannel() {
  confirming.value = true
  try {
    await api.post(`/api/imports/${preview.value.token}/confirm`, null, {
      params: { channel: channelForm.channel, date: channelForm.date }
    })
    ElMessage.success('导入成功')
    channelDialogVisible.value = false
    resetUpload()
    loadHistory()
  } finally {
    confirming.value = false
  }
}

async function discardChannel() {
  if (!preview.value) {
    channelDialogVisible.value = false
    return
  }
  await ElMessageBox.confirm('放弃本次导入？', '提示', { type: 'warning' })
  await api.delete(`/api/imports/${preview.value.token}`)
  channelDialogVisible.value = false
  resetUpload()
}

async function confirm() {
  confirming.value = true
  try {
    await api.post(`/api/imports/${preview.value.token}/confirm`)
    ElMessage.success('导入成功')
    resetUpload()
    loadHistory()
  } finally {
    confirming.value = false
  }
}

async function discard() {
  await ElMessageBox.confirm('放弃本次导入？', '提示', { type: 'warning' })
  await api.delete(`/api/imports/${preview.value.token}`)
  resetUpload()
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

async function loadSheets() {
  const { data } = await api.get('/api/meta/sheets')
  sheets.value = data.data_sheets
}

onMounted(() => {
  loadHistory()
  loadSheets()
})
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

.dialog-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 14px;
}

.dialog-field {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-label {
  color: #4b5563;
  font-size: 14px;
}

.control-label {
  color: var(--qoc-muted);
  font-size: 13px;
}

.dialog-stats {
  margin-bottom: 14px;
}

.sample-title {
  color: #4b5563;
  font-size: 14px;
  margin-bottom: 8px;
}

.panel {
  position: relative;
}

.parse-overlay {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 8px;
}

.parse-box {
  width: 420px;
  padding: 24px 28px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(31, 41, 55, 0.12);
}

.parse-stage {
  text-align: center;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 14px;
}

.parse-tip {
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
  margin-top: 8px;
}
</style>
