import { supabase } from "@/lib/supabase";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const project = searchParams.get("project");
  const user = searchParams.get("user");

  let query = supabase
    .from("iterations")
    .select("*")
    .eq("detail->>type", "summary")
    .order("created_at", { ascending: false });

  if (project) query = query.eq("project", project);
  if (user) query = query.eq("user", user);

  const { data, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
