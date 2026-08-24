<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">商品档案</div>
        <div class="page-desc">全部品牌主表的商品信息，可手工编辑</div>
      </div>
      <el-button :icon="Download" @click="$router.push('/export')">导出</el-button>
    </div>

    <div class="panel">
      <div class="filter-row">
        <el-input
          v-model="filters.search"
          placeholder="搜索条形码 / 货号 / 名称 / 规格"
          clearable
          style="width: 300px"
          @keyup.enter="load(1)"
          @clear="load(1)"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.brand" placeholder="品牌" clearable style="width: 160px" @change="load(1)">
          <el-option v-for="brand in brands" :key="brand" :label="brand" :value="brand" />
        </el-select>
        <el-button type="primary" @click="load(1)">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="items" size="small">
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="sheet_name" label="来源表" width="150" />
        <el-table-column prop="barcode" label="条形码" min-width="130" />
        <el-table-column prop="product_code" label="产品编号" min-width="120" />
        <el-table-column prop="name" label="产品名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="spec" label="规格" width="90" />
        <el-table-column prop="color" label="颜色" min-width="120" show-overflow-tooltip />
        <el-table-column prop="supplier" label="供应商" width="110" />
        <el-table-column label="售卖价" width="90" align="right">
          <template #default="{ row }">{{ row.sale_price ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="采购价" width="90" align="right">
          <template #default="{ row }">{{ row.purchase_price ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="editVisible" title="编辑商品" width="680px" destroy-on-close>
      <el-form :model="editForm" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="产品名称"><el-input v-model="editForm.name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌"><el-input v-model="editForm.brand" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="条形码"><el-input v-model="editForm.barcode" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品编号"><el-input v-model="editForm.product_code" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规格"><el-input v-model="editForm.spec" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="颜色"><el-input v-model="editForm.color" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供应商"><el-input v-model="editForm.supplier" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="等级"><el-input v-model="editForm.grade" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="售卖价"><el-input-number v-model="editForm.sale_price" :precision="2" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采购价"><el-input-number v-model="editForm.purchase_price" :precision="2" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="商品情况"><el-input v-model="editForm.status" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="包装"><el-input v-model="editForm.packaging" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="面料成分"><el-input v-model="editForm.material" type="textarea" :rows="2" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注"><el-input v-model="editForm.notes" type="textarea" :rows="2" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Download, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const items = ref([])
const brands = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const filters = reactive({ search: '', brand: '' })

const editVisible = ref(false)
const saving = ref(false)
const editForm = reactive({})

async function load(nextPage) {
  if (nextPage) page.value = nextPage
  loading.value = true
  try {
    const { data } = await api.get('/api/products', {
      params: { ...filters, page: page.value, page_size: pageSize }
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadBrands() {
  const { data } = await api.get('/api/meta/brands')
  brands.value = data.brands
}

function openEdit(row) {
  Object.keys(editForm).forEach((key) => delete editForm[key])
  Object.assign(editForm, row)
  editVisible.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await api.put(`/api/products/${editForm.id}`, editForm)
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  load()
  loadBrands()
})
</script>
