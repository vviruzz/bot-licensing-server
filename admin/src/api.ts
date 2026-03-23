import type {
  AdminCommandRequest,
  AdminCommandResponse,
  AdminLoginRequest,
  AdminLoginResponse,
  AlertItem,
  BlockLicenseRequest,
  BotDetail,
  BotItem,
  LicenseItem,
} from "./types";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

type RequestOptions = {
  method?: "GET" | "POST";
  token?: string;
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || "Request failed";
    }

    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export function loginAdmin(payload: AdminLoginRequest): Promise<AdminLoginResponse> {
  return request<AdminLoginResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function fetchLicenses(token: string): Promise<LicenseItem[]> {
  return request<LicenseItem[]>("/admin/licenses", { token });
}

export function fetchBots(token: string): Promise<BotItem[]> {
  return request<BotItem[]>("/admin/bots", { token });
}

export function fetchBotDetail(token: string, botInstanceId: string): Promise<BotDetail> {
  return request<BotDetail>(`/admin/bots/${encodeURIComponent(botInstanceId)}`, { token });
}

export function fetchAlerts(token: string): Promise<AlertItem[]> {
  return request<AlertItem[]>("/admin/alerts", { token });
}

export function blockLicense(token: string, payload: BlockLicenseRequest): Promise<AdminCommandResponse> {
  return request<AdminCommandResponse>("/admin/license/block", {
    method: "POST",
    token,
    body: payload,
  });
}

function sendBotCommand(
  token: string,
  path: "/admin/bot/pause" | "/admin/bot/resume" | "/admin/bot/stop" | "/admin/bot/close-positions" | "/admin/bot/noop" | "/admin/bot/recheck-license",
  payload: AdminCommandRequest,
): Promise<AdminCommandResponse> {
  return request<AdminCommandResponse>(path, {
    method: "POST",
    token,
    body: payload,
  });
}

export function pauseBot(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/pause", payload);
}

export function resumeBot(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/resume", payload);
}

export function stopBot(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/stop", payload);
}

export function closePositions(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/close-positions", payload);
}

export function noopBot(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/noop", payload);
}

export function recheckLicenseBot(token: string, payload: AdminCommandRequest): Promise<AdminCommandResponse> {
  return sendBotCommand(token, "/admin/bot/recheck-license", payload);
}
