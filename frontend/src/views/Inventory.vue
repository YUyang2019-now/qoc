<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">库存</div>
        <div class="page-desc">{{ latestDate ? `最新库存日期：${latestDate}` : '暂无数据' }}</div>
      </div>
      <el-button :icon="Download" @click="$router.push('/export?kind=inventory')">导出</el-button>
    </div>

    <div class="panel">
      <div class="filter-row">
        <el-select v-model="filters.brand" placeholder="品牌" clearable aria-label="品牌筛选" style="width: 140px" @change="load(1)">
          <el-option v-for="brand in brands" :key="brand" :label="brand" :value="brand" />
        </el-select>
        <el-select v-model="filters.sheet" placeholder="渠道" clearable filterable aria-label="渠道筛选" style="width: 180px" @change="load(1)">
          <el-option v-for="name in sheets" :key="name" :label="name" :value="name" />
        </el-select>
        <el-input
          v-model="filters.sku"
          placeholder="商品编码"
          clearable
          aria-label="搜索商品编码"
          style="width: 220px"
          @keyup.enter="load(1)"
          @clear="load(1)"
        />
        <el-button type="primary" @click="load(1)">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" size="small" empty-text="没有符合条件的库存记录">
        <el-table-column prop="sku" label="商品编码" min-width="170" />
        <el-table-column prop="name" label="商品名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="sheet_name" label="渠道" min-width="150" />
        <el-table-column label="库存" width="120" align="right">
          <template #default="{ row }">
            <span :class="{ 'warn-text': Number(row.inventory) <= threshold }">{{ row.inventory }}</span>
          </template>
        </el-table-column>
        <el-table-column label="在途" width="100" align="right">
          <template #default="{ row }">{{ row.in_transit ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="showTrend(row)">趋势</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="load"
        />
      </div>
    </div>

    <el-drawer v-model="drawerVisible" title="库存趋势" size="480px">
      <div v-if="current">
        <div class="drawer-meta">商品编码：{{ current.sku }}</div>
        <div class="drawer-meta">渠道：{{ current.sheet_name }}</div>
        <TrendChart :points="trendPoints" series-key="inventory" label="库存" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import api from '../api'
import TrendChart from '../components/TrendChart.vue'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const latestDate = ref('')
const threshold = ref(10)
const filters = reactive({ brand: '', sheet: '', sku: '' })
const brands = ref([])
const sheets = ref([])
const drawerVisible = ref(false)
const current = ref(null)
const trendPoints = ref([])

async function loadMeta() {
  const [{ data: meta }, { data: settings }, { data: brandData }] = await Promise.all([
    api.get('/api/meta/sheets'),
    api.get('/api/settings'),
    api.get('/api/meta/brands')
  ])
  sheets.value = meta.data_sheets
  threshold.value = settings.low_stock_threshold
  brands.value = brandData.brands
}

async function load(nextPage) {
  if (nextPage) page.value = nextPage
  loading.value = true
  try {
    const { data } = await api.get('/api/inventory', {
      params: { ...filters, page: page.value, page_size: pageSize }
    })
    items.value = data.items
    total.value = data.total
    latestDate.value = data.latest_date
  } finally {
    loading.value = false
  }
}

async function showTrend(row) {
  current.value = row
  drawerVisible.value = true
  const { data } = await api.get('/api/inventory/trend', {
    params: { sku: row.sku, sheet: row.sheet_name }
  })
  trendPoints.value = data.points
}

onMounted(() => {
  loadMeta()
  load()
})
</script>

<style scoped>
.drawer-meta {
  color: #6b7682;
  font-size: 13px;
  margin-bottom: 6px;
}

.warn-text {
  color: var(--qoc-warning);
  font-weight: 600;
}
</style>
