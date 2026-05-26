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

let getTokenFn = null

// Resolved by signalAuthReady() once Clerk confirms isLoaded && isSignedIn.
// Blocks the interceptor so no request fires before the JWT cache is warm.
let _resolveReady
const _authReady = new Promise(resolve => { _resolveReady = resolve })

export function setTokenGetter(fn) {
  getTokenFn = fn
}

// Called from useApiSetup effect when Clerk is fully loaded and signed in.
export function signalAuthReady() {
  _resolveReady()
}

// Request interceptor — inject Authorization header
api.interceptors.request.use(async (config) => {
  await _authReady
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
