import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);

export type Iteration = {
  id: string;
  created_at: string;
  ax_version: string;
  user: string;
  project: string;
  detail: {
    type: "iteration" | "summary";
    experiment?: string;
    iteration?: number;
    score?: number;
    verdict?: string;
    failed_items?: Array<{ question: string; priority?: string }>;
    tokens?: {
      script?: { input: number; output: number };
      judge?: { input: number; output: number };
      improve?: { input: number; output: number };
    };
    cost_usd?: number;
    duration_sec?: number;
    script_version?: string;
    final_score?: number;
    total_iterations?: number;
    total_cost_usd?: number;
    status?: string;
  };
};
