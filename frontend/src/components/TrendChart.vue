<template>
  <div ref="chartEl" class="trend-chart"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  seriesKey: { type: String, default: 'inventory' },
  label: { type: String, default: '数值' }
})

const chartEl = ref(null)
let chart = null

function render() {
  if (!chart) return
  const dates = props.points.map((p) => p.date)
  const values = props.points.map((p) => p[props.seriesKey] ?? null)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    series: [{ name: props.label, type: 'line', smooth: true, data: values, areaStyle: { opacity: 0.12 } }]
  })
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  render()
  window.addEventListener('resize', resize)
})

function resize() {
  chart && chart.resize()
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})

watch(() => [props.points, props.seriesKey], render, { deep: true })
</script>

<style scoped>
.trend-chart {
  width: 100%;
  height: 320px;
}
</style>
