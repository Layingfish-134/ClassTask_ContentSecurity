import axios from 'axios'
import config from '../config'

const instance = axios.create({
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout
})

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
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export const get = (url, params) => instance.get(url, { params })
export const post = (url, data) => instance.post(url, data)
export const put = (url, data) => instance.put(url, data)
export const del = (url) => instance.delete(url)

export default instance
