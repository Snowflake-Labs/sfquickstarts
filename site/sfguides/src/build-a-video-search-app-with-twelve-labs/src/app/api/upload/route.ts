import { UPLOAD_STAGE } from '@/lib/constants';
import { safeFileName, sqlLiteral } from '@/lib/server';
import { querySnowflake } from '@/lib/snowflake';
import { randomUUID } from 'node:crypto';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const MAX_BYTES = 250 * 1024 * 1024;
const ALLOWED = /^(image|video)\//;

/** Accepts one image or video and PUTs it to SEARCH_UPLOADS. Returns the stage-relative path. */
export async function POST(request: Request) {
  let dir: string | null = null;
  try {
    const form = await request.formData();
    const file = form.get('file');
    if (!(file instanceof File)) return Response.json({ error: 'No file provided' }, { status: 400 });
    if (!ALLOWED.test(file.type)) return Response.json({ error: 'Only image or video files are supported' }, { status: 400 });
    if (file.size > MAX_BYTES) return Response.json({ error: 'File exceeds 250 MB' }, { status: 413 });

    const name = `${Date.now()}_${safeFileName(file.name)}`;
    dir = path.join(os.tmpdir(), `tl-upload-${randomUUID()}`);
    await mkdir(dir, { recursive: true });
    const local = path.join(dir, name);
    await writeFile(local, Buffer.from(await file.arrayBuffer()));

    // PUT does not accept bind variables; the path is generated server-side from a sanitized name.
    // PUT/ALTER run synchronously: async (long-running) execution cannot fetch PUT results.
    await querySnowflake(`PUT ${sqlLiteral(`file://${local}`)} @${UPLOAD_STAGE} AUTO_COMPRESS=FALSE OVERWRITE=TRUE`);
    await querySnowflake(`ALTER STAGE ${UPLOAD_STAGE} REFRESH`);

    return Response.json({
      path: name,
      stage: 'SEARCH_UPLOADS',
      kind: file.type.startsWith('video/') ? 'video' : 'image',
      size: file.size,
    });
  } catch (e) {
    console.error(new Date().toISOString(), '[upload] failed', e);
    return Response.json({ error: e instanceof Error ? e.message : 'Upload failed' }, { status: 500 });
  } finally {
    if (dir) await rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}
