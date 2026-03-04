import { createContext, useContext, useState, useEffect } from "react"
import type { UserInfo } from "@/types"
import { googleLogin, getMe } from "@/api/auth"
import { clearToken, getToken } from "@/api/client"

interface AuthContextType {
  user: UserInfo | null
  token: string | null
  loading: boolean
  login: (credential: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

// Wrap the app with this in App.tsx
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [token, setTokenState] = useState<string | null>(getToken())
  const [loading, setLoading] = useState(true)

  // On mount: if token exists in localStorage, validate it
  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => {
        // Token expired or invalid — clean up
        clearToken()
        setTokenState(null)
      })
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (credential: string) => {
    const data = await googleLogin(credential)
    // googleLogin already calls setToken(localStorage) in api/auth.ts
    setTokenState(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    clearToken()
    setTokenState(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// The hook, we use this in any component needs it
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
