/**
 * Axios API client with Clerk token injection.
 */
import axios from 'axios'
import { toast } from 'sonner'

let suspendedToastShown = false

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
      const detail = error.response?.data?.detail || ''
      // Clerk's own session is still valid from the browser's point of view
      // (it never revokes a session for this), so a blocked user just gets
      // this specific detail message on every request forever — surface it
      // once instead of leaving them staring at silent failures.
      if (detail.toLowerCase().includes('suspendida') && !suspendedToastShown) {
        suspendedToastShown = true
        toast.error(detail, { duration: 10000 })
      } else if (!detail) {
        console.warn('Unauthorized request')
      }
    }
    return Promise.reject(error)
  }
)

export default api
