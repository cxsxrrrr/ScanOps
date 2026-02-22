/**
 * Custom hook for API calls with Clerk token integration.
 */
import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setTokenGetter } from '../lib/api'

export function useApiSetup() {
  const { getToken } = useAuth()

  useEffect(() => {
    setTokenGetter(getToken)
  }, [getToken])
}
