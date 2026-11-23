import { MODALITIES, PEGASUS_STAGES } from '@/lib/constants';
import { hasRestAuth, runAgentStream, runAgentViaSql, type AgentMessage } from '@/lib/server';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

interface AgentRequest {
  tab: 'marengo' | 'pegasus';
  message: string;
  attachment?: string | null;
  stage?: string | null;
  file?: string | null;
  modalities?: string[];
  rangeStart?: number | null;
  rangeEnd?: number | null;
  history?: AgentMessage[];
}

/** Build the routing context line the agent's orchestration instructions expect. */
function contextLine(req: AgentRequest): string {
  const parts = [`[tab=${req.tab}]`, `[attachment=${req.attachment || 'none'}]`];
  if (req.tab === 'pegasus' && req.stage && req.file) {
    parts.push(`[stage=${req.stage}]`, `[file=${req.file}]`);
    const s = Number(req.rangeStart);
    const e = Number(req.rangeEnd);
    if (req.rangeStart != null && Number.isFinite(s) && Number.isFinite(e) && e > s) {
      parts.push(`[range=${Math.max(0, Math.round(s))}-${Math.round(Math.min(e, s + 600))}]`);
    }
  }
  if (req.tab === 'marengo') {
    const allowed = new Set(MODALITIES.map((m) => m.id as string));
    const mods = (req.modalities ?? []).filter((m) => allowed.has(m));
    parts.push(`[modalities=${(mods.length ? mods : [...allowed]).join(',')}]`);
  }
  return parts.join(' ');
}

export async function POST(request: Request) {
  let body: AgentRequest;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: 'Invalid JSON body' }, { status: 400 });
  }
  if (body.tab !== 'marengo' && body.tab !== 'pegasus') {
    return Response.json({ error: 'tab must be marengo or pegasus' }, { status: 400 });
  }
  if (body.stage && !(PEGASUS_STAGES as readonly string[]).includes(body.stage)) {
    return Response.json({ error: 'Unsupported stage' }, { status: 400 });
  }
  const text = (body.message ?? '').trim() || (body.attachment ? 'Find moments similar to my attachment.' : '');
  if (!text) return Response.json({ error: 'Message is required' }, { status: 400 });

  const history = (body.history ?? []).slice(-8);
  const messages: AgentMessage[] = [
    ...history,
    { role: 'user', content: [{ type: 'text', text: `${contextLine(body)}\n${text}` }] },
  ];

  try {
    const upstream = hasRestAuth() ? await runAgentStream(messages, request.signal) : await runAgentViaSql(messages);
    if (!upstream.ok || !upstream.body) {
      const detail = await upstream.text().catch(() => '');
      console.error(new Date().toISOString(), '[agent] upstream error', upstream.status, detail.slice(0, 500));
      return Response.json(
        { error: `Agent request failed (${upstream.status})`, detail: detail.slice(0, 500) },
        { status: 502 },
      );
    }
    return new Response(upstream.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (e) {
    console.error(new Date().toISOString(), '[agent] failed', e);
    return Response.json({ error: e instanceof Error ? e.message : 'Agent request failed' }, { status: 500 });
  }
}
