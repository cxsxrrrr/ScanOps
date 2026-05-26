import { useEffect, useRef } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setTokenGetter, signalAuthReady } from '../lib/api'

export function useApiSetup() {
  const { getToken, isLoaded, isSignedIn } = useAuth()
  const getTokenRef = useRef(getToken)
  getTokenRef.current = getToken

  // Stable wrapper so interceptor always calls latest getToken
  setTokenGetter(() => getTokenRef.current())

  // Unblock interceptor as soon as Clerk is loaded (public endpoints need this)
  useEffect(() => {
    if (isLoaded) signalAuthReady()
  }, [isLoaded])

  // Warm the JWT token for signed-in users
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return

    let cancelled = false

    async function warmToken() {
      for (let i = 0; i < 15; i++) {
        const token = await getTokenRef.current().catch(() => null)
        if (cancelled) return
        if (token) return  // Token warm, interceptor already unblocked
        await new Promise(r => setTimeout(r, 200))
      }
    }

    warmToken()
    return () => { cancelled = true }
  }, [isLoaded, isSignedIn])
}
