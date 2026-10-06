/**
 * In-memory job store for audit/fix/chat jobs.
 * Each job accumulates events that the frontend polls via GET /api/audit/progress.
 */

export interface AuditJob {
  events: Record<string, unknown>[];
  done: boolean;
  error?: string;
}

export const jobStore = new Map<string, AuditJob>();

export function pushJobEvent(
  jobId: string,
  event: Record<string, unknown>,
): void {
  const job = jobStore.get(jobId);
  if (job) {
    if (job.events.length === 0) event._ts = Date.now();
    job.events.push(event);
  }
}

// Clean up old jobs every 5 minutes (remove jobs older than 30 min)
if (typeof globalThis !== "undefined") {
  const CLEANUP_INTERVAL_MS = 5 * 60 * 1000;
  const MAX_AGE_MS = 30 * 60 * 1000;

  // Use a global ref to avoid duplicate intervals across hot reloads
  const key = "__auditStoreCleanup";
  const g = globalThis as Record<string, unknown>;
  if (!g[key]) {
    g[key] = setInterval(() => {
      const cutoff = Date.now() - MAX_AGE_MS;
      for (const [id, job] of jobStore) {
        if (job.done && job.events.length > 0) {
          const first = job.events[0] as Record<string, unknown>;
          if (first._ts && (first._ts as number) < cutoff) {
            jobStore.delete(id);
          }
        }
      }
    }, CLEANUP_INTERVAL_MS);
  }
}
