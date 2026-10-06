import { NextRequest, NextResponse } from "next/server";
import { querySnowflake } from "@/lib/snowflake";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const database = request.nextUrl.searchParams.get("database") || "";
  if (!database || !/^[\w-]+$/.test(database)) {
    return NextResponse.json(
      { error: "Invalid database name" },
      { status: 400 },
    );
  }

  try {
    const rows = await querySnowflake(
      `SHOW SCHEMAS IN DATABASE ${database}`,
    );
    const schemas = (rows as Array<{ name: string }>)
      .map((r) => r.name)
      .filter((s) => s !== "INFORMATION_SCHEMA")
      .sort();
    return NextResponse.json({ schemas });
  } catch (err) {
    return NextResponse.json(
      { error: "Failed to list schemas", detail: String(err) },
      { status: 500 },
    );
  }
}
