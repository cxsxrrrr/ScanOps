/**
 * Axios API client with Clerk token injection.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token will be set by the auth hook
let getTokenFn = null

export function setTokenGetter(fn) {
  getTokenFn = fn
}

// Request interceptor — inject Authorization header
api.interceptors.request.use(async (config) => {
  if (getTokenFn) {
    try {
      const token = await getTokenFn()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (err) {
      console.error('Failed to get auth token:', err)
    }
  }
  return config
})

// Response interceptor — handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — Clerk will handle redirect
      console.warn('Unauthorized request')
    }
    return Promise.reject(error)
  }
)

export default api
