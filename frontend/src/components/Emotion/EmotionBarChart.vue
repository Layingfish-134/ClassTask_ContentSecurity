<template>
  <el-card title="情绪趋势分析" class="chart-card">
    <div class="chart-container">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  groupBy: {
    type: String,
    default: 'time'
  }
})

const emotionColors = {
  happy: '#FFD93D',
  sad: '#6B7FD7',
  surprised: '#FF9F43',
  angry: '#FF6B6B',
  neutral: '#A55EEA'
}

const emotionLabels = {
  happy: '高兴',
  sad: '悲伤',
  surprised: '惊讶',
  angry: '愤怒',
  neutral: '中性'
}

const chartData = computed(() => {
  const labels = props.data.map(item => item.label)
  
  const datasets = Object.keys(emotionColors).map(emotion => ({
    label: emotionLabels[emotion],
    data: props.data.map(item => item.distribution[emotion] || 0),
    backgroundColor: emotionColors[emotion],
    borderRadius: 4,
    barThickness: 20
  }))
  
  return { labels, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom'
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          return `${context.dataset.label}: ${context.raw}人`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: '人数'
      }
    },
    x: {
      title: {
        display: true,
        text: props.groupBy === 'time' ? '时间段' : '班级'
      }
    }
  }
}
</script>

<style scoped>
.chart-card {
  height: 100%;
}

.chart-container {
  height: 300px;
}
</style>
