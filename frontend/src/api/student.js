import { post, get, put, del } from '../utils/request'

export const create = (studentData) => {
  return post('/students', studentData)
}

export const list = (params) => {
  return get('/students', params)
}

export const getById = (id) => {
  return get(`/students/${id}`)
}

export const update = (id, studentData) => {
  return put(`/students/${id}`, studentData)
}

export const remove = (id) => {
  return del(`/students/${id}`)
}
