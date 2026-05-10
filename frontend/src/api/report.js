import { get } from '../utils/request'

export const exportAttendance = (params) => {
  return get('/reports/attendance/export', params, {
    responseType: 'blob'
  })
}

export const exportAttendanceSummary = (params) => {
  return get('/reports/attendance-summary/export', params, {
    responseType: 'blob'
  })
}

export const exportActivityFrequency = (params) => {
  return get('/reports/activity-frequency/export', params, {
    responseType: 'blob'
  })
}

export const exportStudentActivity = (params) => {
  return get('/reports/activity/export', params, {
    responseType: 'blob'
  })
}

export const exportActivityRecord = (params) => {
  return get('/reports/activity-record/export', params, {
    responseType: 'blob'
  })
}
