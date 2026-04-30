import { useEffect, useState } from "react"
import { checkHealth } from "@/lib/api"

function App() {
  const [status, setStatus] = useState<string>("connecting...")
  const [isError, setIsError] = useState<boolean>(false)

  useEffect(() => {
    const getStatus = async () => {
      try {
        const data = await checkHealth()
        setStatus(data.status)
        setIsError(false)
      } catch (err) {
        console.error("Health check failed:", err)
        setStatus("error")
        setIsError(true)
      }
    }

    getStatus()
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-white p-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-extrabold tracking-tight">
          JobRadar
        </h1>
        <p className="text-slate-400 text-xl font-medium">
          Loading your applications...
        </p>
        
        <div className="pt-8">
          {status === "connecting..." ? (
            <span className="px-4 py-2 rounded-full bg-slate-800 text-slate-300 text-sm font-semibold animate-pulse border border-slate-700">
              Backend: connecting...
            </span>
          ) : isError ? (
            <span className="px-4 py-2 rounded-full bg-red-900/30 text-red-400 text-sm font-semibold border border-red-900/50">
              Backend: error
            </span>
          ) : (
            <span className="px-4 py-2 rounded-full bg-emerald-900/30 text-emerald-400 text-sm font-semibold border border-emerald-900/50">
              Backend: {status}
            </span>
          )}
        </div>
      </div>

      <div className="absolute bottom-8 text-slate-600 text-xs uppercase tracking-widest font-bold">
        Vite + React + Tailwind v4 + Shadcn
      </div>
    </div>
  )
}

export default App
