<template>
  <el-card title="报表导出" class="report-card">
    <el-form :model="form" class="export-form">
      <el-form-item label="报表类型">
        <el-select v-model="form.reportType" placeholder="请选择报表类型">
          <el-option label="考勤报表" value="attendance"></el-option>
          <el-option label="学生活动参与报表" value="studentActivity"></el-option>
          <el-option label="活动记录报表" value="activityRecord"></el-option>
        </el-select>
      </el-form-item>
      
      <el-form-item label="专业" v-if="form.reportType === 'attendance'">
        <el-input v-model="form.class_name" placeholder="请输入专业名称"></el-input>
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
      
      <el-form-item label="学生学号" v-if="form.reportType === 'studentActivity'" required>
        <el-input v-model="form.student_id" placeholder="请输入学生学号"></el-input>
      </el-form-item>

      <el-form-item label="活动名称" v-if="form.reportType === 'activityRecord'" required>
        <el-input v-model="form.activity_name" placeholder="请输入活动名称"></el-input>
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
import { exportAttendanceSummary, exportStudentActivity, exportActivityRecord } from '../../api/report'
import { downloadFile } from '../../utils/file'

const emit = defineEmits(['export'])

const form = reactive({
  reportType: 'attendance',
  class_name: '',
  start_time: '',
  end_time: '',
  student_id: '',
  activity_name: ''
})

const isExporting = ref(false)

const handleExport = async () => {
  if (form.reportType === 'attendance') {
    if (!form.start_time || !form.end_time) {
      emit('export', { error: '请选择时间范围' })
      return
    }
  } else if (form.reportType === 'studentActivity') {
    if (!form.student_id) {
      emit('export', { error: '请输入学生学号' })
      return
    }
  } else {
    if (!form.activity_name) {
      emit('export', { error: '请输入活动名称' })
      return
    }
  }
  
  isExporting.value = true
  
  try {
    let response, filename
    
    if (form.reportType === 'attendance') {
      response = await exportAttendanceSummary({
        class_name: form.class_name,
        start_time: form.start_time.toISOString(),
        end_time: form.end_time.toISOString()
      })
      filename = `考勤报表_${form.class_name || '全部专业'}_${new Date().toLocaleDateString()}.xlsx`
    } else if (form.reportType === 'studentActivity') {
      response = await exportStudentActivity({
        student_id: form.student_id
      })
      filename = `学生活动参与报表_${form.student_id}_${new Date().toLocaleDateString()}.xlsx`
    } else {
      response = await exportActivityRecord({
        activity_name: form.activity_name
      })
      filename = `活动记录报表_${form.activity_name}_${new Date().toLocaleDateString()}.xlsx`
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
