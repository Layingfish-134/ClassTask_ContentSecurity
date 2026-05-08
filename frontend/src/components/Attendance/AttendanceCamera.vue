<template>
  <div class="camera-container">
    <div class="video-wrapper">
      <video ref="videoRef" autoplay playsinline class="video-element"></video>
      <div v-if="!isPreviewing" class="camera-placeholder">
        <el-icon size="64" class="placeholder-icon"><VideoCamera /></el-icon>
        <p>点击下方按钮开启摄像头</p>
      </div>
    </div>
    <div class="camera-controls">
      <el-button 
        :disabled="isProcessing"
        @click="handleStartPreview" 
        v-if="!isPreviewing"
        type="primary"
      >
        <el-icon><VideoCamera /></el-icon>
        开启摄像头
      </el-button>
      <el-button 
        :disabled="isProcessing"
        @click="handleStopPreview" 
        v-else
        type="warning"
      >
        <el-icon><Close /></el-icon>
        关闭摄像头
      </el-button>
      <el-button 
        :disabled="!isPreviewing || isProcessing"
        @click="handleCapture" 
        type="success"
        :loading="isProcessing"
      >
        <el-icon><Camera /></el-icon>
        {{ isProcessing ? '识别中...' : '拍照考勤' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { VideoCamera, Camera, Close } from '@element-plus/icons-vue'
import { initCamera, startPreview, capturePhoto, stopCamera } from '../../utils/camera'

const emit = defineEmits(['photo-captured', 'error'])

const videoRef = ref(null)
const isPreviewing = ref(false)
const isProcessing = ref(false)
let stream = null

const handleStartPreview = async () => {
  try {
    stream = await initCamera()
    if (videoRef.value) {
      startPreview(videoRef.value, stream)
      isPreviewing.value = true
    }
  } catch (error) {
    emit('error', error)
  }
}

const handleStopPreview = () => {
  stopCamera(stream)
  isPreviewing.value = false
  stream = null
}

const handleCapture = async () => {
  if (!videoRef.value || !isPreviewing.value) return
  
  isProcessing.value = true
  
  try {
    const imageBase64 = capturePhoto(videoRef.value)
    emit('photo-captured', imageBase64)
  } catch (error) {
    emit('error', error)
  } finally {
    isProcessing.value = false
  }
}

onUnmounted(() => {
  stopCamera(stream)
})
</script>

<style scoped>
.camera-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.video-wrapper {
  width: 100%;
  max-width: 640px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 4/3;
  position: relative;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  background: #1a1a1a;
}

.placeholder-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.camera-controls {
  display: flex;
  gap: 12px;
}

.camera-controls .el-button {
  padding: 12px 24px;
  font-size: 14px;
}
</style>
