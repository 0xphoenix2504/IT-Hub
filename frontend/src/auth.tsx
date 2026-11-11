import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError } from "./api";
import type { Me } from "./types";

type AuthState = {
  ready: boolean;
  me: Me | null;
  error: string;
  refresh: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setMe(await api<Me>("/api/auth/me"));
      setError("");
    } catch (caught) {
      setMe(null);
      if (caught instanceof ApiError && (caught.status === 401 || caught.status === 403)) setError("");
      else setError(caught instanceof Error ? caught.message : "Could not reach the hub.");
    } finally {
      setReady(true);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      ready,
      me,
      error,
      refresh,
      login: async (username, password) => {
        setMe(await api<Me>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }));
        setError("");
      },
      logout: async () => {
        await api("/api/auth/logout", { method: "POST" });
        setMe(null);
      },
    }),
    [ready, me, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing");
  return value;
}
