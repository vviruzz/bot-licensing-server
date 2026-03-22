export type AdminUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type AdminLoginRequest = {
  email: string;
  password: string;
};

export type AdminLoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AdminUser;
};

export type LicenseItem = {
  license_key: string;
  status: string;
  effective_mode: string;
  product_code: string;
  bot_family: string;
  strategy_code: string;
  owner_label?: string | null;
  suspicious_flag: boolean;
  expires_at?: string | null;
  bot_count: number;
};

export type BotItem = {
  bot_instance_id: string;
  license_key?: string | null;
  product_code: string;
  bot_family: string;
  strategy_code: string;
  status: string;
  connectivity_status: string;
  machine_fingerprint: string;
  hostname?: string | null;
  bot_version?: string | null;
  protocol_version: number;
  platform?: string | null;
  is_authorized: boolean;
  authorized_until?: string | null;
  last_seen_at?: string | null;
  last_state_sync_at?: string | null;
};

export type BotDetail = BotItem & {
  latest_state?: Record<string, unknown> | null;
  recent_commands: Array<Record<string, unknown>>;
};

export type AlertItem = {
  id: number;
  alert_type: string;
  severity: string;
  status: string;
  license_id?: number | null;
  bot_instance_id?: string | null;
  session_id?: string | null;
  summary: string;
  details?: unknown;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at?: string | null;
};

export type AdminCommandRequest = {
  bot_instance_id: string;
  reason?: string;
};

export type BlockLicenseRequest = {
  license_key: string;
  reason?: string;
};

export type AdminCommandResponse = {
  ok: boolean;
  status: string;
  command_id?: string | null;
  command_type?: string | null;
};

export type SessionState = {
  token: string;
  user: AdminUser;
  expiresAt: number;
};
