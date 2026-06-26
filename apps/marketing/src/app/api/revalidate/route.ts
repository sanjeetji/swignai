// On-demand ISR revalidation endpoint (blueprint/08). The Python backend calls this
// after data changes (new picks, CMS edits) to rebuild specific ISR pages immediately.
// Token-gated with a shared secret (must match the backend's REVALIDATE_TOKEN).
import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

const TOKEN = process.env.REVALIDATE_TOKEN || "dev-revalidate-token-change-me";

export async function POST(req: NextRequest) {
  if (req.headers.get("x-revalidate-token") !== TOKEN) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await req.json().catch(() => ({}));
  const paths: string[] = Array.isArray(body?.paths) ? body.paths : [];
  for (const p of paths) {
    if (typeof p === "string" && p.startsWith("/")) revalidatePath(p);
  }
  return NextResponse.json({ revalidated: paths.length, paths });
}
