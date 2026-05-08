<template>
  <el-card :title="title" class="chart-card">
    <div class="chart-container">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
    <div class="legend-container">
      <div 
        v-for="(item, key) in data.distribution" 
        :key="key" 
        class="legend-item"
      >
        <span class="legend-color" :style="{ background: getEmotionColor(key) }"></span>
        <span class="legend-label">{{ getEmotionLabel(key) }}</span>
        <span class="legend-value">{{ item }}人 ({{ getPercentage(item) }}%)</span>
      </div>
    </div>
    <div class="total-info">
      总人数：{{ data.total_count || 0 }}人
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { getEmotionLabel, getEmotionColor } from '../../utils/format'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      total_count: 0,
      distribution: {
        happy: 0,
        sad: 0,
        surprised: 0,
        angry: 0,
        neutral: 0
      }
    })
  },
  title: {
    type: String,
    default: '情绪分布'
  }
})

const chartData = computed(() => ({
  labels: ['高兴', '悲伤', '惊讶', '愤怒', '中性'],
  datasets: [{
    data: [
      props.data.distribution.happy || 0,
      props.data.distribution.sad || 0,
      props.data.distribution.surprised || 0,
      props.data.distribution.angry || 0,
      props.data.distribution.neutral || 0
    ],
    backgroundColor: [
      '#FFD93D',
      '#6B7FD7',
      '#FF9F43',
      '#FF6B6B',
      '#A55EEA'
    ],
    borderWidth: 2,
    borderColor: '#fff'
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const value = context.raw
          const total = props.data.total_count || 1
          const percentage = ((value / total) * 100).toFixed(1)
          return `${context.label}: ${value}人 (${percentage}%)`
        }
      }
    }
  }
}

const getPercentage = (value) => {
  const total = props.data.total_count || 1
  return ((value / total) * 100).toFixed(1)
}
</script>

<style scoped>
.chart-card {
  height: 100%;
}

.chart-container {
  height: 250px;
  margin-bottom: 16px;
}

.legend-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-label {
  font-size: 12px;
  color: #666;
}

.legend-value {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.total-info {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
  font-size: 14px;
  color: #666;
}
</style>
