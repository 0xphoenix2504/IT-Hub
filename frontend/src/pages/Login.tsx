import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { homeFor } from "../api";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Frame, Notice, PrimaryButton } from "../components";
import { useI18n } from "../i18n";

export function LoginPage() {
  const { ready, me, login } = useAuth();
  const { t, lang, toggleLang } = useI18n();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!ready) {
    return (
      <Frame>
        <p className="p-10 text-sm text-muted">{t("loading.default")}</p>
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
      setError(caught instanceof ApiError ? caught.message : t("error.could_not_load"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Frame>
      <div className="grid min-h-[70vh] place-items-center px-4 py-16">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-[28px] border border-white/10 bg-card p-8">
          <div className="mb-8 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-lime font-bold text-ink">IT</span>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight">{t("brand.name")}</h1>
                <p className="text-sm text-muted">{t("login.title")}</p>
              </div>
            </div>
            <button
              type="button"
              className="rounded-full border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white/90 hover:bg-white/10 transition"
              onClick={toggleLang}
              title={lang === "en" ? "التبديل إلى العربية" : "Switch to English"}
            >
              {lang === "en" ? "عربي" : "EN"}
            </button>
          </div>
          <p className="mb-6 text-xs leading-5 text-muted">{t("login.subtitle")}</p>
          <div className="space-y-4">
            {error ? <Notice>{error}</Notice> : null}
            <label className="block text-sm">
              {t("login.username")}
              <input
                className="mt-2 w-full rounded-2xl border border-white/10 bg-elevated px-4 py-3 outline-none"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              {t("login.password")}
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
              {busy ? t("login.signing_in") : t("login.button")}
            </PrimaryButton>
          </div>
        </form>
      </div>
    </Frame>
  );
}
