<template>
  <div ref="chartEl" class="trend-chart" role="img" :aria-label="`${label}趋势图`"></div>
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
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#16242d',
      borderWidth: 0,
      textStyle: { color: '#ffffff', fontSize: 12 }
    },
    grid: { left: 44, right: 20, top: 28, bottom: 30 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#d6e0ee' } },
      axisTick: { show: false },
      axisLabel: { color: '#6a7881', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e6edf6' } },
      axisLabel: { color: '#6a7881', fontSize: 11 }
    },
    series: [
      {
        name: props.label,
        type: 'line',
        smooth: true,
        data: values,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2, color: '#2f6fee' },
        itemStyle: { color: '#2f6fee' },
        areaStyle: { color: 'rgba(47, 111, 238, 0.08)' }
      }
    ]
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
