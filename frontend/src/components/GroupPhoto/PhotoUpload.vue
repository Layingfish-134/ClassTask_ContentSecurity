<template>
  <div class="photo-upload-container">
    <el-card title="上传合照" class="upload-card">
      <div 
        class="upload-area"
        :class="{ 'drag-over': isDragOver }"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input 
          ref="fileInputRef"
          type="file" 
          accept="image/jpeg,image/png,image/jpg" 
          class="file-input"
          @change="handleFileChange"
        />
        <div class="upload-content">
          <el-icon size="64" class="upload-icon"><Upload /></el-icon>
          <p>点击或拖拽上传合照</p>
          <p class="hint">支持 JPG、PNG 格式，文件大小不超过 10MB</p>
        </div>
      </div>
      
      <div v-if="previewUrl" class="preview-section">
        <h4 class="preview-title">图片预览</h4>
        <img :src="previewUrl" class="preview-image" />
        <div class="preview-info">
          <span>文件名: {{ fileName }}</span>
          <span>大小: {{ formatFileSize(fileSize) }}</span>
        </div>
      </div>
      
      <div class="upload-controls">
        <el-input 
          v-model="activityName" 
          placeholder="活动名称（可选）" 
          class="activity-input"
        />
        <el-button 
          type="primary" 
          :disabled="!previewUrl || isProcessing"
          @click="handleUpload"
          :loading="isProcessing"
        >
          <el-icon><Search /></el-icon>
          {{ isProcessing ? '识别中...' : '开始识别' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, Search } from '@element-plus/icons-vue'
import { validateFile, fileToBase64 } from '../../utils/file'

const emit = defineEmits(['upload', 'error'])

const fileInputRef = ref(null)
const isDragOver = ref(false)
const isProcessing = ref(false)
const previewUrl = ref('')
const fileName = ref('')
const fileSize = ref(0)
const activityName = ref('')

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  const validation = validateFile(file)
  if (!validation.valid) {
    emit('error', new Error(validation.message))
    return
  }
  
  try {
    previewUrl.value = await fileToBase64(file)
    fileName.value = file.name
    fileSize.value = file.size
  } catch (error) {
    emit('error', error)
  }
}

const handleDrop = async (event) => {
  isDragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  
  const validation = validateFile(file)
  if (!validation.valid) {
    emit('error', new Error(validation.message))
    return
  }
  
  try {
    previewUrl.value = await fileToBase64(file)
    fileName.value = file.name
    fileSize.value = file.size
  } catch (error) {
    emit('error', error)
  }
}

const handleUpload = async () => {
  if (!previewUrl.value) return
  
  isProcessing.value = true
  
  try {
    const imageFormat = fileName.value.split('.').pop().toLowerCase()
    emit('upload', {
      imageBase64: previewUrl.value,
      format: imageFormat,
      activityName: activityName.value
    })
  } catch (error) {
    emit('error', error)
  } finally {
    isProcessing.value = false
  }
}

const formatFileSize = (size) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  return `${(size / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<style scoped>
.photo-upload-container {
  max-width: 600px;
  margin: 0 auto;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #667eea;
}

.upload-area.drag-over {
  border-color: #667eea;
  background: #f5f7fa;
}

.file-input {
  display: none;
}

.upload-content {
  color: #8c8c8c;
}

.upload-icon {
  margin-bottom: 16px;
  color: #667eea;
}

.upload-content p {
  margin: 8px 0;
}

.hint {
  font-size: 12px;
  color: #bfbfbf;
}

.preview-section {
  margin-top: 24px;
  text-align: center;
}

.preview-title {
  margin-bottom: 12px;
  font-size: 14px;
  color: #333;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  object-fit: contain;
}

.preview-info {
  margin-top: 12px;
  font-size: 12px;
  color: #8c8c8c;
}

.preview-info span {
  margin-right: 16px;
}

.upload-controls {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.activity-input {
  flex: 1;
}
</style>
