"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Iteration } from "@/lib/supabase";

export function ScoreChart({ data }: { data: Iteration[] }) {
  const chartData = data
    .filter((d) => d.detail.type === "iteration")
    .map((d) => ({
      iteration: d.detail.iteration,
      score: d.detail.score,
      verdict: d.detail.verdict,
    }));

  if (chartData.length === 0) {
    return <div className="text-muted-foreground text-sm">데이터 없음</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="iteration" label={{ value: "Iteration", position: "bottom" }} />
        <YAxis domain={[0, 1]} label={{ value: "Score", angle: -90, position: "left" }} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="score"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
