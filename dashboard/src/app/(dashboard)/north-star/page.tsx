import { supabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function NorthStarPage() {
  const [interventions, feedback] = await Promise.all([
    supabase.from("interventions").select("id, severity, hunks_added, hunks_deleted, created_at"),
    supabase.from("feedback_backlog").select("id, status, priority, created_at"),
  ]);

  const ivCount = interventions.data?.length ?? 0;
  const fbCount = feedback.data?.length ?? 0;
  const fbOpen = feedback.data?.filter((f) => f.status === "open").length ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">North Star</h1>
      <p className="text-sm text-muted-foreground mb-6">
        오너 개입 횟수 (↓). moomoo-ax 성공의 단일 지표.
      </p>

      {/* 두 채널 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Card
          title="자동 diff 캡처"
          subtitle="1차 지표 — 정량"
          value={ivCount.toString()}
          unit="interventions"
          note="plugin 산출물 vs 최종 커밋의 diff hunks 수. v0.2부터 실제 수집."
          status={ivCount === 0 ? "대기 중" : "수집 중"}
        />
        <Card
          title="/ax-feedback 백로그"
          subtitle="2차 채널 — 정성"
          value={`${fbOpen}`}
          unit={`open / ${fbCount} total`}
          note="오너 자유 서술. 개선 우선순위 입력. 카운트 아님."
          status={fbCount === 0 ? "대기 중" : "수집 중"}
        />
      </div>

      {/* 방법론 */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          측정 방식
        </h2>
        <div className="prose prose-sm max-w-none border rounded-md p-4 bg-muted/20">
          <p className="mb-2">
            <strong>북극성은 두 채널로 동시에 수집되지만, 역할은 완전히 다르다.</strong>
          </p>
          <ul className="text-sm space-y-1 list-disc pl-5">
            <li>
              <strong>자동 diff</strong>: "얼마나 고쳤나?" — 정량. hunks 단위.
            </li>
            <li>
              <strong>feedback 백로그</strong>: "뭘 고쳐야 하나?" — 정성. 항목 단위.
            </li>
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            기준선(어느 정도면 적절한가)은 v0.2 실전 적용 후 데이터 보고 정한다. v0.1은 측정 방식 정의만.
            전체 설계는 <code className="bg-muted px-1 rounded">docs/north-star.md</code> 참조.
          </p>
        </div>
      </section>

      {/* v0.1 상태 */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          v0.1 상태
        </h2>
        <div className="border border-dashed rounded-md p-6 text-center text-sm text-muted-foreground">
          v0.1은 스키마와 측정 방식 정의만. 실제 수집은 v0.2부터.
        </div>
      </section>
    </div>
  );
}

function Card({
  title,
  subtitle,
  value,
  unit,
  note,
  status,
}: {
  title: string;
  subtitle: string;
  value: string;
  unit: string;
  note: string;
  status: string;
}) {
  return (
    <div className="border rounded-md p-5">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="font-semibold">{title}</div>
          <div className="text-xs text-muted-foreground">{subtitle}</div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
          {status}
        </span>
      </div>
      <div className="flex items-baseline gap-2 mb-2">
        <div className="text-3xl font-bold font-mono">{value}</div>
        <div className="text-xs text-muted-foreground">{unit}</div>
      </div>
      <p className="text-xs text-muted-foreground">{note}</p>
    </div>
  );
}
