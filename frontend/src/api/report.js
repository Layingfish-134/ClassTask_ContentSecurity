import { get } from '../utils/request'

export const exportAttendance = (params) => {
  return get('/reports/attendance/export', params, {
    responseType: 'blob'
  })
}

export const exportActivityFrequency = (params) => {
  return get('/reports/activity-frequency/export', params, {
    responseType: 'blob'
  })
}
