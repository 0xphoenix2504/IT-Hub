import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { homeFor } from "../api";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Frame, Notice, PrimaryButton } from "../components";

export function LoginPage() {
  const { ready, me, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!ready) {
    return (
      <Frame>
        <p className="p-10 text-sm text-muted">Loading IT Hub.</p>
      </Frame>
    );
  }
  if (me) return <Navigate to={homeFor(me.roles)} replace />;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Frame>
      <div className="grid min-h-[70vh] place-items-center px-4 py-16">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-[28px] border border-white/10 bg-card p-8">
          <div className="mb-8 flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-full bg-lime font-bold text-ink">IT</span>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">IT Hub</h1>
              <p className="text-sm text-muted">IT team and executives</p>
            </div>
          </div>
          <div className="space-y-4">
            {error ? <Notice>{error}</Notice> : null}
            <label className="block text-sm">
              Username
              <input
                className="mt-2 w-full rounded-2xl border border-white/10 bg-elevated px-4 py-3 outline-none"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              Password
              <input
                type="password"
                className="mt-2 w-full rounded-2xl border border-white/10 bg-elevated px-4 py-3 outline-none"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <PrimaryButton type="submit" disabled={busy}>
              {busy ? "Signing in" : "Sign in"}
            </PrimaryButton>
          </div>
        </form>
      </div>
    </Frame>
  );
}
