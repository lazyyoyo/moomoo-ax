# Claude Code Plugin 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## Plugin Manifest (`.claude-plugin/plugin.json`)

### Required

- `name` (string): 고유 식별자 (kebab-case). 스킬/에이전트 네임스페이스 prefix. 예: `team-ax`

### Metadata (선택)

- `version`: semver (MAJOR.MINOR.PATCH). plugin.json 이 marketplace entry 보다 우선
- `description`, `author` (`{name, email, url}`), `homepage`, `repository`, `license`, `keywords`

### 컴포넌트 경로 필드

각 필드는 string 또는 array:

- `skills`: 기본 `skills/`
- `commands`: 기본 `commands/` (레거시)
- `agents`: 기본 `agents/`
- `hooks`: 경로 또는 inline JSON
- `mcpServers`: 경로 또는 inline JSON
- `lspServers`: 경로 또는 inline JSON
- `outputStyles`: 기본 `output-styles/`
- `userConfig` (object): 플러그인 활성화 시 입력받을 사용자 값
- `channels` (array): 메시지 채널 (Telegram/Slack/Discord)

**Path 규칙**:
- 상대경로, `./` 로 시작
- `skills`/`commands`/`agents`/`outputStyles` 는 기본값을 **replace** (extends 아님)
- 기본값 유지하려면 명시: `"skills": ["./skills/", "./extras/"]`
- `hooks`/`mcpServers`/`lspServers` 는 여러 소스 merge

### 환경변수 치환

- `${CLAUDE_PLUGIN_ROOT}`: 플러그인 설치 절대경로 (업데이트 시 변함)
- `${CLAUDE_PLUGIN_DATA}`: persistent data 디렉토리 (업데이트 후에도 유지)
- `${CLAUDE_PLUGIN_OPTION_*}`: userConfig 값

## 디렉토리 레이아웃

```
plugin-name/
├── .claude-plugin/           # manifest만
│   └── plugin.json
├── skills/                   # 디렉토리 기반 스킬
│   └── skill-name/
│       ├── SKILL.md         # 필수
│       ├── reference.md
│       └── scripts/
├── commands/                 # 레거시 플랫 파일
│   └── deploy.md
├── agents/
│   └── reviewer.md
├── hooks/
│   └── hooks.json
├── output-styles/
├── bin/                      # PATH 에 추가되는 실행파일
├── .mcp.json
├── .lsp.json
├── settings.json             # 플러그인 활성화 시 기본값 (agent 만 지원)
├── scripts/
└── README.md, LICENSE, CHANGELOG.md
```

**⚠️ 주의**: `.claude-plugin/` 에는 **`plugin.json` 만** 넣는다. skills/commands/agents/hooks/output-styles 는 플러그인 root 에 위치 (`.claude-plugin/` 밖).

## 설치 스코프

| Scope | 저장 위치 | 공유 범위 | 설정 파일 |
|-------|----------|----------|-----------|
| `user` | `~/.claude/plugins/` | 모든 프로젝트 | `~/.claude/settings.json` |
| `project` | `.claude/plugins/` (git commit) | 팀 공유 | `.claude/settings.json` |
| `local` | `.claude/plugins/` (gitignored) | 단일 프로젝트 | `.claude/settings.local.json` |
| `managed` | (관리자 제공) | 조직 전체 | managed settings |

### 캐싱

- 설치 시 `~/.claude/plugins/cache/{plugin-id}/` 로 복사 (in-place 아님)
- 경로 traversal 제한: 플러그인 root 밖 참조 불가 (symlink 는 가능)
- 업데이트 시 이전 버전은 7일 grace period 후 자동 삭제

## `--plugin-dir` CLI Flag

```bash
claude --plugin-dir ./path/to/plugin
```

- 세션 동안만 load (install 불필요)
- 여러 플러그인: `--plugin-dir ./p1 --plugin-dir ./p2`
- 같은 이름 설치된 플러그인과 충돌 시 로컬 copy 우선 (managed force-enable 제외)
- **`/reload-plugins`** 로 수정사항 reload (재시작 불필요)

## 활성/비활성 제어

### CLI

```bash
claude plugin enable <plugin>   [--scope user|project|local]
claude plugin disable <plugin>  [--scope ...]
claude plugin install <plugin>  [--scope ...]
claude plugin uninstall <plugin> [--scope ...] [--keep-data]
claude plugin update <plugin>   [--scope ...]
```

### 설정 파일

```json
{
  "enabledPlugins": {
    "my-plugin": true,
    "disabled-plugin": false
  }
}
```

### UI

`/plugin` 명령어로 매니저 인터페이스.

## 로컬 개발 표준 방법

```bash
# 플러그인 개발 디렉토리
cd my-plugin
claude --plugin-dir .

# 또는 다른 위치
claude --plugin-dir ./path/to/my-plugin
```

세션 내 reload:
```
/reload-plugins
```

테스트:
- 스킬: `/my-plugin:skill-name`
- 에이전트: `/agents`
- 훅: `/hooks`

## 마켓플레이스 배포

- **버전 bump 필수**: 캐싱으로 인해 코드 변경 시 버전 안 올리면 사용자 못 봄
- 공식: https://platform.claude.com/plugins/submit
- 커스텀: `marketplace.json` 생성 → git/HTTP 배포

## moomoo-ax 관점의 함의

- **team-ax 의 `plugin/` 경로는 `--plugin-dir plugin` 로 세션 로드 가능** → Python 하네스가 설치 없이 개발 중인 team-ax 를 subprocess 자식 세션에 주입할 수 있다. **하이브리드 Path A 의 결정적 빌딩 블록**.
- `/reload-plugins` → levelup loop 가 iteration 마다 SKILL.md 를 수정해도 자식 세션 재시작 없이 반영 가능 (재시작이 되면 검증하자).
- 현재 `plugin/.claude-plugin/plugin.json` 에 `name: team-ax` 만 있음. `version`, `skills` 경로 등 추가 필요.
- 플러그인 subagent 에는 `hooks`/`mcpServers`/`permissionMode` 지원 안 됨 → team-ax 에서 해당 기능 필요하면 skill 쪽에서 hooks 정의하거나 `.claude/agents/` 로 별도 배포.

---

**출처**:
- https://code.claude.com/docs/en/plugins.md
- https://code.claude.com/docs/en/plugins-reference.md
- https://code.claude.com/docs/en/discover-plugins.md
