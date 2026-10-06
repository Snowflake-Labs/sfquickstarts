import { NextRequest, NextResponse } from "next/server";
import { querySnowflake } from "@/lib/snowflake";

export const dynamic = "force-dynamic";

const ADMIN_ROLES = [
  "ACCOUNTADMIN",
  "SYSADMIN",
  "SECURITYADMIN",
  "SNOWFLAKE_INTELLIGENCE_ADMIN",
];

export async function GET(request: NextRequest) {
  try {
    const roleRows = await querySnowflake(
      "SELECT CURRENT_ROLE() AS role",
    );
    const row0 = roleRows[0] as Record<string, unknown>;
    const role = String(row0?.ROLE || row0?.role || "");

    let canExecute = ADMIN_ROLES.includes(role.toUpperCase());

    if (!canExecute) {
      const database = request.nextUrl.searchParams.get("database") || "";
      const schema = request.nextUrl.searchParams.get("schema") || "";
      if (database) {
        try {
          const target = schema
            ? `SCHEMA ${database}.${schema}`
            : `DATABASE ${database}`;
          const grants = (await querySnowflake(
            `SHOW GRANTS ON ${target}`,
          )) as Record<string, unknown>[];
          canExecute = grants.some((g) => {
            const priv = String(
              g.privilege || g.PRIVILEGE || "",
            ).toUpperCase();
            const grantee = String(
              g.grantee_name || g.GRANTEE_NAME || "",
            ).toUpperCase();
            return (
              grantee === role.toUpperCase() &&
              [
                "OWNERSHIP",
                "ALL",
                "ALL PRIVILEGES",
                "MODIFY",
                "CREATE TABLE",
                "OPERATE",
                "USAGE",
              ].includes(priv)
            );
          });
        } catch {
          // grant check failed — default to false
        }
      }
    }

    return NextResponse.json({ role, canExecute });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: msg, role: "", canExecute: false },
      { status: 500 },
    );
  }
}
