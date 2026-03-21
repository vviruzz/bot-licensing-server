import type { HealthStatus } from "./types";

export async function getBackendLiveStatus(): Promise<HealthStatus> {
  return { status: "unknown" };
}
