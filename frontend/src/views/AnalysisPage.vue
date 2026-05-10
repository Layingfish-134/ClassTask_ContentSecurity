<template>
  <div class="analysis-page">
    <div class="filter-section">
      <el-card title="筛选条件" class="filter-card">
        <el-form :model="filters" class="filter-form">
          <el-form-item label="专业">
            <el-input v-model="filters.class_name" placeholder="请输入专业名称"></el-input>
          </el-form-item>
          <el-form-item label="开始时间">
            <el-date-picker 
              v-model="filters.start_time" 
              type="datetime" 
              placeholder="选择开始时间"
            />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker 
              v-model="filters.end_time" 
              type="datetime" 
              placeholder="选择结束时间"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <div class="charts-section">
      <div class="chart-item">
        <EmotionPieChart :data="emotionData" title="情绪分布统计" />
      </div>
      <div class="chart-item full-width">
        <EmotionBarChart :data="trendData" group-by="time" />
      </div>
    </div>
    
    <div class="report-section">
      <ReportExport @export="handleExport" />
    </div>
    
    <Loading :visible="loading" text="加载中..." />
    <ErrorAlert 
      :visible="showError" 
      :message="errorMessage"
      type="error"
      @close="showError = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import EmotionPieChart from '../components/Emotion/EmotionPieChart.vue'
import EmotionBarChart from '../components/Emotion/EmotionBarChart.vue'
import ReportExport from '../components/Report/ReportExport.vue'
import Loading from '../components/Common/Loading.vue'
import ErrorAlert from '../components/Common/ErrorAlert.vue'
import { getStatistics, getTrend } from '../api/emotion'

const loading = ref(false)
const showError = ref(false)
const errorMessage = ref('')

const filters = reactive({
  class_name: '',
  start_time: '',
  end_time: ''
})

const emotionData = ref({
  total_count: 0,
  distribution: {
    happy: 0,
    sad: 0,
    surprised: 0,
    angry: 0,
    neutral: 0
  }
})

const trendData = ref([
  { label: '第一周', distribution: { happy: 10, sad: 5, surprised: 8, angry: 2, neutral: 15 } },
  { label: '第二周', distribution: { happy: 15, sad: 3, surprised: 6, angry: 1, neutral: 20 } },
  { label: '第三周', distribution: { happy: 12, sad: 4, surprised: 10, angry: 3, neutral: 18 } },
  { label: '第四周', distribution: { happy: 18, sad: 2, surprised: 7, angry: 1, neutral: 14 } }
])

const handleFilter = async () => {
  await loadEmotionData()
}

const handleReset = () => {
  filters.class_name = ''
  filters.start_time = ''
  filters.end_time = ''
  loadEmotionData()
}

const handleExport = (result) => {
  if (result.success) {
    showError.value = false
  } else if (result.error) {
    showError.value = true
    errorMessage.value = result.error
  }
}

const loadEmotionData = async () => {
  loading.value = true
  
  try {
    const params = {}
    if (filters.class_name) params.class_name = filters.class_name
    if (filters.start_time) params.start_time = filters.start_time.toISOString()
    if (filters.end_time) params.end_time = filters.end_time.toISOString()
    
    const [statsResponse, trendResponse] = await Promise.all([
      getStatistics(params),
      getTrend(params)
    ])
    
    if (statsResponse.code === 200) {
      emotionData.value = statsResponse.data
    }
    
    if (trendResponse.code === 200) {
      trendData.value = trendResponse.data
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.message || '加载数据失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadEmotionData()
})
</script>

<style scoped>
.analysis-page {
  max-width: 1200px;
  margin: 0 auto;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-card {
  max-width: 800px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-item {
  min-height: 350px;
}

.chart-item.full-width {
  grid-column: 1 / -1;
}

.report-section {
  display: flex;
  justify-content: center;
}
</style>
