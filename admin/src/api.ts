import type { BotInstanceSummary, LicenseSummary } from './types'

export async function fetchLicenses(): Promise<LicenseSummary[]> {
  return [
    {
      license_key: 'TODO-LICENSE',
      product_code: 'grid',
      bot_family: 'grid',
      strategy_code: 'grid_v1',
      status: 'active',
      mode: 'monitor',
    },
  ]
}

export async function fetchBotInstances(): Promise<BotInstanceSummary[]> {
  return [
    {
      bot_instance_id: 'TODO-BOT-INSTANCE',
      license_key: 'TODO-LICENSE',
      product_code: 'grid',
      bot_family: 'grid',
      strategy_code: 'grid_v1',
      status: 'offline',
      server_effective_mode: 'monitor',
    },
  ]
}
