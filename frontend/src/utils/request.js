import axios from 'axios'
import config from '../config'

const instance = axios.create({
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout
})

const redirectToLogin = () => {
  sessionStorage.removeItem('access_token')
  sessionStorage.removeItem('refresh_token')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  if (window.location.pathname !== '/login.html') {
    window.location.href = '/login.html'
  }
}

const getApiErrorMessage = (data, fallback) => {
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (data.message) {
    if (typeof data.message === 'string') return data.message
    if (typeof data.message === 'object') {
      return Object.values(data.message).flat().join('；') || fallback
    }
  }
  if (data.msg) return data.msg
  if (data.error) return data.error
  return fallback
}

instance.interceptors.request.use(
  (config) => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    const token = sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data || {}
      const isAuthError = status === 401 || (status === 422 && data.msg)
      if (isAuthError) {
        redirectToLogin()
      }
      const message = getApiErrorMessage(data, `请求失败（HTTP ${status}）`)
      const apiError = new Error(message)
      apiError.status = status
      apiError.code = data.code
      apiError.data = data.data
      apiError.requestId = data.request_id
      apiError.response = error.response
      return Promise.reject(apiError)
    }
    return Promise.reject(error)
  }
)

export const get = (url, params, config = {}) => instance.get(url, { ...config, params })
export const post = (url, data, config = {}) => instance.post(url, data, config)
export const put = (url, data, config = {}) => instance.put(url, data, config)
export const del = (url, config = {}) => instance.delete(url, config)

export default instance
