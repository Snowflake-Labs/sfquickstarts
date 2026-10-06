import { NextRequest, NextResponse } from "next/server";
import { querySnowflake } from "@/lib/snowflake";

export const dynamic = "force-dynamic";

const DANGEROUS_SQL =
  /^\s*(DROP\s+(DATABASE|SCHEMA|WAREHOUSE|ROLE|TABLE|VIEW|FUNCTION|PROCEDURE)|TRUNCATE|DELETE\s+FROM|ALTER\s+ACCOUNT|GRANT\s|REVOKE\s)/i;

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const { sql, database } = body as {
    sql?: string;
    database?: string;
  };

  if (!sql || typeof sql !== "string") {
    return NextResponse.json({ error: "sql is required" }, { status: 400 });
  }

  if (DANGEROUS_SQL.test(sql)) {
    return NextResponse.json(
      {
        error:
          "Blocked: this SQL statement is too destructive to run from the UI.",
      },
      { status: 403 },
    );
  }

  try {
    if (database) {
      if (!/^[\w-]+$/.test(database)) {
        return NextResponse.json({ error: "Invalid database name" }, { status: 400 });
      }
      await querySnowflake(`USE DATABASE ${database}`);
    }
    const rows = await querySnowflake(sql);
    return NextResponse.json({
      success: true,
      rows,
      rowCount: Array.isArray(rows) ? rows.length : 0,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { success: false, error: msg },
      { status: 500 },
    );
  }
}
