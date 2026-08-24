<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">款详情</div>
        <div class="page-desc">{{ latestDate ? `最新数据日期：${latestDate}` : '暂无数据' }}</div>
      </div>
      <el-button v-if="detail" text type="primary" @click="closeDetail">收起详情</el-button>
    </div>

    <div class="panel">
      <div class="filter-row">
        <el-input
          v-model="filters.search"
          placeholder="搜索款号 / 条形码 / 名称 / 规格 / 颜色"
          clearable
          aria-label="搜索款"
          style="width: 360px"
          @keyup.enter="load(1)"
          @clear="load(1)"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select
          v-model="filters.brand"
          placeholder="品牌"
          clearable
          filterable
          aria-label="品牌筛选"
          style="width: 150px"
          @change="load(1)"
        >
          <el-option v-for="brand in brands" :key="brand" :label="brand" :value="brand" />
        </el-select>
        <el-select
          v-model="filters.supplier"
          placeholder="供应商"
          clearable
          filterable
          aria-label="供应商筛选"
          style="width: 170px"
          @change="load(1)"
        >
          <el-option v-for="supplier in suppliers" :key="supplier" :label="supplier" :value="supplier" />
        </el-select>
        <el-button type="primary" @click="load(1)">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" size="small" empty-text="没有匹配的款">
        <el-table-column prop="product_code" label="款号" min-width="140" />
        <el-table-column prop="name" label="产品名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="110" />
        <el-table-column prop="supplier" label="供应商" width="110" />
        <el-table-column prop="sku_count" label="SKU 数" width="90" align="right" />
        <el-table-column label="库存合计" width="110" align="right">
          <template #default="{ row }">{{ formatNum(row.inventory) }}</template>
        </el-table-column>
        <el-table-column label="昨日销量" width="100" align="right">
          <template #default="{ row }">{{ formatNum(row.yesterday_sales) }}</template>
        </el-table-column>
        <el-table-column label="7 天销量" width="100" align="right">
          <template #default="{ row }">{{ formatNum(row.seven_sales) }}</template>
        </el-table-column>
        <el-table-column label="30 天销量" width="100" align="right">
          <template #default="{ row }">{{ formatNum(row.thirty_sales) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openStyle(row)">查看</el-button>
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

    <div v-if="detail" v-loading="detailLoading" id="style-detail" class="detail-wrap">
      <div class="detail-stats">
        <div class="mini-stat">
          <span>SKU 数</span>
          <strong>{{ detail.sku_count }}</strong>
        </div>
        <div class="mini-stat">
          <span>库存合计</span>
          <strong>{{ formatNum(detail.totals.inventory) }}</strong>
        </div>
        <div class="mini-stat">
          <span>在途合计</span>
          <strong>{{ formatNum(detail.totals.in_transit) }}</strong>
        </div>
        <div class="mini-stat">
          <span>昨日销量</span>
          <strong>{{ formatNum(detail.totals.yesterday_sales) }}</strong>
        </div>
        <div class="mini-stat">
          <span>7 天销量</span>
          <strong>{{ formatNum(detail.totals.seven_sales) }}</strong>
        </div>
        <div class="mini-stat">
          <span>30 天销量</span>
          <strong>{{ formatNum(detail.totals.thirty_sales) }}</strong>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">商品信息（{{ detail.product_code }}）</div>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="款号">{{ detail.product_code }}</el-descriptions-item>
          <el-descriptions-item label="产品名称">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="品牌">{{ detail.brand }}</el-descriptions-item>
          <el-descriptions-item label="品类">{{ detail.category }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detail.supplier }}</el-descriptions-item>
          <el-descriptions-item label="等级">{{ detail.grade }}</el-descriptions-item>
          <el-descriptions-item label="商品情况">{{ detail.status }}</el-descriptions-item>
          <el-descriptions-item label="SKU 数">{{ detail.sku_count }}</el-descriptions-item>
          <el-descriptions-item label="售卖价">{{ detail.sale_price ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="采购价">{{ detail.purchase_price ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="包装">{{ detail.packaging }}</el-descriptions-item>
          <el-descriptions-item label="面料成分" :span="3">{{ detail.material }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="4">{{ detail.notes }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="panel">
        <div class="panel-title">款式明细（按主表结构）</div>
        <el-table :data="detail.skus" size="small" border max-height="520" empty-text="该款没有 SKU">
          <el-table-column prop="barcode" label="条形码" min-width="150" fixed />
          <el-table-column prop="name" label="产品名称" min-width="200" fixed show-overflow-tooltip />
          <el-table-column prop="spec" label="规格" width="90" fixed />
          <el-table-column prop="color" label="颜色" min-width="120" fixed show-overflow-tooltip />
          <el-table-column label="售卖价" width="90" align="right" fixed>
            <template #default="{ row }">{{ row.sale_price ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="采购价" width="90" align="right" fixed>
            <template #default="{ row }">{{ row.purchase_price ?? '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="商品情况" width="110" fixed />
          <el-table-column
            v-for="channel in activeChannels"
            :key="channel.sheet_name"
            :label="channel.sheet_name"
            align="center"
          >
            <el-table-column label="库存" width="100" align="right">
              <template #default="{ row }">{{ formatNum(row.channels[channel.sheet_name]?.inventory) }}</template>
            </el-table-column>
            <el-table-column label="在途" width="90" align="right">
              <template #default="{ row }">{{ formatNum(row.channels[channel.sheet_name]?.in_transit) }}</template>
            </el-table-column>
            <el-table-column label="昨日" width="90" align="right">
              <template #default="{ row }">{{ formatNum(row.channels[channel.sheet_name]?.yesterday_sales) }}</template>
            </el-table-column>
            <el-table-column label="7 天" width="90" align="right">
              <template #default="{ row }">{{ formatNum(row.channels[channel.sheet_name]?.seven_sales) }}</template>
            </el-table-column>
            <el-table-column label="30 天" width="90" align="right">
              <template #default="{ row }">{{ formatNum(row.channels[channel.sheet_name]?.thirty_sales) }}</template>
            </el-table-column>
          </el-table-column>
        </el-table>
      </div>

      <div class="panel">
        <div class="panel-title">渠道汇总</div>
        <el-table :data="channelRows" size="small" border max-height="520">
          <el-table-column prop="sheet_name" label="渠道" min-width="180" fixed />
          <el-table-column prop="brand" label="品牌" width="110" fixed />
          <el-table-column label="库存" width="120" align="right">
            <template #default="{ row }">
              <span :class="{ 'total-text': row.is_total }">{{ formatNum(row.inventory) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="在途" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'total-text': row.is_total }">{{ formatNum(row.in_transit) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="昨日" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'total-text': row.is_total }">{{ formatNum(row.yesterday_sales) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="7 天" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'total-text': row.is_total }">{{ formatNum(row.seven_sales) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="30 天" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'total-text': row.is_total }">{{ formatNum(row.thirty_sales) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import api from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const latestDate = ref('')
const filters = reactive({ search: '', brand: '', supplier: '' })
const brands = ref([])
const suppliers = ref([])
const detail = ref(null)
const detailLoading = ref(false)

const activeChannels = computed(() => {
  if (!detail.value) return []
  return detail.value.channels.filter(
    (channel) =>
      channel.inventory ||
      channel.in_transit ||
      channel.yesterday_sales ||
      channel.seven_sales ||
      channel.thirty_sales
  )
})

const channelRows = computed(() => {
  if (!detail.value) return []
  return [
    ...activeChannels.value.map((channel) => ({ ...channel, is_total: false })),
    {
      sheet_name: '合计',
      brand: '',
      is_total: true,
      inventory: detail.value.totals.inventory,
      in_transit: detail.value.totals.in_transit,
      yesterday_sales: detail.value.totals.yesterday_sales,
      seven_sales: detail.value.totals.seven_sales,
      thirty_sales: detail.value.totals.thirty_sales
    }
  ]
})

async function load(nextPage) {
  if (nextPage) page.value = nextPage
  loading.value = true
  try {
    const { data } = await api.get('/api/styles', {
      params: { ...filters, page: page.value, page_size: pageSize }
    })
    items.value = data.items
    total.value = data.total
    latestDate.value = data.latest_date
  } finally {
    loading.value = false
  }
}

async function openStyle(row) {
  detailLoading.value = true
  try {
    const { data } = await api.get(`/api/styles/${encodeURIComponent(row.product_code)}`)
    detail.value = data
    await nextTick()
    document.getElementById('style-detail')?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      block: 'start'
    })
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detail.value = null
  window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}

async function loadMeta() {
  const [{ data: brandData }, { data: supplierData }] = await Promise.all([
    api.get('/api/meta/brands'),
    api.get('/api/meta/suppliers')
  ])
  brands.value = brandData.brands
  suppliers.value = supplierData.suppliers
}

function formatNum(value) {
  const num = Number(value || 0)
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

onMounted(() => {
  load()
  loadMeta()
})
</script>

<style scoped>
.detail-wrap {
  margin-top: 14px;
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.mini-stat {
  background: #f4f8fd;
  border: 1px solid var(--qoc-line);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mini-stat span {
  color: var(--qoc-muted);
  font-size: 12px;
}

.mini-stat strong {
  color: var(--qoc-ink);
  font-size: 18px;
  font-weight: 700;
  font-family: ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace;
}

.total-text {
  font-weight: 700;
  color: #1f2937;
}

@media (max-width: 1100px) {
  .detail-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .detail-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
