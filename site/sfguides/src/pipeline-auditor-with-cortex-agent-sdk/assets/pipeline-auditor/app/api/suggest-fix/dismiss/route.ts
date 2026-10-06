import { NextResponse } from "next/server";
import { setFixSession, setFixActive } from "@/app/api/suggest-fix/route";

export const dynamic = "force-dynamic";

export async function POST() {
  setFixSession(null);
  setFixActive(false);
  return NextResponse.json({ ok: true });
}
