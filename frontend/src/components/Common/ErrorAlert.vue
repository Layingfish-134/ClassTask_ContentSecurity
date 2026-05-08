<template>
  <el-alert
    v-if="visible"
    :type="type"
    :title="message"
    closable
    @close="handleClose"
    class="error-alert"
  />
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'error'
  }
})

const emit = defineEmits(['close'])

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.error-alert {
  margin-bottom: 16px;
}
</style>
