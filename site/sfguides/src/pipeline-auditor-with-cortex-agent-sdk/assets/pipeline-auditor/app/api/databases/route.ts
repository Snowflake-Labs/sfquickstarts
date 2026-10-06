import { NextResponse } from "next/server";
import { querySnowflake } from "@/lib/snowflake";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await querySnowflake("SHOW DATABASES");
    const databases = (rows as Array<{ name: string }>)
      .map((r) => r.name)
      .filter(Boolean)
      .sort();
    return NextResponse.json({ databases });
  } catch (err) {
    return NextResponse.json(
      { error: "Failed to list databases", detail: String(err) },
      { status: 500 },
    );
  }
}
