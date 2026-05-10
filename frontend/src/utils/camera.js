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
    let skinPixelCount = 0

    for (let i = 0; i < pixels.length; i += 4) {
      const r = pixels[i]
      const g = pixels[i + 1]
      const b = pixels[i + 2]

      const brightness = (r * 0.299 + g * 0.587 + b * 0.114)
      brightnessSum += brightness
      pixelCount++

      if (isSkinColor(r, g, b)) {
        skinPixelCount++
      }
    }

    const avgBrightness = brightnessSum / pixelCount
    const skinRatio = skinPixelCount / pixelCount

    const brightnessDetected = avgBrightness > 50
    const skinDetected = skinRatio > 0.02

    resolve({
      detected: brightnessDetected && skinDetected,
      brightness: avgBrightness,
      skinRatio: skinRatio,
      confidence: Math.min(brightnessDetected * 0.5 + skinDetected * 0.5, 1)
    })
  })
}

const isSkinColor = (r, g, b) => {
  if (r < 95 || g < 40 || b < 20) return false

  const maxRGB = Math.max(r, g, b)
  const minRGB = Math.min(r, g, b)

  const delta = maxRGB - minRGB

  if (delta < 15) return false
  if (r / maxRGB < 0.62 || g / maxRGB < 0.51) return false

  const rG = r - g
  if (rG < 10 || rG > 45) return false

  const rbDiff = Math.abs(r - b)
  if (rbDiff < 10) return false

  return true
}
