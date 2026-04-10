import { supabase } from "@/lib/supabase";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const project = searchParams.get("project");
  const user = searchParams.get("user");
  const experiment = searchParams.get("experiment");
  const type = searchParams.get("type") || "iteration";

  let query = supabase
    .from("iterations")
    .select("*")
    .order("created_at", { ascending: true });

  if (project) query = query.eq("project", project);
  if (user) query = query.eq("user", user);
  if (type) query = query.eq("detail->>type", type);
  if (experiment) query = query.eq("detail->>experiment", experiment);

  const { data, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
