import { useEffect, useMemo, useState } from "react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

import {
  ApiError,
  blockLicense,
  closePositions,
  fetchAlerts,
  fetchBotDetail,
  fetchBots,
  fetchLicenses,
  loginAdmin,
  noopBot,
  pauseBot,
  recheckLicenseBot,
  resumeBot,
  stopBot,
} from "./api";
import type {
  AdminUser,
  AlertItem,
  BotDetail,
  BotItem,
  LicenseItem,
  SessionState,
} from "./types";

const SESSION_STORAGE_KEY = "admin-session";

type ViewName = "licenses" | "bots" | "bot-detail" | "alerts";

const viewLabels: Record<Exclude<ViewName, "bot-detail">, string> = {
  licenses: "Licenses",
  bots: "Bots",
  alerts: "Alerts",
};

function readStoredSession(): SessionState | null {
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as SessionState;
    if (!parsed.token || !parsed.user || !parsed.expiresAt) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveSession(session: SessionState | null) {
  if (session) {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    return;
  }

  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

function formatDate(value?: string | null) {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function formatText(value?: string | number | boolean | null) {
  if (value === undefined || value === null || value === "") {
    return "—";
  }
  return String(value);
}

function statusTone(status: string) {
  const normalized = status.toLowerCase();

  if (["active", "online", "completed", "open", "authorized", "ok", "issued", "monitor"].includes(normalized)) {
    return "#d1fae5";
  }
  if (["warning", "paused", "stale", "queued", "acknowledged", "resolved"].includes(normalized)) {
    return "#fef3c7";
  }
  if (["blocked", "invalid", "expired", "offline", "failed", "critical", "stopping", "closing_positions"].includes(normalized)) {
    return "#fee2e2";
  }
  return "#e5e7eb";
}

function Badge({ value }: { value: string | boolean }) {
  const label = typeof value === "boolean" ? (value ? "yes" : "no") : value;

  return (
    <span
      style={{
        background: statusTone(String(label)),
        borderRadius: 999,
        display: "inline-block",
        fontSize: 12,
        fontWeight: 600,
        padding: "0.25rem 0.6rem",
        textTransform: "capitalize",
      }}
    >
      {String(label).split("_").join(" ")}
    </span>
  );
}

function SectionCard(props: { title: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
        padding: "1rem",
      }}
    >
      <div
        style={{
          alignItems: "center",
          display: "flex",
          gap: "0.75rem",
          justifyContent: "space-between",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", margin: 0 }}>{props.title}</h2>
        {props.actions}
      </div>
      {props.children}
    </section>
  );
}

function DataTable(props: { headers: string[]; children: ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {props.headers.map((header) => (
              <th
                key={header}
                style={{
                  borderBottom: "1px solid #e5e7eb",
                  color: "#4b5563",
                  fontSize: 12,
                  padding: "0.75rem",
                  textAlign: "left",
                  textTransform: "uppercase",
                }}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{props.children}</tbody>
      </table>
    </div>
  );
}

function TableCell(props: { children: ReactNode }) {
  return <td style={{ borderBottom: "1px solid #f3f4f6", padding: "0.75rem", verticalAlign: "top" }}>{props.children}</td>;
}

function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        background: "#ffffff",
        border: "1px solid #d1d5db",
        borderRadius: 8,
        fontSize: 14,
        minWidth: 0,
        padding: "0.65rem 0.75rem",
        ...(props.style ?? {}),
      }}
    />
  );
}

function SelectInput(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      style={{
        background: "#ffffff",
        border: "1px solid #d1d5db",
        borderRadius: 8,
        fontSize: 14,
        padding: "0.65rem 0.75rem",
        ...(props.style ?? {}),
      }}
    />
  );
}

function ActionButton(
  props: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: "primary" | "secondary" | "danger" },
) {
  const tone = props.tone ?? "secondary";
  const palette =
    tone === "primary"
      ? { background: "#2563eb", color: "#ffffff", border: "#2563eb" }
      : tone === "danger"
        ? { background: "#b91c1c", color: "#ffffff", border: "#b91c1c" }
        : { background: "#ffffff", color: "#111827", border: "#d1d5db" };

  return (
    <button
      {...props}
      style={{
        background: palette.background,
        border: `1px solid ${palette.border}`,
        borderRadius: 8,
        color: palette.color,
        cursor: props.disabled ? "not-allowed" : "pointer",
        fontSize: 14,
        fontWeight: 600,
        opacity: props.disabled ? 0.6 : 1,
        padding: "0.6rem 0.85rem",
        ...(props.style ?? {}),
      }}
    />
  );
}

function LoginScreen(props: { busy: boolean; error: string; onSubmit: (email: string, password: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <main
      style={{
        alignItems: "center",
        background: "#f3f4f6",
        display: "flex",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "1.5rem",
      }}
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          props.onSubmit(email, password);
        }}
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
          display: "grid",
          gap: "1rem",
          maxWidth: 380,
          padding: "1.5rem",
          width: "100%",
        }}
      >
        <div>
          <h1 style={{ margin: "0 0 0.35rem" }}>Admin login</h1>
          <p style={{ color: "#4b5563", margin: 0 }}>Sign in with an existing admin account to manage licenses, bots, and alerts.</p>
        </div>
        <label style={{ display: "grid", gap: "0.4rem" }}>
          <span>Email</span>
          <TextInput autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "0.4rem" }}>
          <span>Password</span>
          <TextInput autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {props.error ? <div style={{ color: "#b91c1c", fontSize: 14 }}>{props.error}</div> : null}
        <ActionButton tone="primary" type="submit" disabled={props.busy}>
          {props.busy ? "Signing in..." : "Sign in"}
        </ActionButton>
      </form>
    </main>
  );
}

function AppShell(props: {
  user: AdminUser;
  currentView: ViewName;
  onNavigate: (view: Exclude<ViewName, "bot-detail">) => void;
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <div style={{ background: "#f3f4f6", minHeight: "100vh" }}>
      <header
        style={{
          background: "#111827",
          color: "#ffffff",
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
          justifyContent: "space-between",
          padding: "1rem 1.5rem",
        }}
      >
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Bot Licensing Admin</div>
          <div style={{ color: "#d1d5db", fontSize: 14 }}>{props.user.full_name} · {props.user.role}</div>
        </div>
        <nav style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
          {(Object.keys(viewLabels) as Array<Exclude<ViewName, "bot-detail">>).map((view) => (
            <button
              key={view}
              onClick={() => props.onNavigate(view)}
              style={{
                background: props.currentView === view ? "#2563eb" : "transparent",
                border: "1px solid rgba(255,255,255,0.2)",
                borderRadius: 999,
                color: "#ffffff",
                cursor: "pointer",
                padding: "0.5rem 0.85rem",
              }}
            >
              {viewLabels[view]}
            </button>
          ))}
          <ActionButton onClick={props.onLogout}>Logout</ActionButton>
        </nav>
      </header>
      <main style={{ margin: "0 auto", maxWidth: 1440, padding: "1.5rem" }}>{props.children}</main>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState<SessionState | null>(() => readStoredSession());
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [currentView, setCurrentView] = useState<ViewName>("licenses");
  const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
  const [licenses, setLicenses] = useState<LicenseItem[]>([]);
  const [bots, setBots] = useState<BotItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [botDetail, setBotDetail] = useState<BotDetail | null>(null);
  const [busyState, setBusyState] = useState<Record<string, boolean>>({});
  const [errorState, setErrorState] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");
  const [licenseSearch, setLicenseSearch] = useState("");
  const [licenseStatusFilter, setLicenseStatusFilter] = useState("");
  const [licenseProductFilter, setLicenseProductFilter] = useState("");
  const [botSearch, setBotSearch] = useState("");
  const [botStatusFilter, setBotStatusFilter] = useState("");
  const [botProductFilter, setBotProductFilter] = useState("");
  const [alertSearch, setAlertSearch] = useState("");
  const [alertStatusFilter, setAlertStatusFilter] = useState("");

  const token = session?.token ?? "";

  useEffect(() => {
    if (!session) {
      return;
    }

    if (Date.now() > session.expiresAt) {
      setSession(null);
      saveSession(null);
      setAuthError("Your session expired. Please sign in again.");
    }
  }, [session]);

  async function loadLicenses(activeToken = token) {
    setBusyState((current) => ({ ...current, licenses: true }));
    setErrorState((current) => ({ ...current, licenses: "" }));
    try {
      setLicenses(await fetchLicenses(activeToken));
    } catch (error) {
      handleApiError("licenses", error);
    } finally {
      setBusyState((current) => ({ ...current, licenses: false }));
    }
  }

  async function loadBots(activeToken = token) {
    setBusyState((current) => ({ ...current, bots: true }));
    setErrorState((current) => ({ ...current, bots: "" }));
    try {
      setBots(await fetchBots(activeToken));
    } catch (error) {
      handleApiError("bots", error);
    } finally {
      setBusyState((current) => ({ ...current, bots: false }));
    }
  }

  async function loadAlerts(activeToken = token) {
    setBusyState((current) => ({ ...current, alerts: true }));
    setErrorState((current) => ({ ...current, alerts: "" }));
    try {
      setAlerts(await fetchAlerts(activeToken));
    } catch (error) {
      handleApiError("alerts", error);
    } finally {
      setBusyState((current) => ({ ...current, alerts: false }));
    }
  }

  async function loadBotDetail(botId: string, activeToken = token) {
    setBusyState((current) => ({ ...current, botDetail: true }));
    setErrorState((current) => ({ ...current, botDetail: "" }));
    try {
      setBotDetail(await fetchBotDetail(activeToken, botId));
    } catch (error) {
      handleApiError("botDetail", error);
    } finally {
      setBusyState((current) => ({ ...current, botDetail: false }));
    }
  }

  function handleApiError(scope: string, error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      setSession(null);
      saveSession(null);
      setAuthError("Your session is no longer valid. Please sign in again.");
      return;
    }

    const message = error instanceof Error ? error.message : "Request failed";
    setErrorState((current) => ({ ...current, [scope]: message }));
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    void Promise.all([loadLicenses(token), loadBots(token), loadAlerts(token)]);
  }, [token]);

  useEffect(() => {
    if (!token || currentView !== "bot-detail" || !selectedBotId) {
      return;
    }

    void loadBotDetail(selectedBotId, token);
  }, [currentView, selectedBotId, token]);

  const licenseStatuses = useMemo(() => Array.from(new Set(licenses.map((item) => item.status))).sort(), [licenses]);
  const licenseProducts = useMemo(
    () => Array.from(new Set(licenses.flatMap((item) => [item.product_code, item.bot_family, item.strategy_code]))).filter(Boolean).sort(),
    [licenses],
  );
  const botStatuses = useMemo(() => Array.from(new Set(bots.map((item) => item.status))).sort(), [bots]);
  const botProducts = useMemo(
    () => Array.from(new Set(bots.flatMap((item) => [item.product_code, item.bot_family, item.strategy_code]))).filter(Boolean).sort(),
    [bots],
  );
  const alertStatuses = useMemo(() => Array.from(new Set(alerts.map((item) => item.status))).sort(), [alerts]);

  const filteredLicenses = useMemo(() => {
    const query = licenseSearch.toLowerCase().trim();
    return licenses.filter((item) => {
      const matchesQuery =
        !query ||
        item.license_key.toLowerCase().includes(query) ||
        item.product_code.toLowerCase().includes(query) ||
        item.bot_family.toLowerCase().includes(query) ||
        item.strategy_code.toLowerCase().includes(query);
      const matchesStatus = !licenseStatusFilter || item.status === licenseStatusFilter;
      const matchesProduct =
        !licenseProductFilter ||
        [item.product_code, item.bot_family, item.strategy_code].includes(licenseProductFilter);
      return matchesQuery && matchesStatus && matchesProduct;
    });
  }, [licenseProductFilter, licenseSearch, licenseStatusFilter, licenses]);

  const filteredBots = useMemo(() => {
    const query = botSearch.toLowerCase().trim();
    return bots.filter((item) => {
      const matchesQuery =
        !query ||
        item.bot_instance_id.toLowerCase().includes(query) ||
        (item.license_key ?? "").toLowerCase().includes(query) ||
        item.product_code.toLowerCase().includes(query) ||
        item.bot_family.toLowerCase().includes(query) ||
        item.strategy_code.toLowerCase().includes(query);
      const matchesStatus = !botStatusFilter || item.status === botStatusFilter || item.connectivity_status === botStatusFilter;
      const matchesProduct = !botProductFilter || [item.product_code, item.bot_family, item.strategy_code].includes(botProductFilter);
      return matchesQuery && matchesStatus && matchesProduct;
    });
  }, [botProductFilter, botSearch, botStatusFilter, bots]);

  const filteredAlerts = useMemo(() => {
    const query = alertSearch.toLowerCase().trim();
    return alerts.filter((item) => {
      const haystack = [item.summary, item.alert_type, item.bot_instance_id ?? "", item.session_id ?? "", String(item.license_id ?? "")]
        .join(" ")
        .toLowerCase();
      const matchesQuery = !query || haystack.includes(query);
      const matchesStatus = !alertStatusFilter || item.status === alertStatusFilter || item.severity === alertStatusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [alertSearch, alertStatusFilter, alerts]);

  async function handleLogin(email: string, password: string) {
    setAuthBusy(true);
    setAuthError("");

    try {
      const response = await loginAdmin({ email, password });
      const nextSession: SessionState = {
        token: response.access_token,
        user: response.user,
        expiresAt: Date.now() + response.expires_in * 1000,
      };
      setSession(nextSession);
      saveSession(nextSession);
      setCurrentView("licenses");
      setNotice("Signed in successfully.");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Login failed");
    } finally {
      setAuthBusy(false);
    }
  }

  function handleLogout() {
    setSession(null);
    setBotDetail(null);
    saveSession(null);
    setCurrentView("licenses");
    setSelectedBotId(null);
    setNotice("You have been logged out.");
  }

  async function handleBlockLicense(licenseKey: string) {
    const reason = window.prompt(`Optional reason for blocking ${licenseKey}:`) ?? "";
    setNotice("");
    try {
      const response = await blockLicense(token, { license_key: licenseKey, reason: reason || undefined });
      setNotice(`License ${licenseKey} updated: ${response.status}.`);
      await Promise.all([loadLicenses(), loadAlerts()]);
    } catch (error) {
      handleApiError("licenses", error);
    }
  }

  async function handleBotCommand(botId: string, action: "pause" | "resume" | "stop" | "close" | "noop" | "recheck-license") {
    const reason = window.prompt(`Optional reason for ${action} on ${botId}:`) ?? "";
    setNotice("");

    try {
      const response =
        action === "pause"
          ? await pauseBot(token, { bot_instance_id: botId, reason: reason || undefined })
          : action === "resume"
            ? await resumeBot(token, { bot_instance_id: botId, reason: reason || undefined })
            : action === "stop"
              ? await stopBot(token, { bot_instance_id: botId, reason: reason || undefined })
              : action === "noop"
                ? await noopBot(token, { bot_instance_id: botId, reason: reason || undefined })
                : action === "recheck-license"
                  ? await recheckLicenseBot(token, { bot_instance_id: botId, reason: reason || undefined })
                  : await closePositions(token, { bot_instance_id: botId, reason: reason || undefined });
      setNotice(`Command queued for ${botId}: ${response.status}.`);
      await Promise.all([loadBots(), loadAlerts(), selectedBotId === botId ? loadBotDetail(botId) : Promise.resolve()]);
    } catch (error) {
      handleApiError(selectedBotId === botId ? "botDetail" : "bots", error);
    }
  }

  if (!session) {
    return <LoginScreen busy={authBusy} error={authError} onSubmit={handleLogin} />;
  }

  return (
    <AppShell
      user={session.user}
      currentView={currentView}
      onNavigate={(view) => {
        setCurrentView(view);
        setSelectedBotId(null);
        setBotDetail(null);
      }}
      onLogout={handleLogout}
    >
      {notice ? (
        <div style={{ background: "#dbeafe", border: "1px solid #93c5fd", borderRadius: 10, marginBottom: "1rem", padding: "0.9rem 1rem" }}>
          {notice}
        </div>
      ) : null}

      {currentView === "licenses" ? (
        <SectionCard
          title="Licenses"
          actions={<ActionButton onClick={() => void loadLicenses()} disabled={busyState.licenses}>Refresh</ActionButton>}
        >
          <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginBottom: "1rem" }}>
            <TextInput placeholder="Search by license key / product / family / strategy" value={licenseSearch} onChange={(event) => setLicenseSearch(event.target.value)} />
            <SelectInput value={licenseStatusFilter} onChange={(event) => setLicenseStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {licenseStatuses.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </SelectInput>
            <SelectInput value={licenseProductFilter} onChange={(event) => setLicenseProductFilter(event.target.value)}>
              <option value="">All products / families / strategies</option>
              {licenseProducts.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </SelectInput>
          </div>
          {errorState.licenses ? <div style={{ color: "#b91c1c", marginBottom: "0.75rem" }}>{errorState.licenses}</div> : null}
          <DataTable headers={["License key", "Status", "Mode", "Product", "Owner", "Expires", "Bots", "Actions"]}>
            {filteredLicenses.map((item) => (
              <tr key={item.license_key}>
                <TableCell>
                  <strong>{item.license_key}</strong>
                  <div style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>
                    {item.bot_family} / {item.strategy_code}
                  </div>
                </TableCell>
                <TableCell>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <Badge value={item.status} />
                    {item.suspicious_flag ? <Badge value="suspicious" /> : null}
                  </div>
                </TableCell>
                <TableCell><Badge value={item.effective_mode} /></TableCell>
                <TableCell>{item.product_code}</TableCell>
                <TableCell>{formatText(item.owner_label)}</TableCell>
                <TableCell>{formatDate(item.expires_at)}</TableCell>
                <TableCell>{item.bot_count}</TableCell>
                <TableCell>
                  <ActionButton tone="danger" disabled={item.status === "blocked"} onClick={() => void handleBlockLicense(item.license_key)}>
                    Block
                  </ActionButton>
                </TableCell>
              </tr>
            ))}
          </DataTable>
        </SectionCard>
      ) : null}

      {currentView === "bots" ? (
        <SectionCard title="Bots" actions={<ActionButton onClick={() => void loadBots()} disabled={busyState.bots}>Refresh</ActionButton>}>
          <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginBottom: "1rem" }}>
            <TextInput placeholder="Search by bot id / license / product / family / strategy" value={botSearch} onChange={(event) => setBotSearch(event.target.value)} />
            <SelectInput value={botStatusFilter} onChange={(event) => setBotStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {Array.from(new Set([...botStatuses, ...bots.map((item) => item.connectivity_status)])).sort().map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </SelectInput>
            <SelectInput value={botProductFilter} onChange={(event) => setBotProductFilter(event.target.value)}>
              <option value="">All products / families / strategies</option>
              {botProducts.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </SelectInput>
          </div>
          {errorState.bots ? <div style={{ color: "#b91c1c", marginBottom: "0.75rem" }}>{errorState.bots}</div> : null}
          <DataTable headers={["Bot instance", "License", "Status", "Connectivity", "Product", "Machine", "Last seen", "Actions"]}>
            {filteredBots.map((item) => (
              <tr key={item.bot_instance_id}>
                <TableCell>
                  <strong>{item.bot_instance_id}</strong>
                  <div style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>{formatText(item.hostname)} · {formatText(item.bot_version)}</div>
                </TableCell>
                <TableCell>{formatText(item.license_key)}</TableCell>
                <TableCell><Badge value={item.status} /></TableCell>
                <TableCell><Badge value={item.connectivity_status} /></TableCell>
                <TableCell>
                  {item.product_code}
                  <div style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>{item.bot_family} / {item.strategy_code}</div>
                </TableCell>
                <TableCell><span style={{ wordBreak: "break-word" }}>{item.machine_fingerprint}</span></TableCell>
                <TableCell>{formatDate(item.last_seen_at)}</TableCell>
                <TableCell>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <ActionButton onClick={() => { setSelectedBotId(item.bot_instance_id); setCurrentView("bot-detail"); }}>Details</ActionButton>
                    <ActionButton onClick={() => void handleBotCommand(item.bot_instance_id, "pause")}>Pause</ActionButton>
                    <ActionButton onClick={() => void handleBotCommand(item.bot_instance_id, "resume")}>Resume</ActionButton>
                    <ActionButton onClick={() => void handleBotCommand(item.bot_instance_id, "noop")}>No-op</ActionButton>
                    <ActionButton onClick={() => void handleBotCommand(item.bot_instance_id, "recheck-license")}>Recheck license</ActionButton>
                    <ActionButton tone="danger" onClick={() => void handleBotCommand(item.bot_instance_id, "stop")}>Stop</ActionButton>
                    <ActionButton tone="danger" onClick={() => void handleBotCommand(item.bot_instance_id, "close")}>Close positions</ActionButton>
                  </div>
                </TableCell>
              </tr>
            ))}
          </DataTable>
        </SectionCard>
      ) : null}

      {currentView === "bot-detail" ? (
        <div style={{ display: "grid", gap: "1rem" }}>
          <SectionCard
            title={`Bot details${selectedBotId ? ` · ${selectedBotId}` : ""}`}
            actions={
              <div style={{ display: "flex", gap: 8 }}>
                <ActionButton onClick={() => setCurrentView("bots")}>Back to bots</ActionButton>
                {selectedBotId ? <ActionButton onClick={() => void loadBotDetail(selectedBotId)} disabled={busyState.botDetail}>Refresh</ActionButton> : null}
              </div>
            }
          >
            {errorState.botDetail ? <div style={{ color: "#b91c1c", marginBottom: "0.75rem" }}>{errorState.botDetail}</div> : null}
            {!botDetail ? (
              <div style={{ color: "#6b7280" }}>{busyState.botDetail ? "Loading bot details..." : "Select a bot from the list to view details."}</div>
            ) : (
              <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
                <div style={{ background: "#f9fafb", borderRadius: 10, padding: "1rem" }}>
                  <h3 style={{ marginTop: 0 }}>Overview</h3>
                  <dl style={{ display: "grid", gap: "0.65rem", margin: 0 }}>
                    <div><dt>Status</dt><dd style={{ margin: 0 }}><Badge value={botDetail.status} /></dd></div>
                    <div><dt>Connectivity</dt><dd style={{ margin: 0 }}><Badge value={botDetail.connectivity_status} /></dd></div>
                    <div><dt>Authorized</dt><dd style={{ margin: 0 }}><Badge value={botDetail.is_authorized} /></dd></div>
                    <div><dt>License</dt><dd style={{ margin: 0 }}>{formatText(botDetail.license_key)}</dd></div>
                    <div><dt>Authorized until</dt><dd style={{ margin: 0 }}>{formatDate(botDetail.authorized_until)}</dd></div>
                    <div><dt>Last seen</dt><dd style={{ margin: 0 }}>{formatDate(botDetail.last_seen_at)}</dd></div>
                    <div><dt>Last state sync</dt><dd style={{ margin: 0 }}>{formatDate(botDetail.last_state_sync_at)}</dd></div>
                  </dl>
                </div>
                <div style={{ background: "#f9fafb", borderRadius: 10, padding: "1rem" }}>
                  <h3 style={{ marginTop: 0 }}>Identity</h3>
                  <dl style={{ display: "grid", gap: "0.65rem", margin: 0 }}>
                    <div><dt>Bot instance ID</dt><dd style={{ margin: 0 }}>{botDetail.bot_instance_id}</dd></div>
                    <div><dt>Machine fingerprint</dt><dd style={{ margin: 0, wordBreak: "break-word" }}>{botDetail.machine_fingerprint}</dd></div>
                    <div><dt>Hostname</dt><dd style={{ margin: 0 }}>{formatText(botDetail.hostname)}</dd></div>
                    <div><dt>Version</dt><dd style={{ margin: 0 }}>{formatText(botDetail.bot_version)}</dd></div>
                    <div><dt>Platform</dt><dd style={{ margin: 0 }}>{formatText(botDetail.platform)}</dd></div>
                    <div><dt>Protocol version</dt><dd style={{ margin: 0 }}>{botDetail.protocol_version}</dd></div>
                    <div><dt>Product / family / strategy</dt><dd style={{ margin: 0 }}>{botDetail.product_code} / {botDetail.bot_family} / {botDetail.strategy_code}</dd></div>
                  </dl>
                </div>
              </div>
            )}
          </SectionCard>

          {botDetail ? (
            <>
              <SectionCard title="Commands">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <ActionButton onClick={() => void handleBotCommand(botDetail.bot_instance_id, "pause")}>Pause</ActionButton>
                  <ActionButton onClick={() => void handleBotCommand(botDetail.bot_instance_id, "resume")}>Resume</ActionButton>
                  <ActionButton onClick={() => void handleBotCommand(botDetail.bot_instance_id, "noop")}>No-op</ActionButton>
                  <ActionButton onClick={() => void handleBotCommand(botDetail.bot_instance_id, "recheck-license")}>Recheck license</ActionButton>
                  <ActionButton tone="danger" onClick={() => void handleBotCommand(botDetail.bot_instance_id, "stop")}>Stop</ActionButton>
                  <ActionButton tone="danger" onClick={() => void handleBotCommand(botDetail.bot_instance_id, "close")}>Close positions</ActionButton>
                </div>
              </SectionCard>
              <SectionCard title="Latest state payload">
                <pre style={{ background: "#111827", borderRadius: 10, color: "#f9fafb", margin: 0, overflowX: "auto", padding: "1rem" }}>
                  {JSON.stringify(botDetail.latest_state ?? {}, null, 2)}
                </pre>
              </SectionCard>
              <SectionCard title="Recent commands">
                <pre style={{ background: "#111827", borderRadius: 10, color: "#f9fafb", margin: 0, overflowX: "auto", padding: "1rem" }}>
                  {JSON.stringify(botDetail.recent_commands ?? [], null, 2)}
                </pre>
              </SectionCard>
            </>
          ) : null}
        </div>
      ) : null}

      {currentView === "alerts" ? (
        <SectionCard title="Alerts" actions={<ActionButton onClick={() => void loadAlerts()} disabled={busyState.alerts}>Refresh</ActionButton>}>
          <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: "1rem" }}>
            <TextInput placeholder="Search by summary / bot / license" value={alertSearch} onChange={(event) => setAlertSearch(event.target.value)} />
            <SelectInput value={alertStatusFilter} onChange={(event) => setAlertStatusFilter(event.target.value)}>
              <option value="">All statuses / severities</option>
              {Array.from(new Set([...alertStatuses, ...alerts.map((item) => item.severity)])).sort().map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </SelectInput>
          </div>
          {errorState.alerts ? <div style={{ color: "#b91c1c", marginBottom: "0.75rem" }}>{errorState.alerts}</div> : null}
          <DataTable headers={["Alert", "Severity", "Status", "Bot", "License", "First seen", "Last seen"]}>
            {filteredAlerts.map((item) => (
              <tr key={item.id}>
                <TableCell>
                  <strong>{item.summary}</strong>
                  <div style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>{item.alert_type}</div>
                </TableCell>
                <TableCell><Badge value={item.severity} /></TableCell>
                <TableCell><Badge value={item.status} /></TableCell>
                <TableCell>{formatText(item.bot_instance_id)}</TableCell>
                <TableCell>{formatText(item.license_id)}</TableCell>
                <TableCell>{formatDate(item.first_seen_at)}</TableCell>
                <TableCell>
                  {formatDate(item.last_seen_at)}
                  {item.details ? (
                    <details style={{ marginTop: 8 }}>
                      <summary>Details</summary>
                      <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(item.details, null, 2)}</pre>
                    </details>
                  ) : null}
                </TableCell>
              </tr>
            ))}
          </DataTable>
        </SectionCard>
      ) : null}
    </AppShell>
  );
}
