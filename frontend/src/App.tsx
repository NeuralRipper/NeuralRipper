import { useState } from "react"
import { GoogleOAuthProvider } from "@react-oauth/google"
import { AuthProvider } from "@/hooks/useAuth"
import Playground from "@/components/Playground"
import Portfolio from "@/components/portfolio/Portfolio"

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

const TABS = ["About", "Evaluation"] as const
type Tab = typeof TABS[number]

export default function App() {
  const [tab, setTab] = useState<Tab>("About")

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Title bar with tabs */}
      <div className="border-b border-border bg-card px-4 py-3 flex items-center gap-6">
        <span className="text-lg font-bold text-cyan-400">NEURAL RIPPER</span>
        <div className="flex gap-1">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 text-sm cursor-pointer ${
                tab === t
                  ? "text-cyan-400 border-b-2 border-cyan-400"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      
      {tab === "Evaluation" && (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
          <AuthProvider>
            <Playground />
          </AuthProvider>
        </GoogleOAuthProvider>
      )}
      {tab === "About" && <Portfolio />}
    </div>
  )
}
