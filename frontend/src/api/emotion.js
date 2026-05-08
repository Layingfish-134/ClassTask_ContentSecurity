import { get } from '../utils/request'

export const getStatistics = (params) => {
  return get('/emotion/statistics', params)
}

export const getTrend = (params) => {
  return get('/emotion/trend', params)
}
