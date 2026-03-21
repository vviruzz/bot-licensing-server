import { useEffect, useState } from 'react'

import { fetchBotInstances, fetchLicenses } from './api'
import type { BotInstanceSummary, LicenseSummary } from './types'

function App() {
  const [licenses, setLicenses] = useState<LicenseSummary[]>([])
  const [botInstances, setBotInstances] = useState<BotInstanceSummary[]>([])

  useEffect(() => {
    void fetchLicenses().then(setLicenses)
    void fetchBotInstances().then(setBotInstances)
  }, [])

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: '960px', margin: '0 auto' }}>
      <h1>bot-licensing-server admin MVP skeleton</h1>
      <p>
        Contract-first placeholder UI for future licensing, monitoring, audit, and remote control workflows.
      </p>

      <section>
        <h2>Repository boundaries</h2>
        <ul>
          <li>Separate from any trading bot repository.</li>
          <li>No bot runtime integration in this MVP skeleton.</li>
          <li>Explicit product dimensions: product_code, bot_family, strategy_code.</li>
        </ul>
      </section>

      <section>
        <h2>Placeholder licenses</h2>
        <pre>{JSON.stringify(licenses, null, 2)}</pre>
      </section>

      <section>
        <h2>Placeholder bot instances</h2>
        <pre>{JSON.stringify(botInstances, null, 2)}</pre>
      </section>
    </main>
  )
}

export default App
