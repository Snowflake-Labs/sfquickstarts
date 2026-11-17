/**
 * Server-side helpers shared by the API routes: SQL literal escaping and the
 * Cortex Agent REST call.
 */
import { AGENT_NAME, DB, SCHEMA } from '@/lib/constants';
import { getRestApiAuthHeader, getServiceToken, getSnowflakeBaseUrl, querySnowflakeLongRunning } from '@/lib/snowflake';

/** Quote a value as a SQL string literal. Only for functions that reject binds (PUT, GET_PRESIGNED_URL). */
export function sqlLiteral(value: string): string {
  return `'${value.replace(/\\/g, '\\\\').replace(/'/g, "''")}'`;
}

/** Keep uploaded filenames to a safe charset so they can be inlined in PUT / TO_FILE. */
export function safeFileName(name: string): string {
  const dot = name.lastIndexOf('.');
  const base = (dot > 0 ? name.slice(0, dot) : name).replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 60) || 'upload';
  const ext = (dot > 0 ? name.slice(dot + 1) : '').replace(/[^A-Za-z0-9]/g, '').toLowerCase().slice(0, 8);
  return ext ? `${base}.${ext}` : base;
}

/**
 * Auth headers for Snowflake REST. In SAR this is the service OAuth token.
 * For local dev set SNOWFLAKE_PAT (a programmatic access token).
 */
function restAuthHeaders(): Record<string, string> {
  const pat = process.env.SNOWFLAKE_PAT;
  if (pat && !getServiceToken()) {
    return {
      Authorization: `Bearer ${pat}`,
      'X-Snowflake-Authorization-Token-Type': 'PROGRAMMATIC_ACCESS_TOKEN',
    };
  }
  return {
    Authorization: getRestApiAuthHeader(),
    'X-Snowflake-Authorization-Token-Type': 'OAUTH',
  };
}

export interface AgentMessage {
  role: 'user' | 'assistant';
  content: { type: 'text'; text: string }[];
}

/** POST to the agent's :run endpoint with streaming on; returns the raw SSE response. */
export async function runAgentStream(messages: AgentMessage[], signal?: AbortSignal): Promise<Response> {
  const base = getSnowflakeBaseUrl();
  if (!base) throw new Error('Snowflake account URL is not configured');
  const url = `${base}/api/v2/databases/${DB}/schemas/${SCHEMA}/agents/${AGENT_NAME}:run`;
  return fetch(url, {
    method: 'POST',
    headers: {
      ...restAuthHeaders(),
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ messages, stream: true }),
    signal,
  });
}

/** True when a REST bearer token is available (SAR service token or a local PAT). */
export function hasRestAuth(): boolean {
  return Boolean(getServiceToken() || process.env.SNOWFLAKE_PAT);
}

/**
 * Local-dev fallback: run the agent over SQL (non-streaming) and replay its content
 * as the same SSE events the REST stream emits, so the client code path is identical.
 */
export async function runAgentViaSql(messages: AgentMessage[]): Promise<Response> {
  const rows = await querySnowflakeLongRunning('SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?, FALSE) AS R', {
    binds: [`${DB}.${SCHEMA}.${AGENT_NAME}`, JSON.stringify({ messages })],
  });
  const raw = rows[0]?.R;
  const resp = typeof raw === 'string' ? JSON.parse(raw) : raw;
  const encoder = new TextEncoder();
  const sse = (event: string, data: unknown) => encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);

  const body = new ReadableStream({
    start(controller) {
      if (!resp || !Array.isArray(resp.content)) {
        controller.enqueue(sse('error', { message: resp?.message ?? 'Agent returned no content' }));
        controller.close();
        return;
      }
      for (const c of resp.content) {
        if (c.type === 'thinking') controller.enqueue(sse('response.thinking.delta', { text: c.thinking?.text ?? '' }));
        else if (c.type === 'tool_use') controller.enqueue(sse('response.tool_use', c.tool_use ?? {}));
        else if (c.type === 'tool_result') controller.enqueue(sse('response.tool_result', c.tool_result ?? {}));
        else if (c.type === 'text') controller.enqueue(sse('response.text.delta', { text: c.text ?? '' }));
      }
      controller.enqueue(sse('response', resp));
      controller.close();
    },
  });
  return new Response(body, { status: 200 });
}
