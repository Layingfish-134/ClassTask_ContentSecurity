import config from '../config'

export const validateFile = (file) => {
  if (!file) {
    return { valid: false, message: '请选择文件' }
  }
  
  if (!config.file.supportedTypes.includes(file.type)) {
    return { valid: false, message: '只支持JPG、PNG格式的图片' }
  }
  
  if (file.size > config.file.maxSize) {
    return { valid: false, message: `文件大小不能超过${config.file.maxSize / (1024 * 1024)}MB` }
  }
  
  return { valid: true, message: '' }
}

export const compressImage = (file, maxSizeKB = 1024) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      const img = new Image()
      img.src = e.target.result
      
      img.onload = () => {
        let quality = 0.9
        let canvas = document.createElement('canvas')
        let ctx = canvas.getContext('2d')
        
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)
        
        let dataUrl = canvas.toDataURL('image/jpeg', quality)
        let blob = dataURItoBlob(dataUrl)
        
        while (blob.size > maxSizeKB * 1024 && quality > 0.1) {
          quality -= 0.1
          dataUrl = canvas.toDataURL('image/jpeg', quality)
          blob = dataURItoBlob(dataUrl)
        }
        
        resolve(blob)
      }
    }
    
    reader.readAsDataURL(file)
  })
}

export const dataURItoBlob = (dataURI) => {
  const byteString = atob(dataURI.split(',')[1])
  const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0]
  const ab = new ArrayBuffer(byteString.length)
  const ia = new Uint8Array(ab)
  
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i)
  }
  
  return new Blob([ab], { type: mimeString })
}

export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      resolve(e.target.result)
    }
    
    reader.onerror = (error) => {
      reject(error)
    }
    
    reader.readAsDataURL(file)
  })
}

export const downloadFile = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
