- [x] T-001 Projects 카드에 최근 product run의 stage/status/command를 보여줘서 프로젝트별 사용 맥락이 보이게 한다
> 실패 (fix-1): product_runs 쿼리가 error 를 무시해서 RLS/schema/네트워크 실패를 "기록 없음" 과 동일하게 렌더 — silent failure
- [x] T-FIX-T-001-1 Projects 페이지에서 supabase product_runs select 의 error 를 체크하고, error 케이스는 empty state 와 구분해 명시적으로 표시
