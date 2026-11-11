import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { homeFor } from "./api";
import { useAuth } from "./auth";
import { Frame, Notice } from "./components";
import { ExecutivePage } from "./pages/Executive";
import { LoginPage } from "./pages/Login";
import { SettingsPage } from "./pages/Settings";
import { TechnicalPage } from "./pages/Technical";
import type { Role } from "./types";

function Guard({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { ready, me, error } = useAuth();
  if (!ready) {
    return (
      <Frame>
        <p className="p-10 text-sm text-muted">Loading IT Hub.</p>
      </Frame>
    );
  }
  if (error && !me) {
    return (
      <Frame>
        <div className="p-10">
          <Notice>{error}</Notice>
        </div>
      </Frame>
    );
  }
  if (!me) return <Navigate to="/login" replace />;
  const allowed = me.roles.includes("it_manager") || roles.some((role) => me.roles.includes(role));
  if (!allowed) return <Navigate to={homeFor(me.roles)} replace />;
  return children;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Guard roles={["executive"]}><ExecutivePage /></Guard>} />
      <Route path="/servers" element={<Guard roles={["system_admin"]}><TechnicalPage title="Servers" path="servers" noun="Servers" /></Guard>} />
      <Route path="/network" element={<Guard roles={["network_admin"]}><TechnicalPage title="Network" path="network" noun="Network devices" /></Guard>} />
      <Route path="/helpdesk" element={<Guard roles={["helpdesk"]}><TechnicalPage title="Helpdesk" path="helpdesk" noun="End-user devices" /></Guard>} />
      <Route path="/settings" element={<Guard roles={["it_manager"]}><SettingsPage /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
