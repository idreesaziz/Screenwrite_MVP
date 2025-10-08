import { useState, useEffect } from 'react'
import { supabase } from '~/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

export interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
}

export interface AuthActions {
  signIn: (email: string, password: string) => Promise<{ error: any }>
  signUp: (email: string, password: string) => Promise<{ error: any }>
  signOut: () => Promise<{ error: any }>
  getToken: () => Promise<string | null>
}

export type UseAuthReturn = AuthState & AuthActions

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    const initializeAuth = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Error getting session:', error)
        }
        
        setSession(session)
        setUser(session?.user ?? null)
      } catch (error) {
        console.error('Error initializing auth:', error)
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      console.log('Auth state changed:', _event, session?.user?.email)
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signIn = async (email: string, password: string) => {
    try {
      const result = await supabase.auth.signInWithPassword({ 
        email, 
        password 
      })
      
      if (result.error) {
        console.error('Sign in error:', result.error)
      } else {
        console.log('Sign in successful:', result.data.user?.email)
      }
      
      return { error: result.error }
    } catch (error) {
      console.error('Sign in exception:', error)
      return { error }
    }
  }

  const signUp = async (email: string, password: string) => {
    try {
      const result = await supabase.auth.signUp({ 
        email, 
        password 
      })
      
      if (result.error) {
        console.error('Sign up error:', result.error)
      } else {
        console.log('Sign up successful:', result.data.user?.email)
      }
      
      return { error: result.error }
    } catch (error) {
      console.error('Sign up exception:', error)
      return { error }
    }
  }

  const signOut = async () => {
    try {
      const result = await supabase.auth.signOut()
      
      if (result.error) {
        console.error('Sign out error:', result.error)
      } else {
        console.log('Sign out successful')
      }
      
      return { error: result.error }
    } catch (error) {
      console.error('Sign out exception:', error)
      return { error }
    }
  }

  const getToken = async (): Promise<string | null> => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession()
      
      if (error) {
        console.error('Error getting token:', error)
        return null
      }
      
      return session?.access_token ?? null
    } catch (error) {
      console.error('Error getting token:', error)
      return null
    }
  }

  return {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    getToken
  }
}
