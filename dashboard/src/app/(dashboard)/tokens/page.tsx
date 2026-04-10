"use client";

import { useEffect, useState } from "react";
import { TokenChart } from "@/components/charts/token-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Iteration } from "@/lib/supabase";

export default function TokensPage() {
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/iterations?type=iteration")
      .then((r) => r.json())
      .then((data) => {
        setIterations(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-muted-foreground">로딩 중...</div>;

  // 전체 토큰 집계
  let totalScript = 0;
  let totalJudge = 0;
  let totalImprove = 0;
  let totalCost = 0;

  iterations.forEach((d) => {
    const t = d.detail.tokens;
    if (t) {
      totalScript += (t.script?.input || 0) + (t.script?.output || 0);
      totalJudge += (t.judge?.input || 0) + (t.judge?.output || 0);
      totalImprove += (t.improve?.input || 0) + (t.improve?.output || 0);
    }
    totalCost += d.detail.cost_usd || 0;
  });

  const totalTokens = totalScript + totalJudge + totalImprove;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Token Usage</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTokens.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Script</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalScript.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Judge</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalJudge.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalCost.toFixed(2)}</div>
          </CardContent>
        </Card>
      </div>

      <h2 className="text-lg font-semibold mb-3">Iteration별 토큰</h2>
      <TokenChart data={iterations} />
    </div>
  );
}
