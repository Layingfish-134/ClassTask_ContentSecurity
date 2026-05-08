export const initCamera = async (constraints = {}) => {
  const defaultConstraints = {
    video: {
      width: 640,
      height: 480,
      facingMode: 'user'
    }
  }
  
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      ...defaultConstraints,
      ...constraints
    })
    return stream
  } catch (error) {
    throw new Error(`摄像头初始化失败: ${error.message}`)
  }
}

export const startPreview = (videoElement, stream) => {
  videoElement.srcObject = stream
}

export const capturePhoto = (videoElement) => {
  const canvas = document.createElement('canvas')
  canvas.width = videoElement.videoWidth || 640
  canvas.height = videoElement.videoHeight || 480
  
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)
  
  return canvas.toDataURL('image/jpeg', 0.9)
}

export const stopCamera = (stream) => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
}

export const detectFace = (videoElement) => {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas')
    canvas.width = videoElement.videoWidth || 640
    canvas.height = videoElement.videoHeight || 480
    
    const ctx = canvas.getContext('2d')
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const pixels = imageData.data
    
    let brightnessSum = 0
    let pixelCount = 0
    
    for (let i = 0; i < pixels.length; i += 4) {
      const brightness = (pixels[i] * 0.299 + pixels[i + 1] * 0.587 + pixels[i + 2] * 0.114)
      brightnessSum += brightness
      pixelCount++
    }
    
    const avgBrightness = brightnessSum / pixelCount
    
    resolve({
      detected: avgBrightness > 50,
      brightness: avgBrightness
    })
  })
}
