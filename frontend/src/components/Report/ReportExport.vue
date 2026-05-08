<template>
  <el-card title="报表导出" class="report-card">
    <el-form :model="form" class="export-form">
      <el-form-item label="报表类型">
        <el-select v-model="form.reportType" placeholder="请选择报表类型">
          <el-option label="考勤报表" value="attendance"></el-option>
          <el-option label="活动频次报表" value="activityFrequency"></el-option>
        </el-select>
      </el-form-item>
      
      <el-form-item label="班级" v-if="form.reportType === 'attendance'">
        <el-input v-model="form.class_name" placeholder="请输入班级名称"></el-input>
      </el-form-item>
      
      <el-form-item label="开始时间" v-if="form.reportType === 'attendance'">
        <el-date-picker 
          v-model="form.start_time" 
          type="datetime" 
          placeholder="选择开始时间"
        />
      </el-form-item>
      
      <el-form-item label="结束时间" v-if="form.reportType === 'attendance'">
        <el-date-picker 
          v-model="form.end_time" 
          type="datetime" 
          placeholder="选择结束时间"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleExport"
          :loading="isExporting"
        >
          <el-icon><Download /></el-icon>
          {{ isExporting ? '导出中...' : '导出报表' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { exportAttendance, exportActivityFrequency } from '../../api/report'
import { downloadFile } from '../../utils/file'

const emit = defineEmits(['export'])

const form = reactive({
  reportType: 'attendance',
  class_name: '',
  start_time: '',
  end_time: ''
})

const isExporting = ref(false)

const handleExport = async () => {
  if (form.reportType === 'attendance') {
    if (!form.start_time || !form.end_time) {
      emit('export', { error: '请选择时间范围' })
      return
    }
  }
  
  isExporting.value = true
  
  try {
    let response, filename
    
    if (form.reportType === 'attendance') {
      response = await exportAttendance({
        class_name: form.class_name,
        start_time: form.start_time.toISOString(),
        end_time: form.end_time.toISOString()
      })
      filename = `考勤报表_${new Date().toLocaleDateString()}.xlsx`
    } else {
      response = await exportActivityFrequency({
        class_name: form.class_name
      })
      filename = `活动频次报表_${new Date().toLocaleDateString()}.xlsx`
    }
    
    if (response instanceof Blob) {
      downloadFile(response, filename)
    } else if (response.code === 200 && response.data) {
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      downloadFile(blob, filename)
    }
    
    emit('export', { success: true })
  } catch (error) {
    emit('export', { error: error.message })
  } finally {
    isExporting.value = false
  }
}
</script>

<style scoped>
.report-card {
  max-width: 500px;
}

.export-form {
  padding: 16px;
}
</style>
