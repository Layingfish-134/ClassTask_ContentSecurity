<template>
  <el-card title="识别结果" class="result-card" v-if="visible && result">
    <div class="result-summary">
      <div class="summary-item">
        <span class="label">活动名称</span>
        <span class="value">{{ result.activity_name || '未命名' }}</span>
      </div>
      <div class="summary-item">
        <span class="label">照片名称</span>
        <span class="value">{{ result.photo_name }}</span>
      </div>
      <div class="summary-item">
        <span class="label">识别人数</span>
        <span class="value highlight">{{ result.recognized_count }} / {{ result.total_faces }}</span>
      </div>
    </div>
    
    <div class="students-section">
      <h4 class="section-title">识别到的学生</h4>
      <el-table 
        :data="result.students" 
        border 
        class="students-table"
      >
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="class_name" label="班级" width="150" />
        <el-table-column prop="confidence" label="匹配置信度" width="120">
          <template #default="scope">
            {{ formatConfidence(scope.row.confidence) }}
          </template>
        </el-table-column>
        <el-table-column prop="emotion" label="情绪" width="100">
          <template #default="scope">
            <span :class="getEmotionClass(scope.row.emotion)" class="emotion-tag">
              {{ getEmotionLabel(scope.row.emotion) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="emotion_confidence" label="情绪置信度" width="120">
          <template #default="scope">
            {{ formatConfidence(scope.row.emotion_confidence) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { formatConfidence, getEmotionLabel, getEmotionClass } from '../../utils/format'

defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  }
})
</script>

<style scoped>
.result-card {
  margin-top: 20px;
}

.result-summary {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.summary-item {
  display: flex;
  flex-direction: column;
}

.summary-item .label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.summary-item .value {
  font-size: 16px;
  font-weight: 500;
}

.summary-item .value.highlight {
  color: #667eea;
}

.section-title {
  margin-bottom: 12px;
  font-size: 14px;
  color: #333;
}

.students-table {
  margin-top: 8px;
}
</style>
