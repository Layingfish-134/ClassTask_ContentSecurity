import { post, get } from '../utils/request'

export const recognize = (imageBase64, format, activityName = '') => {
  return post('/group-photo/recognize', {
    photo_base64: imageBase64,
    image_base64: imageBase64,
    image_format: format,
    activity_name: activityName
  })
}

export const getRecords = (params) => {
  return get('/group-photo/records', params)
}

export const getRecordById = (id) => {
  return get(`/group-photo/records/${id}`)
}
