<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">数据导出</div>
        <div class="page-desc">按当前筛选条件导出 Excel / CSV 文件</div>
      </div>
    </div>

    <div class="panel">
      <el-form label-width="100px" style="max-width: 640px">
        <el-form-item label="导出内容">
          <el-radio-group v-model="form.kind">
            <el-radio-button label="products">商品档案</el-radio-button>
            <el-radio-button label="inventory">库存</el-radio-button>
            <el-radio-button label="sales">销量</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="品牌">
          <el-select v-model="form.brand" clearable placeholder="全部品牌" style="width: 220px">
            <el-option v-for="brand in brands" :key="brand" :label="brand" :value="brand" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.kind !== 'products'" label="渠道">
          <el-select v-model="form.sheet" clearable filterable placeholder="全部渠道" style="width: 260px">
            <el-option v-for="name in sheets" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品编码">
          <el-input v-model="form.sku" placeholder="可留空" style="width: 260px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="exporting" @click="exportFile">
            <el-icon class="btn-icon"><Download /></el-icon>
            导出 CSV
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api, { downloadFile } from '../api'

const form = reactive({ kind: 'products', brand: '', sheet: '', sku: '' })
const brands = ref([])
const sheets = ref([])
const exporting = ref(false)

async function loadMeta() {
  const [{ data: meta }, { data: brandData }] = await Promise.all([
    api.get('/api/meta/sheets'),
    api.get('/api/meta/brands')
  ])
  sheets.value = meta.data_sheets
  brands.value = brandData.brands
}

async function exportFile() {
  exporting.value = true
  try {
    const params = new URLSearchParams()
    if (form.brand) params.set('brand', form.brand)
    if (form.sheet) params.set('sheet', form.sheet)
    if (form.sku) params.set('sku', form.sku)
    const { data } = await downloadFile(`/api/export/${form.kind}?${params.toString()}`)
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = `${form.kind}_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出完成')
  } finally {
    exporting.value = false
  }
}

onMounted(loadMeta)
</script>

<style scoped>
.btn-icon {
  margin-right: 4px;
}
</style>
