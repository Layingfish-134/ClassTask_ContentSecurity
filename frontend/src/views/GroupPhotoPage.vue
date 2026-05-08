<template>
  <div class="group-photo-page">
    <PhotoUpload 
      @upload="handleUpload" 
      @error="handleError" 
    />
    
    <PhotoResult 
      :visible="showResult" 
      :result="recognizeResult" 
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
import { ref } from 'vue'
import PhotoUpload from '../components/GroupPhoto/PhotoUpload.vue'
import PhotoResult from '../components/GroupPhoto/PhotoResult.vue'
import Loading from '../components/Common/Loading.vue'
import ErrorAlert from '../components/Common/ErrorAlert.vue'
import { recognize } from '../api/groupPhoto'

const showResult = ref(false)
const recognizeResult = ref(null)
const isProcessing = ref(false)
const showError = ref(false)
const errorMessage = ref('')

const handleUpload = async ({ imageBase64, format, activityName }) => {
  isProcessing.value = true
  
  try {
    const response = await recognize(imageBase64, format, activityName)
    
    if (response.code === 200) {
      recognizeResult.value = response.data
      showResult.value = true
      errorMessage.value = ''
    } else {
      showError.value = true
      errorMessage.value = response.message || '识别失败'
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.message || '识别失败，请重试'
  } finally {
    isProcessing.value = false
  }
}

const handleError = (error) => {
  showError.value = true
  errorMessage.value = error.message
}
</script>

<style scoped>
.group-photo-page {
  max-width: 800px;
  margin: 0 auto;
}
</style>
