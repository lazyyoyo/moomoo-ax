"use client";

import { useEffect, useState } from "react";
import { ExperimentCard } from "@/components/cards/experiment-card";
import { Iteration } from "@/lib/supabase";

export default function OverviewPage() {
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

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Overview</h1>

      {summaries.length === 0 ? (
        <div className="text-muted-foreground">아직 실행된 루프가 없습니다.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {summaries.map((s) => (
            <ExperimentCard key={s.id} summary={s} />
          ))}
        </div>
      )}
    </div>
  );
}
