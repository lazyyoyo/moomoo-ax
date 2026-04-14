# Changelog

## v0.4.0 — 2026-04-14

### Added
- Supabase `product_runs` write path and `versions/v0.4/product-runs-migration.sql`
- dashboard `live/projects` product run observability
- Codex executor / reviewer worker contract, wrappers, templates, and model routing
- `dashboard/` first dogfooding evidence note
- plugin-bundled Codex runner / normalize path for marketplace-cache installs

### Changed
- `team-ax/ax-implement` now runs as **Claude conductor + Codex executor/reviewer**
- `scripts/ax_product_run.py` supports `--target-subdir` guard mode
- `PROJECT_BRIEF.md` roadmap now prioritizes:
  1. `ax-implement` real-project usability
  2. `ax-define` Codex-authored base documents

### Fixed
- plugin runtime path mismatch when loading from Claude plugin cache / marketplace install
- macOS bash 3.2 empty-array failure in `run_codex_worker.sh`
- `dashboard/src/app/(dashboard)/projects/page.tsx` silent failure on `product_runs` query errors

### Notes
- Track B fixture green achieved with Codex workers
- Track C first dogfooding completed on `dashboard/`
- latency remains a known issue and is not treated as a release blocker in `v0.4`

## v0.3.0 — 2026-04-13

### Added
- `team-ax/ax-implement` stage skeleton with scripts, references, templates, and agents
- isolated fixture driver `scripts/ax_product_run.py`

### Notes
- first end-to-end fixture pass proved the product-loop implement stage can run
