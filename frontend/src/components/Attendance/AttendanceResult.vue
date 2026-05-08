<template>
  <div v-if="visible && result" class="result-card">
    <el-card :title="result.status === 1 ? '考勤成功' : '考勤失败'" class="attendance-result">
      <div v-if="result.status === 1" class="success-content">
        <div class="result-icon success">
          <el-icon size="48"><CircleCheck /></el-icon>
        </div>
        <div class="student-info">
          <div class="info-item">
            <span class="label">学号</span>
            <span class="value">{{ result.student_id }}</span>
          </div>
          <div class="info-item">
            <span class="label">姓名</span>
            <span class="value">{{ result.name }}</span>
          </div>
          <div class="info-item">
            <span class="label">班级</span>
            <span class="value">{{ result.class_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">考勤时间</span>
            <span class="value">{{ formatDateTime(result.attendance_time) }}</span>
          </div>
          <div class="info-item">
            <span class="label">匹配度</span>
            <span class="value">{{ formatConfidence(result.confidence) }}</span>
          </div>
          <div class="info-item">
            <span class="label">情绪</span>
            <span :class="getEmotionClass(result.emotion)" class="emotion-tag">
              {{ getEmotionLabel(result.emotion) }}
            </span>
          </div>
        </div>
      </div>
      <div v-else class="failed-content">
        <div class="result-icon failed">
          <el-icon size="48"><CircleClose /></el-icon>
        </div>
        <p class="failed-message">{{ message || '未匹配到学生信息' }}</p>
        <el-button type="primary" @click="$emit('retry')">
          <el-icon><Refresh /></el-icon>
          重新考勤
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { CircleCheck, CircleClose, Refresh } from '@element-plus/icons-vue'
import { formatDateTime, formatConfidence, getEmotionLabel, getEmotionClass } from '../../utils/format'

defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  },
  message: {
    type: String,
    default: ''
  }
})

defineEmits(['retry'])
</script>

<style scoped>
.result-card {
  margin-top: 16px;
}

.attendance-result {
  text-align: center;
}

.result-icon {
  margin-bottom: 16px;
}

.result-icon.success {
  color: #52c41a;
}

.result-icon.failed {
  color: #f5222d;
}

.success-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.student-info {
  width: 100%;
  max-width: 400px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #8c8c8c;
}

.info-item .value {
  font-weight: 500;
}

.failed-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.failed-message {
  color: #f5222d;
  font-size: 16px;
}
</style>
