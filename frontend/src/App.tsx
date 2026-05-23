import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Sessions from "./pages/Sessions";

export default function App() {
  const { ready, authRequired, hasToken, backendError } = useAuth();

  if (!ready) {
    return (
      <div className="min-h-full flex items-center justify-center text-muted">
        Connecting to rover...
      </div>
    );
  }

  if (backendError) {
    return (
      <div className="min-h-full flex flex-col items-center justify-center gap-4 p-8 text-center max-w-lg mx-auto">
        <p className="mono text-[11px] tracking-wider text-blood uppercase">API unreachable</p>
        <p className="text-muted">{backendError}</p>
        <p className="mono text-[10px] tracking-wider text-ash">
          Dev: <code className="text-bone">uvicorn backend.main:app --reload --port 8000</code>
        </p>
      </div>
    );
  }

  if (authRequired && !hasToken) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sessions" element={<Sessions />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
