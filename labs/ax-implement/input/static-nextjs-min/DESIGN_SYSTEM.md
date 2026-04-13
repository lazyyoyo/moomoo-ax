# DESIGN_SYSTEM

## 토큰 (최소)

```css
:root {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-surface: #ffffff;
  --color-text: #111827;
  --color-text-inverse: #ffffff;
  --radius-sm: 4px;
  --radius-md: 8px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
}
```

스타일은 **위 토큰만** 사용. 색상/간격/폰트 값 하드코딩 금지.

## 컴포넌트 목록

| 이름 | variant | 상태 |
|---|---|---|
| `Button` | `primary`, `secondary` | v0.3 에서 신규 (T-001) |

신규 컴포넌트는 이 표에 먼저 추가 후 구현.
