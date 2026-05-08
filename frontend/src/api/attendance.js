import { post, get } from '../utils/request'

export const checkin = (imageBase64, format) => {
  return post('/attendance/checkin', {
    image_base64: imageBase64,
    image_format: format
  })
}

export const getRecords = (params) => {
  return get('/attendance/records', params)
}

export const getRecordById = (id) => {
  return get(`/attendance/records/${id}`)
}
