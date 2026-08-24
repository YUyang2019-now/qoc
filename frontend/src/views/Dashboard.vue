<template>
  <div v-loading="loading" element-loading-text="加载中..." :aria-busy="loading">
    <div class="page-head">
      <div>
        <div class="page-title">仪表盘</div>
        <div class="page-desc">
          {{ summary.latest_date ? `最新数据日期：${summary.latest_date}` : '还没有导入数据' }}
        </div>
      </div>
      <el-button type="primary" @click="$router.push('/import')">
        <el-icon class="btn-icon"><UploadFilled /></el-icon>
        导入数据
      </el-button>
    </div>

    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-head">
          <span class="stat-label">主仓库存</span>
          <el-icon class="stat-icon"><Box /></el-icon>
        </div>
        <div class="stat-value">{{ formatNum(summary.total_inventory) }}</div>
        <div class="stat-sub">实际可用数合计</div>
      </div>
      <div class="stat-box">
        <div class="stat-head">
          <span class="stat-label">在途</span>
          <el-icon class="stat-icon"><Box /></el-icon>
        </div>
        <div class="stat-value">{{ formatNum(summary.total_in_transit) }}</div>
        <div class="stat-sub">各渠道在途合计</div>
      </div>
      <div class="stat-box">
        <div class="stat-head">
          <span class="stat-label">昨日销量</span>
          <el-icon class="stat-icon"><TrendCharts /></el-icon>
        </div>
        <div class="stat-value">{{ formatNum(summary.total_yesterday) }}</div>
        <div class="stat-sub">各渠道合计</div>
      </div>
      <div class="stat-box">
        <div class="stat-head">
          <span class="stat-label">低库存预警</span>
          <el-icon class="stat-icon"><Warning /></el-icon>
        </div>
        <div class="stat-value warning-value">{{ summary.low_stock_count }}</div>
        <div class="stat-sub">低于预警阈值的 SKU 数</div>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :xs="24" :lg="14">
        <div class="panel">
          <div class="panel-title">渠道汇总（{{ summary.latest_date || '-' }}）</div>
          <el-table :data="summary.channel_summary" size="small" max-height="420">
            <el-table-column prop="brand" label="品牌" width="110" />
            <el-table-column prop="sheet_name" label="渠道" min-width="150" />
            <el-table-column prop="sku_count" label="SKU 数" width="90" align="right" />
            <el-table-column label="库存" width="120" align="right">
              <template #default="{ row }">{{ formatNum(row.inventory) }}</template>
            </el-table-column>
            <el-table-column label="昨日" width="100" align="right">
              <template #default="{ row }">{{ formatNum(row.yesterday_sales) }}</template>
            </el-table-column>
            <el-table-column label="7 天" width="100" align="right">
              <template #default="{ row }">{{ formatNum(row.seven_sales) }}</template>
            </el-table-column>
            <el-table-column label="30 天" width="100" align="right">
              <template #default="{ row }">{{ formatNum(row.thirty_sales) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="panel">
          <div class="panel-title">低库存预警</div>
          <el-empty v-if="!summary.low_stock?.length" description="暂无低库存预警" :image-size="70" />
          <el-table v-else :data="summary.low_stock" size="small" max-height="420">
            <el-table-column prop="sku" label="商品编码" min-width="150" />
            <el-table-column prop="brand" label="品牌" width="90" />
            <el-table-column label="库存" width="90" align="right">
              <template #default="{ row }">
                <span class="warn-text">{{ row.inventory }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="sheet_name" label="来源" width="130" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Box, TrendCharts, UploadFilled, Warning } from '@element-plus/icons-vue'
import api from '../api'

const loading = ref(false)
const summary = reactive({
  latest_date: null,
  total_inventory: 0,
  total_in_transit: 0,
  total_yesterday: 0,
  total_seven: 0,
  total_thirty: 0,
  low_stock_count: 0,
  low_stock: [],
  channel_summary: []
})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/api/dashboard/summary')
    Object.assign(summary, data)
  } finally {
    loading.value = false
  }
}

function formatNum(value) {
  const num = Number(value || 0)
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 1 })
}

onMounted(load)
</script>

<style scoped>
.btn-icon {
  margin-right: 4px;
}

.warning-value {
  color: var(--qoc-warning);
}

.warn-text {
  color: var(--qoc-warning);
  font-weight: 600;
}
</style>
