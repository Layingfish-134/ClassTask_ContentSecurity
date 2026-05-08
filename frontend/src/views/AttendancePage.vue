<template>
  <div class="attendance-page">
    <el-card title="实时考勤" class="main-card">
      <AttendanceCamera 
        @photo-captured="handlePhotoCaptured" 
        @error="handleCameraError" 
      />
    </el-card>
    
    <AttendanceResult 
      :visible="showResult" 
      :result="attendanceResult"
      :message="errorMessage"
      @retry="handleRetry" 
    />
    
    <AttendanceRecord 
      :records="records"
      :loading="loading"
      :pagination="pagination"
      @search="handleSearch"
      @page-change="handlePageChange"
    />
    
    <Loading :visible="isProcessing" text="识别中..." />
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
import AttendanceCamera from '../components/Attendance/AttendanceCamera.vue'
import AttendanceResult from '../components/Attendance/AttendanceResult.vue'
import AttendanceRecord from '../components/Attendance/AttendanceRecord.vue'
import Loading from '../components/Common/Loading.vue'
import ErrorAlert from '../components/Common/ErrorAlert.vue'
import { checkin, getRecords } from '../api/attendance'

const showResult = ref(false)
const attendanceResult = ref(null)
const isProcessing = ref(false)
const showError = ref(false)
const errorMessage = ref('')
const loading = ref(false)

const records = ref([])
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const handlePhotoCaptured = async (imageBase64) => {
  isProcessing.value = true
  
  try {
    const response = await checkin(imageBase64, 'jpg')
    
    if (response.code === 200) {
      attendanceResult.value = response.data
      showResult.value = true
      errorMessage.value = ''
      await loadRecords()
    } else {
      attendanceResult.value = { status: 0 }
      showResult.value = true
      errorMessage.value = response.message || '考勤失败'
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.message || '考勤失败，请重试'
  } finally {
    isProcessing.value = false
  }
}

const handleCameraError = (error) => {
  showError.value = true
  errorMessage.value = error.message
}

const handleRetry = () => {
  showResult.value = false
  attendanceResult.value = null
  errorMessage.value = ''
}

const handleSearch = async (params) => {
  pagination.page = params.page || 1
  await loadRecords(params)
}

const handlePageChange = async (params) => {
  if (params.page) pagination.page = params.page
  if (params.size) pagination.size = params.size
  await loadRecords()
}

const loadRecords = async (params = {}) => {
  loading.value = true
  
  try {
    const response = await getRecords({
      page: pagination.page,
      size: pagination.size,
      ...params
    })
    
    if (response.code === 200) {
      records.value = response.data.records || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('加载考勤记录失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.attendance-page {
  max-width: 900px;
  margin: 0 auto;
}

.main-card {
  text-align: center;
}
</style>
