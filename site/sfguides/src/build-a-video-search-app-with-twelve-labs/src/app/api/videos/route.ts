import { DB, SCHEMA, VIDEO_STAGE } from '@/lib/constants';
import { querySnowflake } from '@/lib/snowflake';

export const dynamic = 'force-dynamic';

export interface VideoItem {
  stage: typeof VIDEO_STAGE;
  path: string;
  title: string;
  size: number;
}

function titleOf(p: string): string {
  return p.replace(/\.[^.]+$/, '').replace(/_/g, ' ');
}

/** Lists the videos on VIDEO_STAGE that Pegasus can analyze. */
export async function GET() {
  try {
    const rows = await querySnowflake(
      `SELECT RELATIVE_PATH, SIZE FROM DIRECTORY(@${DB}.${SCHEMA}.${VIDEO_STAGE})
         WHERE RELATIVE_PATH ILIKE '%.mp4' OR RELATIVE_PATH ILIKE '%.mov'
       ORDER BY 1`,
    );
    const items: VideoItem[] = rows.map((r) => ({
      stage: VIDEO_STAGE,
      path: r.RELATIVE_PATH,
      title: titleOf(r.RELATIVE_PATH),
      size: Number(r.SIZE),
    }));
    return Response.json({ items });
  } catch (e) {
    console.error(new Date().toISOString(), '[videos] failed', e);
    return Response.json({ error: e instanceof Error ? e.message : 'Failed to list videos' }, { status: 500 });
  }
}
