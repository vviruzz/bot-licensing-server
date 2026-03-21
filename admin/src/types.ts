export type AppMode = 'off' | 'monitor' | 'enforce'
export type LicenseStatus = 'active' | 'blocked' | 'revoked' | 'expired' | 'suspicious'
export type BotStatus = 'online' | 'offline' | 'stale' | 'paused' | 'blocked' | 'stopping' | 'closing_positions'

export type ProductDimensions = {
  product_code: string
  bot_family: string
  strategy_code: string
}

export type LicenseSummary = ProductDimensions & {
  license_key: string
  status: LicenseStatus
  mode: AppMode
}

export type BotInstanceSummary = ProductDimensions & {
  bot_instance_id: string
  license_key: string
  status: BotStatus
  server_effective_mode: AppMode
}
