import { getBackendLiveStatus } from "./api";

export default function App() {
  const backendStatus = typeof getBackendLiveStatus === "function" ? "bootstrap" : "unknown";

  return (
    <main style={{ fontFamily: "Arial, sans-serif", margin: "2rem" }}>
      <h1>Bot Licensing Admin</h1>
      <p>Admin frontend bootstrap placeholder for the MVP.</p>
      <p>Backend status placeholder: {backendStatus}</p>
    </main>
  );
}
