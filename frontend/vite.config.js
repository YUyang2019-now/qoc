import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'axios'],
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          echarts: ['echarts']
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
