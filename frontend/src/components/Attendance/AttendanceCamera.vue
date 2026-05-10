<template>
  <div class="camera-container">
    <div class="video-wrapper">
      <video ref="videoRef" autoplay playsinline class="video-element"></video>
      <div v-if="!isPreviewing" class="camera-placeholder">
        <el-icon size="64" class="placeholder-icon"><VideoCamera /></el-icon>
        <p>正在准备摄像头</p>
      </div>
      <div v-if="isPreviewing && isAutoMode" class="auto-mode-indicator">
        <el-icon size="24" class="indicator-icon"><CircleCheck /></el-icon>
        <span>自动识别模式</span>
        <div v-if="faceDetected" class="face-detected-badge">
          <el-icon><User /></el-icon>
          <span>检测到人脸</span>
        </div>
      </div>
    </div>
    <div class="mode-switch">
      <span class="switch-label">签到模式：</span>
      <el-switch
        v-model="isAutoMode"
        :disabled="isBusy || !isPreviewing"
        active-text="自动识别"
        inactive-text="手动拍照"
        @change="handleModeChange"
      />
    </div>
    <div class="camera-controls">
      <el-button 
        :disabled="isBusy"
        @click="handleStartPreview" 
        v-if="!isPreviewing"
        type="primary"
      >
        <el-icon><VideoCamera /></el-icon>
        开启摄像头
      </el-button>
      <el-button 
        :disabled="isBusy"
        @click="handleStopPreview" 
        v-else
        type="warning"
      >
        <el-icon><Close /></el-icon>
        关闭摄像头
      </el-button>
      <el-button 
        :disabled="!isPreviewing || isBusy || isAutoMode"
        @click="handleCapture" 
        type="success"
        :loading="isBusy"
      >
        <el-icon><Camera /></el-icon>
        {{ isBusy ? '识别中...' : '拍照考勤' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { VideoCamera, Camera, Close, CircleCheck, User } from '@element-plus/icons-vue'
import { initCamera, startPreview, capturePhoto, stopCamera, detectFace } from '../../utils/camera'

const emit = defineEmits(['photo-captured', 'error'])

const props = defineProps({
  processing: {
    type: Boolean,
    default: false
  }
})

const videoRef = ref(null)
const isPreviewing = ref(false)
const isProcessing = ref(false)
const isAutoMode = ref(true)
const faceDetected = ref(false)
const autoDetecting = ref(false)
const isBusy = computed(() => isProcessing.value || props.processing)
let stream = null
let detectionInterval = null
let cooldownTimer = null

const handleStartPreview = async () => {
  try {
    stream = await initCamera()
    if (videoRef.value) {
      await startPreview(videoRef.value, stream)
      isPreviewing.value = true
      if (isAutoMode.value) {
        startFaceDetection()
      }
    }
  } catch (error) {
    emit('error', error)
  }
}

const handleStopPreview = () => {
  stopFaceDetection()
  stopCamera(stream)
  isPreviewing.value = false
  isProcessing.value = false
  faceDetected.value = false
  autoDetecting.value = false
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

const handleModeChange = (value) => {
  if (value) {
    startFaceDetection()
  } else {
    stopFaceDetection()
    faceDetected.value = false
  }
}

const startFaceDetection = () => {
  if (!isPreviewing.value || detectionInterval) return

  autoDetecting.value = true
  detectionInterval = window.setInterval(async () => {
    if (!videoRef.value || isBusy.value || !autoDetecting.value) return

    try {
      const result = await detectFace(videoRef.value)
      faceDetected.value = result.detected

      if (result.detected && !isBusy.value && autoDetecting.value) {
        autoDetecting.value = false
        const imageBase64 = capturePhoto(videoRef.value)
        emit('photo-captured', imageBase64)
      }
    } catch (error) {
      console.error('人脸检测失败:', error)
    }
  }, 2000)
}

const stopFaceDetection = () => {
  if (detectionInterval) {
    window.clearInterval(detectionInterval)
    detectionInterval = null
  }
  if (cooldownTimer) {
    window.clearTimeout(cooldownTimer)
    cooldownTimer = null
  }
  autoDetecting.value = false
}

watch(() => props.processing, (processing) => {
  if (!processing && isAutoMode.value && isPreviewing.value) {
    cooldownTimer = window.setTimeout(() => {
      if (isAutoMode.value && isPreviewing.value && !props.processing) {
        autoDetecting.value = true
        faceDetected.value = false
      }
    }, 3000)
  }
})

watch(isAutoMode, (newVal) => {
  if (newVal && isPreviewing.value) {
    startFaceDetection()
  } else {
    stopFaceDetection()
    faceDetected.value = false
  }
})

onMounted(async () => {
  await nextTick()
  await handleStartPreview()
})

onUnmounted(() => {
  stopFaceDetection()
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

.auto-mode-indicator {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 20px;
  color: #52c41a;
  font-size: 14px;
}

.indicator-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.face-detected-badge {
  position: absolute;
  top: 50px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(82, 196, 26, 0.9);
  border-radius: 16px;
  color: #fff;
  font-size: 12px;
  animation: fadeIn 0.3s ease;
  white-space: nowrap;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.switch-label {
  font-size: 14px;
  color: #666;
}

.camera-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.camera-controls .el-button {
  padding: 12px 24px;
  font-size: 14px;
}
</style>
