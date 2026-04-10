"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Iteration } from "@/lib/supabase";

export function TokenChart({ data }: { data: Iteration[] }) {
  const chartData = data
    .filter((d) => d.detail.type === "iteration" && d.detail.tokens)
    .map((d) => {
      const t = d.detail.tokens!;
      return {
        iteration: d.detail.iteration,
        script: (t.script?.input || 0) + (t.script?.output || 0),
        judge: (t.judge?.input || 0) + (t.judge?.output || 0),
        improve: (t.improve?.input || 0) + (t.improve?.output || 0),
      };
    });

  if (chartData.length === 0) {
    return <div className="text-muted-foreground text-sm">데이터 없음</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="iteration" />
        <YAxis label={{ value: "Tokens", angle: -90, position: "left" }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="script" fill="hsl(var(--primary))" name="Script" stackId="a" />
        <Bar dataKey="judge" fill="hsl(var(--chart-2))" name="Judge" stackId="a" />
        <Bar dataKey="improve" fill="hsl(var(--chart-3))" name="Improve" stackId="a" />
      </BarChart>
    </ResponsiveContainer>
  );
}
