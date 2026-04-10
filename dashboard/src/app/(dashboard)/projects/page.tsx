"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Iteration } from "@/lib/supabase";

export default function ProjectsPage() {
  const [summaries, setSummaries] = useState<Iteration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/summary")
      .then((r) => r.json())
      .then((data) => {
        setSummaries(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-muted-foreground">로딩 중...</div>;

  // 프로젝트별 그룹핑
  const byProject = summaries.reduce<Record<string, Iteration[]>>((acc, s) => {
    const p = s.project;
    if (!acc[p]) acc[p] = [];
    acc[p].push(s);
    return acc;
  }, {});

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Projects</h1>

      {Object.keys(byProject).length === 0 ? (
        <div className="text-muted-foreground">데이터 없음</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(byProject).map(([project, runs]) => {
            const totalCost = runs.reduce(
              (sum, r) => sum + (r.detail.total_cost_usd || 0),
              0
            );
            const avgScore =
              runs.reduce((sum, r) => sum + (r.detail.final_score || 0), 0) /
              runs.length;

            return (
              <Card key={project}>
                <CardHeader>
                  <CardTitle>{project}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Runs</div>
                      <div className="text-xl font-bold">{runs.length}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Avg Score</div>
                      <div className="text-xl font-bold">
                        {avgScore.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Total Cost</div>
                      <div className="text-xl font-bold">
                        ${totalCost.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
