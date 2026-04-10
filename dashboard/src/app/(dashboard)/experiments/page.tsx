"use client";

import { useEffect, useState } from "react";
import { ScoreChart } from "@/components/charts/score-chart";
import { TokenChart } from "@/components/charts/token-chart";
import { Iteration } from "@/lib/supabase";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function ExperimentsPage() {
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [experiments, setExperiments] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/iterations?type=iteration")
      .then((r) => r.json())
      .then((data: Iteration[]) => {
        setIterations(data);
        const exps = [...new Set(data.map((d) => d.detail.experiment || ""))].filter(Boolean);
        setExperiments(exps);
        if (exps.length > 0) setSelected(exps[exps.length - 1]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-muted-foreground">로딩 중...</div>;

  const filtered = iterations.filter((d) => d.detail.experiment === selected);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Experiments</h1>

      <div className="flex gap-2 mb-6">
        {experiments.map((exp) => (
          <button
            key={exp}
            onClick={() => setSelected(exp)}
            className={`px-3 py-1 rounded-md text-sm ${
              selected === exp
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {exp}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="text-muted-foreground">데이터 없음</div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div>
              <h2 className="text-lg font-semibold mb-3">Score</h2>
              <ScoreChart data={filtered} />
            </div>
            <div>
              <h2 className="text-lg font-semibold mb-3">Tokens</h2>
              <TokenChart data={filtered} />
            </div>
          </div>

          <h2 className="text-lg font-semibold mb-3">Iterations</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Cost</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{row.detail.iteration}</TableCell>
                  <TableCell>{row.detail.score?.toFixed(3)}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        row.detail.verdict === "keep"
                          ? "default"
                          : row.detail.verdict === "crash"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {row.detail.verdict}
                    </Badge>
                  </TableCell>
                  <TableCell>${row.detail.cost_usd?.toFixed(4)}</TableCell>
                  <TableCell>{row.detail.duration_sec}s</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(row.created_at).toLocaleString("ko-KR")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </div>
  );
}
