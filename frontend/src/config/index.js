export default {
  api: {
    baseUrl: '/api',
    timeout: 30000,
    retryCount: 3
  },
  
  file: {
    maxSize: 10 * 1024 * 1024,
    supportedTypes: ['image/jpeg', 'image/png', 'image/jpg']
  },
  
  camera: {
    width: 640,
    height: 480,
    facingMode: 'user'
  },
  
  pagination: {
    defaultSize: 20,
    pageSizes: [10, 20, 50, 100]
  },
  
  emotions: {
    happy: { label: '高兴', color: '#FFD93D' },
    sad: { label: '悲伤', color: '#6B7FD7' },
    surprised: { label: '惊讶', color: '#FF9F43' },
    angry: { label: '愤怒', color: '#FF6B6B' },
    neutral: { label: '中性', color: '#A55EEA' }
  },
  
  routes: {
    attendance: 'attendance',
    groupPhoto: 'groupPhoto',
    analysis: 'analysis',
    student: 'student'
  }
}
