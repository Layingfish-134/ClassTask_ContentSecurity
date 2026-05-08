import config from '../config'

export const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

export const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

export const formatDateTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${formatDate(d)} ${formatTime(d)}`
}

export const formatConfidence = (value) => {
  if (!value && value !== 0) return '-'
  return `${value.toFixed(1)}%`
}

export const getEmotionLabel = (emotion) => {
  return config.emotions[emotion]?.label || emotion
}

export const getEmotionColor = (emotion) => {
  return config.emotions[emotion]?.color || '#8c8c8c'
}

export const getStatusLabel = (status) => {
  return status === 1 ? '成功' : '失败'
}

export const getStatusColor = (status) => {
  return status === 1 ? '#52c41a' : '#f5222d'
}

export const getEmotionClass = (emotion) => {
  return `emotion-${emotion}`
}
