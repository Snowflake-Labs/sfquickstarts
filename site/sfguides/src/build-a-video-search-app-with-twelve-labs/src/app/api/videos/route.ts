import { DB, SCHEMA } from '@/lib/constants';
import { querySnowflake } from '@/lib/snowflake';

export const dynamic = 'force-dynamic';

export interface VideoItem {
  stage: 'TRAILERS_STAGE' | 'VOYAGERS_STAGE';
  path: string;
  title: string;
  size: number;
}

function titleOf(stage: string, p: string): string {
  const base = p.replace(/\.[^.]+$/, '');
  if (stage === 'VOYAGERS_STAGE') return base.replace(/^Voyagers! - /, '');
  return base
    .replace(/_\d+K.*$/i, '')
    .replace(/_/g, ' · ')
    .replace(/([a-z])([A-Z])/g, '$1 $2');
}

/** Lists videos Pegasus can analyze: trailers plus full Voyagers! episodes. */
export async function GET() {
  try {
    const rows = await querySnowflake(
      `SELECT 'TRAILERS_STAGE' AS STAGE, RELATIVE_PATH, SIZE FROM DIRECTORY(@${DB}.${SCHEMA}.TRAILERS_STAGE)
         WHERE RELATIVE_PATH ILIKE '%.mp4' OR RELATIVE_PATH ILIKE '%.mov'
       UNION ALL
       SELECT 'VOYAGERS_STAGE', RELATIVE_PATH, SIZE FROM DIRECTORY(@${DB}.${SCHEMA}.VOYAGERS_STAGE)
         WHERE RELATIVE_PATH ILIKE '%.mp4'
       ORDER BY 1, 2`,
    );
    const items: VideoItem[] = rows.map((r) => ({
      stage: r.STAGE,
      path: r.RELATIVE_PATH,
      title: titleOf(r.STAGE, r.RELATIVE_PATH),
      size: Number(r.SIZE),
    }));
    return Response.json({ items });
  } catch (e) {
    console.error(new Date().toISOString(), '[videos] failed', e);
    return Response.json({ error: e instanceof Error ? e.message : 'Failed to list videos' }, { status: 500 });
  }
}
