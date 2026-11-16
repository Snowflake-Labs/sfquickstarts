import { DB, PEGASUS_STAGES, SCHEMA } from '@/lib/constants';
import { sqlLiteral } from '@/lib/server';
import { querySnowflake } from '@/lib/snowflake';

export const dynamic = 'force-dynamic';

/** Presigned URL for previewing a staged video. ?stage=TRAILERS_STAGE&path=foo.mp4 */
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const stage = params.get('stage') ?? '';
  const path = params.get('path') ?? '';
  if (!(PEGASUS_STAGES as readonly string[]).includes(stage) || !path || path.length > 300) {
    return Response.json({ error: 'Invalid stage or path' }, { status: 400 });
  }
  try {
    // Confirm the file exists on the stage (bound), then presign (function requires a literal path).
    const ref = `@${DB}.${SCHEMA}.${stage}`;
    const found = await querySnowflake(`SELECT 1 AS OK FROM DIRECTORY(${ref}) WHERE RELATIVE_PATH = ?`, { binds: [path] });
    if (!found.length) return Response.json({ error: 'File not found' }, { status: 404 });
    const rows = await querySnowflake(`SELECT GET_PRESIGNED_URL(${ref}, ${sqlLiteral(path)}, 3600) AS URL`);
    return Response.json({ url: rows[0]?.URL ?? null });
  } catch (e) {
    console.error(new Date().toISOString(), '[clip-url] failed', e);
    return Response.json({ error: e instanceof Error ? e.message : 'Failed to sign URL' }, { status: 500 });
  }
}
