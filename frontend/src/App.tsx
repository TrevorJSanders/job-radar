import { useQuery } from "@tanstack/react-query"
import axios from "axios"

const fetchHealth = async () => {
  const { data } = await axios.get("http://localhost:8000/health")
  return data
}

function App() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  })

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="p-8 bg-white rounded-xl shadow-lg border border-slate-200 max-w-md w-full">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">JobRadar Health Check</h1>
        
        {isLoading && (
          <p className="text-slate-600 animate-pulse">Checking backend status...</p>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium">Backend Unreachable</p>
            <p className="text-red-600 text-sm mt-1">
              Make sure the FastAPI server is running on localhost:8000
            </p>
          </div>
        )}

        {data && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-700 font-medium text-lg">
              Status: <span className="uppercase">{data.status}</span>
            </p>
            <p className="text-green-600 text-sm mt-1">
              Frontend and Backend are connected!
            </p>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-slate-100 text-slate-500 text-xs">
          Built with React + Vite + TypeScript + Tailwind CSS
        </div>
      </div>
    </div>
  )
}

export default App
