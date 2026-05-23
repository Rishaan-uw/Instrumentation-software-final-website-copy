import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { ApiError, api, getToken, setToken } from "../api/client";

interface InfoResponse {
  auth_enabled: boolean;
}

interface AuthContextValue {
  ready: boolean;
  authRequired: boolean;
  hasToken: boolean;
  /** Set when /api/info could not be reached (e.g. backend not running). Not a missing token. */
  backendError: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authRequired, setAuthRequired] = useState(false);
  const [hasToken, setHasToken] = useState(Boolean(getToken()));
  const [ready, setReady] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setReady(false);
    setBackendError(null);
    api
      .get<InfoResponse>("/api/info")
      .then((info) => {
        setAuthRequired(info.auth_enabled);
        setBackendError(null);
        setReady(true);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          setAuthRequired(true);
          setBackendError(null);
        } else {
          setAuthRequired(false);
          const raw = err instanceof Error ? err.message : "Unable to reach the science API.";
          const unreachable =
            raw === "Failed to fetch" ||
            raw === "Load failed" ||
            raw.includes("NetworkError") ||
            raw.includes("ECONNREFUSED");
          setBackendError(
            unreachable
              ? "Cannot reach the API (is the backend running on port 8000?). Refresh after starting it."
              : raw
          );
        }
        setReady(true);
      });
  }, [hasToken]);

  const login = useCallback(async (token: string) => {
    setToken(token);
    try {
      await api.get("/api/health");
      setHasToken(true);
      setError(null);
    } catch (err) {
      setToken("");
      setHasToken(false);
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    setToken("");
    setHasToken(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{ ready, authRequired, hasToken, backendError, login, logout, error }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
