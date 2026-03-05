import { GoogleOAuthProvider } from "@react-oauth/google"
import { AuthProvider } from "@/hooks/useAuth"
import Playground from "@/components/Playground"

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <Playground />
      </AuthProvider>
    </GoogleOAuthProvider>
  )
}
