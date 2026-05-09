import axios from 'axios'
import config from '../config'

const instance = axios.create({
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout
})

const redirectToLogin = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  if (window.location.pathname !== '/login.html') {
    window.location.href = '/login.html'
  }
}

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
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
    }
    return Promise.reject(error)
  }
)

export const get = (url, params) => instance.get(url, { params })
export const post = (url, data) => instance.post(url, data)
export const put = (url, data) => instance.put(url, data)
export const del = (url) => instance.delete(url)

export default instance
